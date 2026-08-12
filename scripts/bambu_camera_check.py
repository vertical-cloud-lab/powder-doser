#!/usr/bin/env python3
"""Grab a still from a LAN-mode Bambu printer's camera, and optionally
decide whether the build plate looks clear.

Two transports, because Bambu uses two different camera protocols:

  * A1 / A1 mini / P1 series -> a proprietary "chamber image" protocol on
    TCP 6000 (TLS, user `bblp`, password = the 8-digit access code). This
    script speaks it directly with nothing but the standard library.
  * X1 / H2 series (H2D)     -> RTSPS on TCP 322,
    rtsps://bblp:<code>@<ip>:322/streaming/live/1 . There is no sane
    stdlib RTSP client, so this script shells out to ffmpeg for one
    frame. ffmpeg is found on PATH, via the FFMPEG env var / --ffmpeg,
    via `pip install imageio-ffmpeg` (bundles a static binary - the
    easiest fix on a lab laptop), or in the usual winget / chocolatey /
    scoop / Homebrew install locations.

On the H2D the camera port is gated by the **LAN Mode Liveview** toggle
(touchscreen -> Settings -> General), which is separate from Developer
Mode / LAN Only Mode. The A1 mini has no such separate toggle (field
observation, 2026-08); if a capture fails there, suspect network or
access code, not a missing setting.

Subcommands
-----------
    capture    save one frame to a file
    reference  save one frame as the "this is what an EMPTY bed looks
               like" baseline (do this with the plate clean and the
               lighting the way it will be at print time)
    check      capture a frame, compare it against the reference(s),
               and print CLEAR / NOT CLEAR / UNKNOWN

Examples
--------
    python bambu_camera_check.py capture --ip 192.168.1.42 \
        --access-code 12345678 -o frame.jpg

    # once, with the plate empty:
    python bambu_camera_check.py reference --ip ... --access-code ...
    # then, before each job:
    python bambu_camera_check.py check --ip ... --access-code ...

    # bed position varies (A1 mini is a bedslinger)? Take several
    # references into a folder and point --reference at the folder:
    python bambu_camera_check.py reference --ip ... --access-code ... \
        -o refs/bed_front.jpg
    python bambu_camera_check.py check --ip ... --access-code ... \
        --reference refs

    # H2D (RTSPS, needs ffmpeg - see above for install options):
    python bambu_camera_check.py capture --transport rtsp --ip ... \
        --access-code ... -o frame.jpg

    # let Claude look at the frame instead of pixel-diffing it
    # (pip install anthropic, ANTHROPIC_API_KEY set; no reference needed):
    python bambu_camera_check.py check --judge llm --ip ... --access-code ...

Exit codes for `check`: 0 = looks clear, 1 = does NOT look clear,
2 = unknown (no frame, no reference, Pillow missing, or the LLM judge
could not run).

IMPORTANT - what this is and is not. The default comparison is a
whole-image difference, not a model that understands 3D prints. It
aligns the frame against the reference (small translations - a nudged
camera or a bed parked at a slightly different Y no longer read as
"everything changed") and can match against multiple references, but a
part on a plate can still hide from it (transparent, low, or
plate-coloured parts read as clear - the dangerous direction) and a big
scene change still reads as "not clear". `--judge llm` sends the frame
to Claude, which understands what a 3D printer bed is and is robust to
movement and lighting, at the cost of needing an API key and a network
round trip. Treat CLEAR from either judge as *evidence*, not as a
safety interlock. Nothing here substitutes for the hardware interlock
in the docs.
"""

import argparse
import base64
import glob as globlib
import json
import os
import re
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

# How far (in pixels of the 160x160 analysis image, so ~7.5% of the
# frame) the comparison searches for the best alignment between frame
# and reference. A shifted plate or nudged camera is absorbed up to
# this; a part on the plate is a local blob no translation can remove.
MAX_SHIFT = 12

DEFAULT_REFERENCE = "bed_reference.jpg"

