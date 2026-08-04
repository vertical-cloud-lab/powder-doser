#!/usr/bin/env python3
"""Grab a still from a LAN-mode Bambu printer's camera, and optionally
decide whether the build plate looks clear.

Two transports, because Bambu uses two different camera protocols:

  * A1 / A1 mini / P1 series -> a proprietary "chamber image" protocol on
    TCP 6000 (TLS, user `bblp`, password = the 8-digit access code). This
    script speaks it directly with nothing but the standard library.
  * X1 / H2 series (H2D)     -> RTSPS on TCP 322,
    rtsps://bblp:<code>@<ip>:322/streaming/live/1 . There is no sane
    stdlib RTSP client, so this script shells out to ffmpeg for one frame.

Either way the printer must have **LAN Mode Liveview** enabled
(touchscreen -> Settings -> General). That toggle is separate from
Developer Mode / LAN Only Mode: with it off, the port is closed and every
capture below times out even though MQTT and FTPS work fine.

Subcommands
-----------
    capture    save one frame to a file
    reference  save one frame as the "this is what an EMPTY bed looks
               like" baseline (do this with the plate clean and the
               lighting the way it will be at print time)
    check      capture a frame, compare it against the reference, and
               print CLEAR / NOT CLEAR / UNKNOWN

Examples
--------
    python bambu_camera_check.py capture --ip 192.168.1.42 \
        --access-code 12345678 -o frame.jpg

    # once, with the plate empty:
    python bambu_camera_check.py reference --ip ... --access-code ...
    # then, before each job:
    python bambu_camera_check.py check --ip ... --access-code ...

    # H2D (RTSPS, needs ffmpeg on PATH):
    python bambu_camera_check.py capture --transport rtsp --ip ... \
        --access-code ... -o frame.jpg

Exit codes for `check`: 0 = looks clear, 1 = does NOT look clear,
2 = unknown (no frame, no reference, or Pillow missing).

IMPORTANT - what this is and is not. The comparison is a dumb
whole-image difference, not a model that understands 3D prints. It
reliably catches "the last part is still sitting on the plate" and
"a tool is lying across the bed", and it reliably false-positives on
changed lighting, a moved camera, or a toolhead parked in view. Treat
CLEAR as *evidence*, not as a safety interlock: a transparent or
low-contrast part on a same-coloured plate can read as clear. Nothing
here substitutes for the hardware interlock in the docs.
"""

import argparse
import os
import shutil
import socket
import ssl
import struct
import subprocess
import sys
import time

CAMERA_PORT = 6000          # A1 / A1 mini / P1 chamber-image protocol
RTSP_PORT = 322             # X1 / H2 series
USERNAME = "bblp"

JPEG_SOI = b"\xff\xd8"
JPEG_EOI = b"\xff\xd9"

# Defaults for the bed-clear heuristic. A pixel counts as "changed" when
# it differs from the reference by more than PIXEL_DELTA (0-255); the
# frame counts as "not clear" when more than AREA_FRACTION of pixels
# changed. Tuned to be forgiving of JPEG noise, not of an actual part.
PIXEL_DELTA = 28
AREA_FRACTION = 0.02

DEFAULT_REFERENCE = "bed_reference.jpg"


def _is_placeholder(value):
    return not value or (isinstance(value, str) and value.startswith("PUT_"))


# --------------------------------------------------------------------
# Transport A: the A1/P1 chamber-image protocol on TCP 6000.
# --------------------------------------------------------------------

def _auth_packet(access_code, username=USERNAME):
    """The 80-byte hello the printer expects before it sends frames.

    Layout (little-endian): 0x40, 0x3000, 0, 0, then the username and the
    access code each in a 32-byte NUL-padded field.
    """
    packet = bytearray()
    packet += struct.pack("<IIII", 0x40, 0x3000, 0, 0)
    for field in (username, str(access_code)):
        raw = field.encode("ascii")
        if len(raw) > 32:
            raise ValueError(f"field too long for the 32-byte slot: {field!r}")
        packet += raw + b"\x00" * (32 - len(raw))
    return bytes(packet)


