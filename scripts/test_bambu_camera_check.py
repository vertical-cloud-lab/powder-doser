#!/usr/bin/env python3
"""Self-test for bambu_camera_check.py - no printer required.

Stands up a fake camera server that speaks the A1/P1 chamber-image
protocol (TLS on a random port, 16-byte header + JPEG payload) and drives
the real client against it, then exercises the bed-clear heuristic with
synthetic images.

    python test_bambu_camera_check.py

Needs `openssl` on PATH for the TLS half (skipped with a note if absent)
and Pillow for the image half.
"""

import os
import shutil
import socket
import ssl
import struct
import subprocess
import sys
import tempfile
import threading

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import bambu_camera_check as cam  # noqa: E402

PASSES = []
FAILURES = []


def check(name, condition, detail=""):
    (PASSES if condition else FAILURES).append(name)
    print(f"{'PASS' if condition else 'FAIL'}: {name}"
          + (f" - {detail}" if detail and not condition else ""))


def make_cert(directory):
    cert = os.path.join(directory, "cert.pem")
    key = os.path.join(directory, "key.pem")
    try:
        subprocess.run(
            ["openssl", "req", "-x509", "-newkey", "rsa:2048", "-nodes",
             "-keyout", key, "-out", cert, "-days", "1",
             "-subj", "/CN=localhost"],
            check=True, capture_output=True, timeout=60)
    except (OSError, subprocess.SubprocessError):
        return None, None
    return cert, key


class FakeCamera:
    """Serves `frames` to one client, framed the way the printer does."""

    def __init__(self, cert, key, frames, split_header=True, drop=False):
        self.frames = frames
        self.split_header = split_header
        self.drop = drop
        self.auth = None
        self.ctx = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
        self.ctx.load_cert_chain(cert, key)
        self.sock = socket.socket()
        self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.sock.bind(("127.0.0.1", 0))
        self.sock.listen(1)
        self.port = self.sock.getsockname()[1]
        self.thread = threading.Thread(target=self._serve, daemon=True)
        self.thread.start()

    def _serve(self):
        try:
            raw, _ = self.sock.accept()
            with raw:
                conn = self.ctx.wrap_socket(raw, server_side=True)
                with conn:
                    self.auth = conn.recv(80)
                    if self.drop:
                        return
                    for frame in self.frames:
                        header = (struct.pack("<I", len(frame))
                                  + b"\x00" * 12)
                        if self.split_header:
                            conn.sendall(header)
                            conn.sendall(frame)
                        else:
                            # Everything in one TCP write - the naive
                            # "a 16-byte recv is a header" parser breaks
                            # here, a buffered one does not.
                            conn.sendall(header + frame)
        except (OSError, ssl.SSLError):
            pass
        finally:
            self.sock.close()


def jpeg(color=(120, 120, 120), size=(320, 240), blob=None):
    """A real JPEG; optionally with a bright rectangle standing in for a
    part left on the plate."""
    from PIL import Image, ImageDraw
    from io import BytesIO
    img = Image.new("RGB", size, color)
    if blob:
        ImageDraw.Draw(img).rectangle(blob, fill=(250, 250, 250))
    buf = BytesIO()
    img.save(buf, format="JPEG", quality=85)
    return buf.getvalue()


def textured(width=320, height=240, offset=(0, 0), blob=None):
    """A deterministic speckled scene, cropped at `offset` - two crops of
    the same scene at different offsets stand in for 'the bed/camera
    moved between the reference and the check'."""
    from PIL import Image, ImageDraw
    from io import BytesIO
    scene = Image.new("L", (width + 80, height + 80), 128)
    draw = ImageDraw.Draw(scene)
    seed = 12345
    def rnd(mod):
        nonlocal seed
        seed = (seed * 1103515245 + 12345) % (2 ** 31)
        return seed % mod
    for _ in range(260):
        x, y = rnd(width + 60), rnd(height + 60)
        shade = 40 + rnd(176)
        draw.rectangle((x, y, x + 14, y + 10), fill=shade)
    ox, oy = offset
    img = scene.crop((ox, oy, ox + width, oy + height)).convert("RGB")
    if blob:
        ImageDraw.Draw(img).rectangle(blob, fill=(250, 250, 250))
    buf = BytesIO()
    img.save(buf, format="JPEG", quality=85)
    return buf.getvalue()