# Model for the --judge llm path. Vision-capable; effort is pinned low
# because this is a single-image yes/no call.
DEFAULT_LLM_MODEL = "claude-opus-5"


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
            f"could not open {ip}:{port} ({exc}). On an X1/H2D use "
            f"--transport rtsp instead - those stream on {RTSP_PORT}, "
            f"not {port}, and are gated by the LAN Mode Liveview toggle "
            "(Settings -> General). On an A1/A1 mini/P1 there is no "
            "separate liveview toggle - check the IP, the access code, "
            "and that the laptop can reach the printer at all.") from exc

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


def _find_ffmpeg(explicit=None):
    """Locate an ffmpeg binary, looking well beyond PATH.

    Order: --ffmpeg / FFMPEG env var, PATH, the imageio-ffmpeg wheel's
    bundled static binary, then the usual Windows/macOS install spots
    that a fresh terminal often does not have on PATH yet.
    """
    for candidate in (explicit, os.environ.get("FFMPEG")):
        if candidate:
            if os.path.isfile(candidate):
                return candidate
            found = shutil.which(candidate)
            if found:
                return found
    found = shutil.which("ffmpeg")
    if found:
        return found
    try:
        import imageio_ffmpeg
        return imageio_ffmpeg.get_ffmpeg_exe()
    except Exception:
        pass
    home = os.path.expanduser("~")
    for candidate in (
            # winget's shim dir (only on PATH after a new terminal)
            os.path.join(os.environ.get("LOCALAPPDATA", ""),
                         "Microsoft", "WinGet", "Links", "ffmpeg.exe"),
            r"C:\ProgramData\chocolatey\bin\ffmpeg.exe",
            os.path.join(home, "scoop", "shims", "ffmpeg.exe"),
            "/opt/homebrew/bin/ffmpeg",
            "/usr/local/bin/ffmpeg",
    ):
        if candidate and os.path.isfile(candidate):
            return candidate
    return None


_FFMPEG_INSTALL_HELP = (
    "install options:\n"
    "      pip install imageio-ffmpeg      (no admin rights; this script\n"
    "                                       finds its bundled binary)\n"
    "      winget install Gyan.FFmpeg      (Windows; reopen the terminal)\n"
    "      choco install ffmpeg            (Windows, admin)\n"
    "      brew install ffmpeg             (macOS)\n"
    "      sudo apt install ffmpeg         (Linux)\n"
    "    or point the FFMPEG env var / --ffmpeg at the binary.")


def capture_rtsp_frame(ip, access_code, timeout=30.0, port=RTSP_PORT,
                       ffmpeg=None):
    """Return one JPEG frame from the RTSPS stream using ffmpeg."""
    ffmpeg = _find_ffmpeg(ffmpeg)
    if not ffmpeg:
        raise RuntimeError(
            "ffmpeg not found (PATH, FFMPEG env var, imageio-ffmpeg, or "
            "the usual install folders). The X1/H2 camera is RTSPS and "
            "there is no stdlib client for it; " + _FFMPEG_INSTALL_HELP
            + "\n    Or capture by hand with:\n    ffmpeg -rtsp_transport"
            f" tcp -i '{rtsp_url(ip, '<CODE>', port)}' -frames:v 1 "
            "frame.jpg")
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


def capture(ip, access_code, transport="auto", timeout=15.0, port=None,
            ffmpeg=None):
    """Capture one frame with the transport appropriate to the printer."""
    if transport == "rtsp":
        return capture_rtsp_frame(ip, access_code, timeout=max(timeout, 30.0),
                                  port=port or RTSP_PORT, ffmpeg=ffmpeg)
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
        return capture_rtsp_frame(ip, access_code, timeout=max(timeout, 30.0),
                                  ffmpeg=ffmpeg)


# --------------------------------------------------------------------
# Judge 1: the pixel-diff heuristic (aligned, multi-reference).
# --------------------------------------------------------------------