def capture_chamber_image(ip, access_code, timeout=15.0, port=CAMERA_PORT):
    """Return one JPEG frame (bytes) from the port-6000 camera.

    Raises RuntimeError with an actionable message on failure.
    """
    ctx = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE

    deadline = time.monotonic() + timeout
    try:
        raw = socket.create_connection((ip, port), timeout=timeout)
    except OSError as exc:
        raise RuntimeError(
            f"could not open {ip}:{port} ({exc}). The usual cause is "
            "LAN Mode Liveview being off on the printer (Settings -> "
            "General); it is a separate toggle from Developer Mode. On "
            "an X1/H2D use --transport rtsp instead - those stream on "
            f"{RTSP_PORT}, not {port}.") from exc

    with raw:
        sock = ctx.wrap_socket(raw, server_hostname=str(ip))
        with sock:
            sock.sendall(_auth_packet(access_code))
            sock.settimeout(max(1.0, timeout))
            buf = bytearray()
            payload_size = None
            while True:
                if time.monotonic() > deadline:
                    raise RuntimeError(
                        f"no complete frame within {timeout:.0f}s. The "
                        "camera streams roughly one frame per second, so "
                        "try a longer --timeout before assuming a fault.")
                try:
                    chunk = sock.recv(8192)
                except socket.timeout as exc:
                    raise RuntimeError(
                        f"timed out reading from {ip}:{port}. Connection "
                        "was accepted but no image data arrived.") from exc
                if not chunk:
                    # The printer closes the socket immediately when the
                    # access code is wrong - that is the whole error report.
                    raise RuntimeError(
                        "printer closed the camera connection without "
                        "sending a frame. That is what a wrong access "
                        "code looks like; double-check the 8-digit code "
                        "from Settings -> WLAN.")
                buf += chunk

                # 16-byte header, first 3 bytes = payload length, then the
                # JPEG itself.
                if payload_size is None:
                    if len(buf) < 16:
                        continue
                    payload_size = int.from_bytes(buf[0:3], byteorder="little")
                    del buf[:16]
                    if not 0 < payload_size <= 32 << 20:
                        raise RuntimeError(
                            f"implausible frame length {payload_size} - the "
                            "stream is not the expected chamber-image "
                            "protocol.")
                if len(buf) >= payload_size:
                    frame = bytes(buf[:payload_size])
                    if not (frame.startswith(JPEG_SOI)
                            and frame.endswith(JPEG_EOI)):
                        # Desynchronised; drop it and resync on the next
                        # header rather than saving a corrupt file.
                        del buf[:payload_size]
                        payload_size = None
                        continue
                    return frame


# --------------------------------------------------------------------
# Transport B: RTSPS on TCP 322 (X1 / H2 series), via ffmpeg.
# --------------------------------------------------------------------

def rtsp_url(ip, access_code, port=RTSP_PORT):
    return f"rtsps://{USERNAME}:{access_code}@{ip}:{port}/streaming/live/1"


def capture_rtsp_frame(ip, access_code, timeout=30.0, port=RTSP_PORT):
    """Return one JPEG frame from the RTSPS stream using ffmpeg."""
    ffmpeg = shutil.which("ffmpeg")
    if not ffmpeg:
        raise RuntimeError(
            "ffmpeg not found on PATH. The X1/H2 camera is RTSPS and there "
            "is no stdlib client for it; install ffmpeg, or capture by "
            "hand with:\n    ffmpeg -rtsp_transport tcp -i "
            f"'{rtsp_url(ip, '<CODE>', port)}' -frames:v 1 frame.jpg")
    cmd = [ffmpeg, "-loglevel", "error", "-rtsp_transport", "tcp",
           "-i", rtsp_url(ip, access_code, port),
           "-frames:v", "1", "-f", "image2", "-vcodec", "mjpeg", "pipe:1"]
    try:
        proc = subprocess.run(cmd, capture_output=True, timeout=timeout)
    except subprocess.TimeoutExpired as exc:
        raise RuntimeError(
            f"ffmpeg did not return a frame within {timeout:.0f}s. Check "
            "that LAN Mode Liveview is on and that TCP "
            f"{port} is reachable.") from exc
    if proc.returncode != 0 or not proc.stdout:
        # Never echo the URL back - it contains the access code.
        detail = proc.stderr.decode("utf-8", "replace").strip()
        detail = detail.replace(str(access_code), "<CODE>")
        raise RuntimeError(f"ffmpeg failed (exit {proc.returncode}): {detail}")
    return proc.stdout


def capture(ip, access_code, transport="auto", timeout=15.0, port=None):
    """Capture one frame with the transport appropriate to the printer."""
    if transport == "rtsp":
        return capture_rtsp_frame(ip, access_code, timeout=max(timeout, 30.0),
                                  port=port or RTSP_PORT)
    if transport == "chamber":
        return capture_chamber_image(ip, access_code, timeout=timeout,
                                     port=port or CAMERA_PORT)
    # auto: try the A1/P1 protocol, fall back to RTSPS.
    try:
        return capture_chamber_image(ip, access_code, timeout=timeout,
                                     port=port or CAMERA_PORT)
    except RuntimeError as exc:
        print(f"NOTE: chamber-image capture failed ({exc}); trying RTSPS "
              f"on {RTSP_PORT} ...", file=sys.stderr)
        return capture_rtsp_frame(ip, access_code, timeout=max(timeout, 30.0))


