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