def _load_pillow():
    try:
        from PIL import Image, ImageFilter  # noqa: F401
    except ImportError:
        return None
    return Image, ImageFilter


ANALYSIS_SIZE = 160


def _prepare(image, roi, size=ANALYSIS_SIZE):
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


def _shifted_fraction(now, ref, size, dx, dy, pixel_delta):
    """Changed fraction comparing now shifted by (dx, dy) against ref.

    Only the overlapping region is compared, and the comparison is
    against the MEDIAN difference so a uniform lighting change cancels
    out (normalising each frame by its own mean/std - the obvious first
    attempt - fails badly: one bright object drags the whole frame's
    statistics and every pixel then reads as changed).
    """
    xs = range(max(0, -dx), size - max(0, dx))
    ys = range(max(0, -dy), size - max(0, dy))
    diffs = []
    for y in ys:
        row_now = (y + dy) * size + dx
        row_ref = y * size
        diffs.extend(now[row_now + x] - ref[row_ref + x] for x in xs)
    offset = _median(diffs)
    changed = sum(1 for d in diffs if abs(d - offset) > pixel_delta)
    return changed / len(diffs)


def compare_frames(frame_bytes, reference_bytes, roi=None,
                   pixel_delta=PIXEL_DELTA, area_fraction=AREA_FRACTION,
                   max_shift=MAX_SHIFT):
    """Return (is_clear, changed_fraction, detail).

    is_clear is None when no verdict is possible (Pillow missing).

    The frame is aligned against the reference before scoring: the
    comparison searches translations up to max_shift pixels (in the
    160x160 analysis image) and keeps the best-matching one, so a
    nudged camera or a bed parked at a slightly different position no
    longer reads as "everything changed". A part on the plate is a
    local blob no translation can remove, so it still scores high.
    max_shift=0 restores the old rigid comparison.
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

    size = ANALYSIS_SIZE
    max_shift = max(0, min(int(max_shift), size // 4))

    best = (_shifted_fraction(now, ref, size, 0, 0, pixel_delta), 0, 0)
    # Only search for an alignment when the rigid comparison says
    # "everything changed" - the signature of a moved bed/camera, not of
    # a part. Without this gate, a part touching the frame edge on an
    # otherwise featureless bed could be shifted partly out of the
    # comparison window and read as clear.
    if max_shift and best[0] > max(4 * area_fraction, 0.04):
        # Coarse-to-fine translation search: coarse grid first, then a
        # 1-px sweep around the coarse winner. ~100 evaluations total.
        for dx in range(-max_shift, max_shift + 1, 4):
            for dy in range(-max_shift, max_shift + 1, 4):
                if (dx, dy) == (0, 0):
                    continue
                frac = _shifted_fraction(now, ref, size, dx, dy, pixel_delta)
                if frac < best[0]:
                    best = (frac, dx, dy)
        cx, cy = best[1], best[2]
        for dx in range(max(-max_shift, cx - 3), min(max_shift, cx + 3) + 1):
            for dy in range(max(-max_shift, cy - 3),
                            min(max_shift, cy + 3) + 1):
                if (dx, dy) == (cx, cy):
                    continue
                frac = _shifted_fraction(now, ref, size, dx, dy, pixel_delta)
                if frac < best[0]:
                    best = (frac, dx, dy)

    fraction, dx, dy = best
    is_clear = fraction <= area_fraction
    shifted = f", aligned at shift ({dx},{dy})" if (dx, dy) != (0, 0) else ""
    detail = (f"{fraction * 100:.2f}% of the frame differs from the "
              f"reference (limit {area_fraction * 100:.2f}%{shifted})")
    return is_clear, fraction, detail


def resolve_reference_paths(reference_path):
    """A reference can be one image or a folder of them."""
    if not reference_path:
        return []
    if os.path.isdir(reference_path):
        paths = []
        for pattern in ("*.jpg", "*.jpeg", "*.png"):
            paths.extend(globlib.glob(os.path.join(reference_path, pattern)))
        return sorted(paths)
    if os.path.isfile(reference_path):
        return [reference_path]
    return []


def compare_against_references(frame_bytes, reference_path, roi=None,
                               pixel_delta=PIXEL_DELTA,
                               area_fraction=AREA_FRACTION,
                               max_shift=MAX_SHIFT):
    """Compare a frame against one reference image or a folder of them.

    Returns (is_clear, best_fraction, detail). The frame counts as
    clear when it matches ANY reference - take references with the bed
    parked at each position it ends up in, and a moved plate stops
    reading as "not clear".
    """
    paths = resolve_reference_paths(reference_path)
    if not paths:
        return None, 0.0, (
            f"no reference image at {reference_path!r} - run "
            "`bambu_camera_check.py reference` once with the bed empty "
            "(or pass a folder of empty-bed shots)")
    best = None
    for path in paths:
        try:
            with open(path, "rb") as fh:
                reference = fh.read()
        except OSError as exc:
            return None, 0.0, f"could not read the reference image: {exc}"
        verdict, fraction, detail = compare_frames(
            frame_bytes, reference, roi=roi, pixel_delta=pixel_delta,
            area_fraction=area_fraction, max_shift=max_shift)
        if verdict is None:
            return None, fraction, detail
        if best is None or fraction < best[1]:
            best = (verdict, fraction,
                    detail + (f" [best of {len(paths)} references: "
                              f"{os.path.basename(path)}]"
                              if len(paths) > 1 else ""))
        if best[0]:
            break
    return best


# --------------------------------------------------------------------
# Judge 2: ask Claude to look at the frame (--judge llm).
#
# No reference image, robust to a moved plate/camera and lighting, and
# it understands what a printer bed is - at the cost of an API key
# (ANTHROPIC_API_KEY), `pip install anthropic`, and a network round
# trip. Fails to UNKNOWN (never CLEAR) on any error.
# --------------------------------------------------------------------

_LLM_SCHEMA = {
    "type": "object",
    "properties": {
        "plate_visible": {"type": "boolean"},
        "bed_clear": {"type": "boolean"},
        "observation": {"type": "string"},
    },
    "required": ["plate_visible", "bed_clear", "observation"],
    "additionalProperties": False,
}

_LLM_PROMPT = (
    "This is a frame from the built-in camera of a Bambu Lab 3D printer, "
    "looking at the build plate. Decide whether the BUILD PLATE is clear "
    "enough to start a new print.\n\n"
    "Clear means: no finished or failed print stuck to the plate, no "
    "detached filament / spaghetti, no tools, scrapers, or other objects "
    "resting on it. A normal empty textured/smooth build surface (often "
    "gold, black, or grey, possibly with a printed grid or logo) is "
    "clear. Ignore the toolhead/gantry, PTFE tubes, purge chute and "
    "wiper, filament on spools, and anything outside the plate area. "
    "Purge lines or small filament scraps at the very edge of the plate "
    "do not block a print - still mention them in the observation.\n\n"
    "If the plate is not visible or the image is too dark/blurred to "
    "tell, set plate_visible to false.\n\n"
    "Respond with a JSON object only: {\"plate_visible\": bool, "
    "\"bed_clear\": bool, \"observation\": \"one sentence\"}")


def _parse_llm_verdict(text):
    """Return (verdict True/False/None, observation-or-error string)."""
    data = None
    try:
        data = json.loads(text)
    except (ValueError, TypeError):
        match = re.search(r"\{.*\}", text or "", re.S)
        if match:
            try:
                data = json.loads(match.group(0))
            except ValueError:
                data = None
    if not isinstance(data, dict) or "bed_clear" not in data:
        return None, f"could not parse the model's answer: {text!r}"
    observation = str(data.get("observation", "")).strip()
    if not data.get("plate_visible", True):
        return None, ("the model could not see the plate"
                      + (f" - {observation}" if observation else ""))
    return bool(data["bed_clear"]), observation


def llm_bed_check(frame_bytes, model=DEFAULT_LLM_MODEL, timeout=90.0):
    """Ask Claude whether the plate in this JPEG is clear.

    Returns (verdict, message); verdict is True/False/None. Never
    raises - a missing SDK, missing key, refusal, or API error all
    degrade to None so the caller falls back to asking a human.
    """
    try:
        import anthropic
    except ImportError:
        return None, ("the LLM judge needs the Anthropic SDK: "
                      "pip install anthropic  (and set ANTHROPIC_API_KEY)")
    request = dict(
        model=model,
        max_tokens=2048,
        messages=[{
            "role": "user",
            "content": [
                {"type": "image",
                 "source": {"type": "base64", "media_type": "image/jpeg",
                            "data": base64.standard_b64encode(
                                frame_bytes).decode("ascii")}},
                {"type": "text", "text": _LLM_PROMPT},
            ],
        }],
    )
    try:
        client = anthropic.Anthropic(timeout=timeout)
        try:
            response = client.messages.create(
                output_config={
                    "effort": "low",
                    "format": {"type": "json_schema", "schema": _LLM_SCHEMA},
                },
                **request)
        except TypeError:
            # Older SDK without output_config: the prompt still asks for
            # bare JSON, and _parse_llm_verdict digs it out of prose.
            response = client.messages.create(**request)
    except Exception as exc:
        return None, f"LLM judge unavailable: {exc}"
    if getattr(response, "stop_reason", None) == "refusal":
        return None, "LLM judge unavailable: the model declined the request"
    text = next((b.text for b in response.content
                 if getattr(b, "type", "") == "text"), "")
    verdict, message = _parse_llm_verdict(text)
    if verdict is None:
        return None, f"LLM judge inconclusive: {message}"
    return verdict, f"Claude ({response.model}): {message}"


# --------------------------------------------------------------------
# The combined check.
# --------------------------------------------------------------------

def check_bed_clear(ip, access_code, reference_path=DEFAULT_REFERENCE,
                    transport="auto", timeout=15.0, roi=None,
                    save_to=None, pixel_delta=PIXEL_DELTA,
                    area_fraction=AREA_FRACTION, port=None,
                    max_shift=MAX_SHIFT, judge="diff",
                    llm_model=DEFAULT_LLM_MODEL, ffmpeg=None):
    """Capture and judge. Returns (verdict, message).

    verdict is True (clear), False (not clear), or None (unknown).
    judge is "diff" (pixel comparison against the reference(s)),
    "llm" (ask Claude - no reference needed), or "both" (NOT CLEAR if
    either says so; CLEAR only when both agree the plate is clear).
    Never raises: a camera fault must not be able to crash a print run,
    it must degrade to "unknown" so the caller can fall back to asking a
    human.
    """
    try:
        frame = capture(ip, access_code, transport=transport,
                        timeout=timeout, port=port, ffmpeg=ffmpeg)
    except (RuntimeError, OSError, ValueError) as exc:
        return None, f"camera unavailable: {exc}"
    if save_to:
        try:
            with open(save_to, "wb") as fh:
                fh.write(frame)
        except OSError as exc:
            print(f"NOTE: could not save the frame to {save_to}: {exc}",
                  file=sys.stderr)

    verdicts = []
    if judge in ("diff", "both"):
        verdict, _fraction, detail = compare_against_references(
            frame, reference_path, roi=roi, pixel_delta=pixel_delta,
            area_fraction=area_fraction, max_shift=max_shift)
        verdicts.append((verdict, detail))
    if judge in ("llm", "both"):
        verdict, detail = llm_bed_check(frame, model=llm_model)
        verdicts.append((verdict, detail))

    combined = " | ".join(d for _, d in verdicts)
    if any(v is False for v, _ in verdicts):
        return False, (f"bed does NOT look clear - {combined}. If the plate "
                       "is genuinely empty, the reference is stale (moved "
                       "camera, lighting, or a parked toolhead in frame): "
                       "retake it, add references at other bed positions "
                       "(--reference <folder>), or try --judge llm.")
    if verdicts and all(v is True for v, _ in verdicts):
        return True, f"bed looks CLEAR - {combined}"
    return None, combined or "no judge ran"


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
    parser.add_argument("--ffmpeg", default=None,
                        help="path to the ffmpeg binary for --transport "
                             "rtsp (default: PATH, FFMPEG env var, "
                             "imageio-ffmpeg, or common install folders)")
    parser.add_argument("-o", "--output", default=None,
                        help="where to write the JPEG (default: frame.jpg "
                             "for capture/check, the reference path for "
                             "reference)")
    parser.add_argument("--reference", default=DEFAULT_REFERENCE,
                        help="empty-bed baseline: one image, or a folder "
                             "of images taken at different bed positions "
                             f"(default {DEFAULT_REFERENCE})")
    parser.add_argument("--judge", default="diff",
                        choices=("diff", "llm", "both"),
                        help="diff = pixel comparison against the "
                             "reference(s); llm = send the frame to Claude "
                             "(pip install anthropic + ANTHROPIC_API_KEY, "
                             "no reference needed); both = strictest")
    parser.add_argument("--llm-model", default=DEFAULT_LLM_MODEL,
                        help=f"model for --judge llm (default "
                             f"{DEFAULT_LLM_MODEL})")
    parser.add_argument("--roi", default=None,
                        help="restrict the comparison to a fraction of the "
                             "frame: x0,y0,x1,y1 in 0-1, e.g. 0.2,0.3,0.8,0.9")
    parser.add_argument("--pixel-delta", type=float, default=PIXEL_DELTA,
                        help="per-pixel difference that counts as changed "
                             f"(0-255, default {PIXEL_DELTA})")
    parser.add_argument("--area-fraction", type=float, default=AREA_FRACTION,
                        help="fraction of changed pixels that means NOT "
                             f"clear (default {AREA_FRACTION})")
    parser.add_argument("--max-shift", type=int, default=MAX_SHIFT,
                        help="how far (px of the 160x160 analysis image) to "
                             "search for the best frame/reference alignment "
                             f"(default {MAX_SHIFT}; 0 = rigid comparison)")
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
        if os.path.isdir(out):
            parser.error(f"{out!r} is a folder - pass an image filename "
                         "with -o (e.g. -o refs/bed_front.jpg)")
        try:
            frame = capture(ip, code, transport=args.transport,
                            timeout=args.timeout, ffmpeg=args.ffmpeg)
        except (RuntimeError, OSError, ValueError) as exc:
            print(f"ERROR: {exc}")
            return 2
        parent = os.path.dirname(out)
        if parent:
            os.makedirs(parent, exist_ok=True)
        with open(out, "wb") as fh:
            fh.write(frame)
        print(f"Saved {len(frame)} bytes to {out}")
        if args.mode == "reference":
            print("That frame is now the empty-bed baseline. Retake it "
                  "whenever the camera moves or the lighting changes, and "
                  "consider a folder of references (one per bed position) "
                  "if the plate parks in different spots.")
        return 0

    verdict, message = check_bed_clear(
        ip, code, reference_path=args.reference, transport=args.transport,
        timeout=args.timeout, roi=roi, save_to=args.output or "frame.jpg",
        pixel_delta=args.pixel_delta, area_fraction=args.area_fraction,
        max_shift=args.max_shift, judge=args.judge,
        llm_model=args.llm_model, ffmpeg=args.ffmpeg)
    label = {True: "CLEAR", False: "NOT CLEAR", None: "UNKNOWN"}[verdict]
    print(f"{label}: {message}")
    return {True: 0, False: 1, None: 2}[verdict]


if __name__ == "__main__":
    sys.exit(main())