# --------------------------------------------------------------------
# The bed-clear heuristic.
# --------------------------------------------------------------------

def _load_pillow():
    try:
        from PIL import Image, ImageFilter  # noqa: F401
    except ImportError:
        return None
    return Image, ImageFilter


def _prepare(image, roi, size=160):
    """Grayscale, crop to the ROI, downscale, blur. Returns pixels 0-255."""
    Image, ImageFilter = _load_pillow()
    img = image.convert("L")
    if roi:
        w, h = img.size
        x0, y0, x1, y1 = roi
        img = img.crop((int(x0 * w), int(y0 * h), int(x1 * w), int(y1 * h)))
    img = img.resize((size, size), Image.BILINEAR)
    # Blur first: it costs nothing and stops JPEG ringing and a
    # one-pixel camera shift from registering as change.
    img = img.filter(ImageFilter.GaussianBlur(radius=1.2))
    return list(img.getdata())


def _median(values):
    ordered = sorted(values)
    mid = len(ordered) // 2
    if len(ordered) % 2:
        return float(ordered[mid])
    return (ordered[mid - 1] + ordered[mid]) / 2.0


def parse_roi(text):
    if not text:
        return None
    parts = [float(p) for p in str(text).replace(" ", "").split(",")]
    if len(parts) != 4:
        raise ValueError("--roi wants four comma-separated fractions: "
                         "x0,y0,x1,y1 (0-1)")
    x0, y0, x1, y1 = parts
    if not (0 <= x0 < x1 <= 1 and 0 <= y0 < y1 <= 1):
        raise ValueError("--roi values must satisfy 0 <= x0 < x1 <= 1 and "
                         "0 <= y0 < y1 <= 1")
    return (x0, y0, x1, y1)


def compare_frames(frame_bytes, reference_bytes, roi=None,
                   pixel_delta=PIXEL_DELTA, area_fraction=AREA_FRACTION):
    """Return (is_clear, changed_fraction, detail).

    is_clear is None when no verdict is possible (Pillow missing).
    """
    pillow = _load_pillow()
    if pillow is None:
        return None, 0.0, ("Pillow is not installed, so the frame was saved "
                           "but not analysed. pip install pillow")
    Image, _ = pillow
    from io import BytesIO
    try:
        now = _prepare(Image.open(BytesIO(frame_bytes)), roi)
        ref = _prepare(Image.open(BytesIO(reference_bytes)), roi)
    except OSError as exc:
        return None, 0.0, f"could not decode an image: {exc}"

    # Compare against the MEDIAN difference rather than the raw one. A
    # change in room lighting shifts every pixel by roughly the same
    # amount, and the median absorbs that; a part sitting on the plate
    # only moves a minority of pixels, so it survives as a residual.
    # (Normalising each frame by its own mean/std instead - the obvious
    # first attempt - fails badly: one bright object drags the whole
    # frame's statistics and every pixel then reads as changed.)
    diffs = [a - b for a, b in zip(now, ref)]
    offset = _median(diffs)
    changed = sum(1 for d in diffs if abs(d - offset) > pixel_delta)
    fraction = changed / len(now)
    is_clear = fraction <= area_fraction
    detail = (f"{fraction * 100:.2f}% of the frame differs from the "
              f"reference (limit {area_fraction * 100:.2f}%)")
    return is_clear, fraction, detail


def check_bed_clear(ip, access_code, reference_path=DEFAULT_REFERENCE,
                    transport="auto", timeout=15.0, roi=None,
                    save_to=None, pixel_delta=PIXEL_DELTA,
                    area_fraction=AREA_FRACTION, port=None):
    """Capture and compare. Returns (verdict, message).

    verdict is True (clear), False (not clear), or None (unknown).
    Never raises: a camera fault must not be able to crash a print run,
    it must degrade to "unknown" so the caller can fall back to asking a
    human.
    """
    try:
        frame = capture(ip, access_code, transport=transport,
                        timeout=timeout, port=port)
    except (RuntimeError, OSError, ValueError) as exc:
        return None, f"camera unavailable: {exc}"
    if save_to:
        try:
            with open(save_to, "wb") as fh:
                fh.write(frame)
        except OSError as exc:
            print(f"NOTE: could not save the frame to {save_to}: {exc}",
                  file=sys.stderr)
    if not reference_path or not os.path.isfile(reference_path):
        return None, (f"no reference image at {reference_path!r} - run "
                      "`bambu_camera_check.py reference` once with the bed "
                      "empty to create one")
    try:
        with open(reference_path, "rb") as fh:
            reference = fh.read()
    except OSError as exc:
        return None, f"could not read the reference image: {exc}"
    verdict, _fraction, detail = compare_frames(
        frame, reference, roi=roi, pixel_delta=pixel_delta,
        area_fraction=area_fraction)
    if verdict is None:
        return None, detail
    if verdict:
        return True, f"bed looks CLEAR - {detail}"
    return False, (f"bed does NOT look clear - {detail}. If the plate is "
                   "genuinely empty, the reference is stale (lighting, "
                   "camera angle, or a parked toolhead in frame): retake "
                   "it, or widen the check with --roi/--area-fraction.")