class _FakeLLMResponse:
    def __init__(self, text):
        self.model = "claude-fake"
        self.stop_reason = "end_turn"
        block = type("Block", (), {"type": "text", "text": text})()
        self.content = [block]


def install_fake_anthropic(behaviour):
    """Put a fake `anthropic` module into sys.modules.

    behaviour: "json" (answers with valid JSON, but rejects the
    output_config kwarg first, exercising the old-SDK fallback) or
    "down" (every request raises).
    """
    import types

    class Messages:
        def create(self, **kwargs):
            if behaviour == "down":
                raise RuntimeError("no API key")
            if "output_config" in kwargs:
                raise TypeError("unexpected keyword argument 'output_config'")
            return _FakeLLMResponse(
                'Here you go: {"plate_visible": true, "bed_clear": true, '
                '"observation": "plate is empty"}')

    class Anthropic:
        def __init__(self, **kwargs):
            self.messages = Messages()

    module = types.ModuleType("anthropic")
    module.Anthropic = Anthropic
    previous = sys.modules.get("anthropic")
    sys.modules["anthropic"] = module
    return previous


def main():
    # --- auth packet shape -------------------------------------------
    packet = cam._auth_packet("12345678")
    check("auth packet is 80 bytes", len(packet) == 80, str(len(packet)))
    check("auth packet header", struct.unpack("<IIII", packet[:16])
          == (0x40, 0x3000, 0, 0))
    check("username field NUL-padded to 32",
          packet[16:48] == b"bblp" + b"\x00" * 28)
    check("access code field NUL-padded to 32",
          packet[48:80] == b"12345678" + b"\x00" * 24)

    try:
        from PIL import Image  # noqa: F401
        have_pillow = True
    except ImportError:
        have_pillow = False
        print("SKIP: Pillow not installed - image tests skipped")

    with tempfile.TemporaryDirectory() as tmp:
        cert, key = make_cert(tmp)
        if not cert:
            print("SKIP: openssl unavailable - TLS server tests skipped")
        elif not have_pillow:
            pass
        else:
            empty = jpeg()
            occupied = jpeg(blob=(90, 70, 230, 180))

            # --- happy path, header and payload in separate writes ----
            server = FakeCamera(cert, key, [empty])
            got = cam.capture_chamber_image("127.0.0.1", "12345678",
                                            timeout=10, port=server.port)
            check("captures a frame over the chamber protocol", got == empty)
            check("printer receives the 80-byte auth packet",
                  server.auth == cam._auth_packet("12345678"))

            # --- header and payload coalesced into one write ----------
            server = FakeCamera(cert, key, [empty], split_header=False)
            got = cam.capture_chamber_image("127.0.0.1", "12345678",
                                            timeout=10, port=server.port)
            check("handles a coalesced header+payload write", got == empty)

            # --- a corrupt frame is skipped, not returned -------------
            server = FakeCamera(cert, key, [b"\xff\xd8notjpeg", empty])
            got = cam.capture_chamber_image("127.0.0.1", "12345678",
                                            timeout=10, port=server.port)
            check("resyncs past a corrupt frame", got == empty)

            # --- wrong access code: printer just hangs up -------------
            server = FakeCamera(cert, key, [], drop=True)
            try:
                cam.capture_chamber_image("127.0.0.1", "bad", timeout=10,
                                          port=server.port)
                check("closed connection raises", False, "no exception")
            except RuntimeError as exc:
                check("closed connection explains the wrong access code",
                      "access code" in str(exc), str(exc))

            # --- check_bed_clear end to end ---------------------------
            ref = os.path.join(tmp, "ref.jpg")
            with open(ref, "wb") as fh:
                fh.write(empty)

            saved = os.path.join(tmp, "frame.jpg")
            server = FakeCamera(cert, key, [empty])
            verdict, msg = cam.check_bed_clear(
                "127.0.0.1", "12345678", reference_path=ref,
                transport="chamber", timeout=10, save_to=saved,
                port=server.port)
            check("end-to-end check on an empty bed reports CLEAR",
                  verdict is True, msg)
            check("the captured frame is saved for the record",
                  os.path.isfile(saved) and os.path.getsize(saved) > 0)

            server = FakeCamera(cert, key, [occupied])
            verdict, msg = cam.check_bed_clear(
                "127.0.0.1", "12345678", reference_path=ref,
                transport="chamber", timeout=10, port=server.port)
            check("end-to-end check with a part on the plate reports "
                  "NOT CLEAR", verdict is False, msg)

            # Nothing listening on this port at all.
            verdict, msg = cam.check_bed_clear(
                "127.0.0.1", "12345678", reference_path=ref,
                transport="chamber", timeout=3, port=server.port)
            check("unreachable camera degrades to UNKNOWN, never raises",
                  verdict is None and "camera unavailable" in msg, msg)

            clear, frac, detail = cam.compare_frames(empty, empty)
            check("identical frames read as clear", clear is True, detail)
            check("identical frames score ~0", frac < 0.005, str(frac))

            clear, frac, detail = cam.compare_frames(occupied, empty)
            check("a part on the plate reads as NOT clear",
                  clear is False, detail)
            check("part covers a plausible area fraction",
                  0.05 < frac < 0.6, str(frac))

            # --- lighting change alone must not trip the check --------
            darker = jpeg(color=(85, 85, 85))
            clear, frac, detail = cam.compare_frames(darker, empty)
            check("uniform lighting change still reads as clear",
                  clear is True, detail)

            # --- ROI restricts where we look --------------------------
            corner = jpeg(blob=(0, 0, 60, 45))
            clear, _, _ = cam.compare_frames(corner, empty)
            check("blob in the corner trips the full-frame check",
                  clear is False)
            clear, _, _ = cam.compare_frames(corner, empty,
                                             roi=(0.4, 0.4, 1.0, 1.0))
            check("same blob outside the ROI is ignored", clear is True)

            # --- a missing reference is UNKNOWN, not CLEAR ------------
            server = FakeCamera(cert, key, [empty])
            verdict, msg = cam.check_bed_clear(
                "127.0.0.1", "12345678",
                reference_path=os.path.join(tmp, "nope.jpg"),
                transport="chamber", timeout=10, port=server.port)
            check("missing reference never reports CLEAR",
                  verdict is None and "reference" in msg, msg)

    if have_pillow:
        # --- alignment: a moved bed/camera must not read as a part ----
        ref = textured(offset=(0, 0))
        moved = textured(offset=(12, 9))
        clear, frac, _ = cam.compare_frames(moved, ref, max_shift=0)
        check("rigid comparison flags a moved scene (the reported failure)",
              clear is False, str(frac))
        clear, frac, detail = cam.compare_frames(moved, ref)
        check("aligned comparison absorbs the move and reads clear",
              clear is True, detail)
        check("the detail names the alignment shift", "shift" in detail,
              detail)

        moved_part = textured(offset=(12, 9), blob=(90, 70, 230, 180))
        clear, frac, _ = cam.compare_frames(moved_part, ref)
        check("a part on a MOVED bed still reads NOT clear",
              clear is False, str(frac))

        # A corner blob on a featureless bed must not be shifted out of
        # the comparison window (alignment only kicks in when the rigid
        # score says "everything changed").
        corner = jpeg(blob=(0, 0, 60, 45))
        clear, _, _ = cam.compare_frames(corner, jpeg())
        check("alignment cannot shift a corner part out of view",
              clear is False)

        # --- multiple references (bed parks at several positions) -----
        refdir = os.path.join(tmp2 := tempfile.mkdtemp(), "refs")
        os.makedirs(refdir)
        with open(os.path.join(refdir, "a.jpg"), "wb") as fh:
            fh.write(textured(offset=(0, 0)))
        with open(os.path.join(refdir, "b.jpg"), "wb") as fh:
            fh.write(textured(offset=(48, 30)))
        far_frame = textured(offset=(48, 30))
        clear, _, _ = cam.compare_against_references(
            far_frame, os.path.join(refdir, "a.jpg"))
        check("a far bed position misses a single reference",
              clear is False)
        clear, _, detail = cam.compare_against_references(far_frame, refdir)
        check("a reference folder covers multiple bed positions",
              clear is True, detail)
        verdict, _, detail = cam.compare_against_references(
            far_frame, os.path.join(refdir, "nope.jpg"))
        check("a missing reference is UNKNOWN, not CLEAR",
              verdict is None and "reference" in detail, detail)
        shutil.rmtree(tmp2, ignore_errors=True)

    # --- ffmpeg discovery ---------------------------------------------
    with tempfile.TemporaryDirectory() as tmp3:
        fake = os.path.join(tmp3, "ffmpeg-fake")
        with open(fake, "w") as fh:
            fh.write("#!/bin/sh\n")
        check("explicit --ffmpeg path wins", cam._find_ffmpeg(fake) == fake)
        old_env = os.environ.get("FFMPEG")
        os.environ["FFMPEG"] = fake
        try:
            check("FFMPEG env var is honoured", cam._find_ffmpeg() == fake)
        finally:
            if old_env is None:
                os.environ.pop("FFMPEG", None)
            else:
                os.environ["FFMPEG"] = old_env

    # --- the LLM judge ------------------------------------------------
    verdict, msg = cam._parse_llm_verdict(
        '{"plate_visible": true, "bed_clear": true, "observation": "empty"}')
    check("LLM verdict: clear JSON parses", verdict is True, msg)
    verdict, msg = cam._parse_llm_verdict(
        'Sure! {"plate_visible": true, "bed_clear": false, '
        '"observation": "a part is on the plate"}')
    check("LLM verdict: JSON inside prose parses", verdict is False, msg)
    verdict, msg = cam._parse_llm_verdict(
        '{"plate_visible": false, "bed_clear": true, "observation": "dark"}')
    check("LLM verdict: unseen plate is UNKNOWN, never CLEAR",
          verdict is None, msg)
    verdict, msg = cam._parse_llm_verdict("I cannot tell.")
    check("LLM verdict: non-JSON answer is UNKNOWN", verdict is None, msg)

    previous = install_fake_anthropic("json")
    try:
        verdict, msg = cam.llm_bed_check(b"\xff\xd8fake\xff\xd9")
        check("LLM judge end-to-end (incl. old-SDK output_config "
              "fallback)", verdict is True, msg)
    finally:
        if previous is None:
            sys.modules.pop("anthropic", None)
        else:
            sys.modules["anthropic"] = previous
    previous = install_fake_anthropic("down")
    try:
        verdict, msg = cam.llm_bed_check(b"\xff\xd8fake\xff\xd9")
        check("an unreachable LLM degrades to UNKNOWN, never raises",
              verdict is None and "unavailable" in msg, msg)
    finally:
        if previous is None:
            sys.modules.pop("anthropic", None)
        else:
            sys.modules["anthropic"] = previous

    # --- ROI parsing --------------------------------------------------
    check("parse_roi accepts fractions",
          cam.parse_roi("0.1,0.2,0.9,0.8") == (0.1, 0.2, 0.9, 0.8))
    for bad in ("0.1,0.2,0.9", "0.9,0.2,0.1,0.8", "0,0,2,1"):
        try:
            cam.parse_roi(bad)
            check(f"parse_roi rejects {bad!r}", False)
        except ValueError:
            check(f"parse_roi rejects {bad!r}", True)

    # --- RTSP URL shape -----------------------------------------------
    url = cam.rtsp_url("192.168.1.42", "12345678")
    check("rtsp url matches the documented form",
          url == "rtsps://bblp:12345678@192.168.1.42:322/streaming/live/1",
          url)

    print(f"\n{len(PASSES)} passed, {len(FAILURES)} failed")
    for name in FAILURES:
        print(f"  FAILED: {name}")
    return 1 if FAILURES else 0


if __name__ == "__main__":
    sys.exit(main())