# --------------------------------------------------------------------
# CLI
# --------------------------------------------------------------------

def _creds(args, parser):
    ip = args.ip or os.environ.get("A1_MINI_IP") or os.environ.get(
        "H2D_IP") or os.environ.get("BAMBU_IP")
    code = args.access_code or os.environ.get(
        "A1_MINI_ACCESS_CODE") or os.environ.get(
        "H2D_ACCESS_CODE") or os.environ.get("BAMBU_ACCESS_CODE")
    missing = [n for n, v in [("--ip", ip), ("--access-code", code)] if
               _is_placeholder(v)]
    if missing:
        parser.error("missing " + " and ".join(missing) + " (or the "
                     "A1_MINI_IP / A1_MINI_ACCESS_CODE environment "
                     "variables)")
    return ip, code


def build_parser():
    parser = argparse.ArgumentParser(
        description="Capture a frame from a Bambu printer's camera and "
                    "optionally judge whether the bed is clear.")
    parser.add_argument("mode", choices=("capture", "reference", "check"))
    parser.add_argument("--ip", default=None)
    parser.add_argument("--access-code", default=None)
    parser.add_argument("--transport", default="auto",
                        choices=("auto", "chamber", "rtsp"),
                        help="chamber = A1/A1 mini/P1 on TCP 6000; "
                             "rtsp = X1/H2D on TCP 322 via ffmpeg")
    parser.add_argument("-o", "--output", default=None,
                        help="where to write the JPEG (default: frame.jpg "
                             "for capture/check, the reference path for "
                             "reference)")
    parser.add_argument("--reference", default=DEFAULT_REFERENCE,
                        help=f"empty-bed baseline (default {DEFAULT_REFERENCE})")
    parser.add_argument("--roi", default=None,
                        help="restrict the comparison to a fraction of the "
                             "frame: x0,y0,x1,y1 in 0-1, e.g. 0.2,0.3,0.8,0.9")
    parser.add_argument("--pixel-delta", type=float, default=PIXEL_DELTA,
                        help="per-pixel difference that counts as changed "
                             f"(0-255, default {PIXEL_DELTA})")
    parser.add_argument("--area-fraction", type=float, default=AREA_FRACTION,
                        help="fraction of changed pixels that means NOT "
                             f"clear (default {AREA_FRACTION})")
    parser.add_argument("--timeout", type=float, default=15.0)
    return parser


def main():
    parser = build_parser()
    args = parser.parse_args()
    ip, code = _creds(args, parser)
    try:
        roi = parse_roi(args.roi)
    except ValueError as exc:
        parser.error(str(exc))

    if args.mode in ("capture", "reference"):
        out = args.output or (args.reference if args.mode == "reference"
                              else "frame.jpg")
        try:
            frame = capture(ip, code, transport=args.transport,
                            timeout=args.timeout)
        except (RuntimeError, OSError, ValueError) as exc:
            print(f"ERROR: {exc}")
            return 2
        with open(out, "wb") as fh:
            fh.write(frame)
        print(f"Saved {len(frame)} bytes to {out}")
        if args.mode == "reference":
            print("That frame is now the empty-bed baseline. Retake it "
                  "whenever the camera moves or the lighting changes.")
        return 0

    verdict, message = check_bed_clear(
        ip, code, reference_path=args.reference, transport=args.transport,
        timeout=args.timeout, roi=roi, save_to=args.output or "frame.jpg",
        pixel_delta=args.pixel_delta, area_fraction=args.area_fraction)
    label = {True: "CLEAR", False: "NOT CLEAR", None: "UNKNOWN"}[verdict]
    print(f"{label}: {message}")
    return {True: 0, False: 1, None: 2}[verdict]


if __name__ == "__main__":
    sys.exit(main())
