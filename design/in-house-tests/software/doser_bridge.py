#!/usr/bin/env python3
"""Doser bridge: runs on the doser's Raspberry Pi Zero 2 W.

It holds the doser Pico's USB serial port and serves a line protocol on
127.0.0.1 only. The bench Pi 5 reaches it through an SSH port forward:

    ssh -N -L 8765:127.0.0.1:8765 <user>@<zero>

Requests (one per line):
    r 360                      any doser firmware command (main_three_phase.py)
    {"cmd": "r 3600", "timeout": 120, "id": 3}     the same as JSON
    .ping | .info              bridge health
    .weigh <Hz> <seconds>      stream balance readings (polls `w`)
    .abort                     Ctrl-C + soft reset of the doser Pico (stops a
                               blocking move; the doser re-runs its boot,
                               which moves the tilt servos to their default)
Replies: one JSON object per line. `.weigh` sends {"ev": "w", ...} lines
first, then its reply.

The doser firmware prints no prompt, so the bridge marks the end of each
command by sending an unknown command (`zz_eoc_<n>`) after it: the Pico
handles lines in order, so its "unknown command 'zz_eoc_<n>'" reply comes
only after the real command has finished.

Python 3.13 + pyserial. `--mock` serves a simulated doser (no hardware);
the bench simulator and the tests use the same mock in-process.
"""

import argparse
import ipaddress
import json
import logging
import random
import re
import socketserver
import threading
import time

DEFAULT_PORT = 8765
MARK = "zz_eoc_"
LOG = logging.getLogger("doser_bridge")

_SCALE_RE = re.compile(r"\[scale\]\s+(ST|US|OL)\s+(\S+)\s*(\S*)")
_RPM_RE = re.compile(r"stepper:\s+([\d.]+)\s+auger rpm")
_ERR_MARKERS = ("command failed", "unknown command", "unknown preset", "unavailable",
                "no response", "usage:")


class BridgeError(Exception):
    pass


# ---------------------------------------------------------------------------
# Talking to the doser Pico
# ---------------------------------------------------------------------------

class DoserLink:
    """One command at a time over a serial-like object (write, readline
    returning b"" on timeout, optional reset_input_buffer)."""

    def __init__(self, ser, default_rpm=60.0):
        self.ser = ser
        self.lock = threading.Lock()
        self.n = 0
        self.rpm = default_rpm          # auger rpm used by `r` (tracked from `rpm` and `s`)
        self.stray = []
        self._buf = b""

    def _send(self, text):
        self.ser.write((text + "\n").encode())
        flush = getattr(self.ser, "flush", None)
        if flush:
            flush()

    def _readline(self):
        """One complete line, or None. pyserial's readline() can hand back a
        partial line when its timeout expires, so partials are buffered."""
        raw = self.ser.readline()
        if not raw:
            return None
        self._buf += raw
        if not self._buf.endswith(b"\n"):
            return None
        line, self._buf = self._buf, b""
        return line.decode(errors="replace").strip()

    def _drain(self):
        """Keep stray output (boot messages, late lines) out of the next reply.
        Returns at once when the port reports nothing waiting."""
        while True:
            if getattr(self.ser, "in_waiting", None) == 0:
                return
            line = self._readline()
            if line is None:
                if self._buf:
                    continue
                return
            if line:
                self.stray.append(line)
                del self.stray[:-50]

    def default_timeout(self, cmd):
        verb, _, arg = cmd.strip().partition(" ")
        verb = verb.lower()
        try:
            x = float(arg) if arg else 0.0
        except ValueError:
            x = 0.0
        if verb == "r":
            return abs(x) / 360.0 * 60.0 / max(1.0, min(self.rpm, 60.0)) * 2.0 + 10.0
        if verb == "d":
            return 60.0
        if verb in ("g", "dose"):
            return 660.0
        if verb in ("a", "p", "t", "w"):
            return 15.0
        if verb == "z":
            return 20.0
        return 30.0

    def command(self, cmd, timeout=None):
        cmd = cmd.strip()
        if not cmd:
            raise BridgeError("empty command")
        if "\n" in cmd or "\r" in cmd or "\x03" in cmd or "\x04" in cmd:
            raise BridgeError("one line per command")
        timeout = self.default_timeout(cmd) if timeout is None else float(timeout)
        with self.lock:
            self._drain()
            self.n += 1
            mark = "{}{}".format(MARK, self.n)
            t0 = time.time()
            self._send(cmd)
            self._send(mark)
            lines = []
            deadline = time.monotonic() + timeout
            done = False
            while time.monotonic() < deadline:
                line = self._readline()
                if not line:
                    continue
                if mark in line:
                    done = True
                    break
                lines.append(line)
            t1 = time.time()
        res = parse_result(cmd, lines)
        res.update({"cmd": cmd, "lines": lines, "t0": round(t0, 3), "t1": round(t1, 3),
                    "elapsed_s": round(t1 - t0, 3)})
        if not done:
            res["ok"] = False
            res["err"] = "timeout after {:.0f} s (doser busy or disconnected)".format(timeout)
        if res.get("ok") and cmd.lower().startswith("rpm "):
            try:
                self.rpm = float(cmd.split()[1])
            except (IndexError, ValueError):
                pass
        # (the doser's `s` prints config.STEPPER_SPEED_RPM, not the live
        # speed, so its rpm is reported but not tracked)
        return res

    def abort(self, wait_s=20.0):
        """Interrupt a blocking command and soft-reset the doser Pico."""
        with self.lock:
            self.ser.write(b"\x03\x03")
            time.sleep(0.3)
            self.ser.write(b"\x04")
            lines = []
            deadline = time.monotonic() + wait_s
            ready = False
            while time.monotonic() < deadline:
                line = self._readline()
                if line is None:
                    continue
                lines.append(line)
                if "[rig] ready" in line:
                    ready = True
                    break
        return {"ok": ready, "cmd": ".abort", "lines": lines[-20:],
                **({} if ready else {"err": "no '[rig] ready' after soft reset"})}


def parse_result(cmd, lines):
    """Turn the doser's text replies into fields."""
    res = {"ok": True}
    for line in lines:
        low = line.lower()
        if any(m in low for m in _ERR_MARKERS):
            res["ok"] = False
            res["err"] = line
            break
    verb = cmd.split()[0].lower() if cmd.split() else ""
    if verb == "w":
        for line in lines:
            m = _SCALE_RE.search(line)
            if m:
                status, val, unit = m.groups()
                res["status"] = status
                res["stable"] = status == "ST"
                res["unit"] = unit or "g"
                try:
                    res["grams"] = float(val)
                except ValueError:
                    res["grams"] = None
                if status == "OL":
                    res["ok"] = False
                    res["err"] = "balance overload"
                break
        else:
            if res["ok"]:
                res["ok"] = False
                res["err"] = "no scale reading in reply"
    if verb == "s":
        for line in lines:
            m = _RPM_RE.search(line)
            if m:
                res["rpm"] = float(m.group(1))
    return res


# ---------------------------------------------------------------------------
# A simulated doser Pico (main_three_phase.py's REPL replies)
# ---------------------------------------------------------------------------

class SimplePlant:
    """Default physics for --mock: powder leaves at g_per_rev, more at steeper
    tilt, onto a balance with 0.1 mg resolution and a little noise."""

    def __init__(self, g_per_rev=0.05, seed=0):
        self.g_per_rev = g_per_rev
        self.mass = 0.0
        self.tare_g = 0.0
        self.plate_deg = 45.0
        self.rng = random.Random(seed)

    def rotate(self, auger_deg, rpm):
        f = 0.3 + self.plate_deg / 45.0 * 0.7
        revs = max(0.0, auger_deg) / 360.0
        self.mass += max(0.0, self.rng.gauss(self.g_per_rev * f * revs, 0.05 * self.g_per_rev * revs))

    def tilt(self, plate_deg):
        self.plate_deg = plate_deg

    def tap(self, n):
        self.mass += 0.0005 * n

    def tare(self):
        self.tare_g = self.mass

    def grams(self):
        return round(self.mass - self.tare_g + self.rng.gauss(0, 0.00005), 4), True

    def estop(self):
        pass


class MockDoserSerial:
    """Serial-port stand-in that answers like main_three_phase.py."""

    PRESETS = {"horizontal": 0.0, "tilt": 22.5, "vertical": 45.0, "tip": 67.5}

    def __init__(self, plant=None, rpm_command=True, seed=0):
        self.plant = plant or SimplePlant(seed=seed)
        self.rpm = 60.0
        self.rpm_command = rpm_command
        self.out = []
        self.inbuf = b""
        self.plate = 45.0
        self.in_repl = False
        self.commands = []

    # serial surface
    def write(self, data):
        for byte in data:
            ch = bytes([byte])
            if ch == b"\x03":
                self.out += ["Traceback (most recent call last):", "KeyboardInterrupt:", ">>> "]
                self.in_repl = True
                self.inbuf = b""
            elif ch == b"\x04":
                self.out += ["MPY: soft reboot", "[rig] bringing up powder-doser test module",
                             "[rig] ready -- type 'h' for help"]
                self.in_repl = False
                self.plate = 45.0
                self.plant.tilt(45.0)
            elif ch in (b"\n", b"\r"):
                line, self.inbuf = self.inbuf.decode(), b""
                if line.strip() and not self.in_repl:
                    self._handle(line.strip())
            else:
                self.inbuf += ch
        return len(data)

    def flush(self):
        pass

    def readline(self):
        if not self.out:
            return b""
        return (self.out.pop(0) + "\r\n").encode()

    def reset_input_buffer(self):
        self.out = []

    def _handle(self, line):
        self.commands.append(line)
        cmd, _, arg = line.partition(" ")
        cmd = cmd.lower()
        p = self.out
        try:
            if cmd in ("h", "?", "help"):
                p += ["Three-phase doser commands (...)", "  r <deg>  rotate auger"]
            elif cmd == "s":
                p.append("stepper: {} auger rpm (gear 2.20:1, max 109), microsteps=1/8, "
                         "usteps/auger-rev=3520, dispense_deg=360.0 auger deg".format(self.rpm))
                p.append("plate: angle={:.1f} plate deg (gear 2:1), range=[0..90]".format(self.plate))
            elif cmd == "r":
                self.plant.rotate(float(arg), self.rpm)
            elif cmd == "d":
                self.plant.rotate(360.0, self.rpm)
            elif cmd == "rpm" and self.rpm_command:
                self.rpm = min(float(arg), 240.0 / 2.2)
                p.append("[stepper] {:.1f} auger RPM".format(self.rpm))
            elif cmd == "t":
                self.plant.tap(3)
            elif cmd == "a":
                self.plate = max(0.0, min(90.0, float(arg)))
                self.plant.tilt(self.plate)
            elif cmd == "p":
                if arg not in self.PRESETS:
                    p.append("unknown preset {!r}; choose from {}".format(arg, list(self.PRESETS)))
                    return
                self.plate = self.PRESETS[arg]
                self.plant.tilt(self.plate)
            elif cmd == "w":
                g, stable = self.plant.grams()
                if g is None:
                    p.append("[scale] OL None g")
                else:
                    p.append("[scale] {} {} g".format("ST" if stable else "US", g))
            elif cmd == "z":
                self.plant.tare()
                p.append("[scale] re-zeroed")
            elif cmd in ("!", "stop"):
                self.plant.estop()
                p.append("[rig] EMERGENCY STOP")
            else:
                p.append("unknown command {!r}; 'h' for help".format(cmd))
        except Exception as exc:  # noqa: BLE001 - mirror the firmware's catch-all
            p.append("[rig] command failed: {!r}".format(exc))


# ---------------------------------------------------------------------------
# Request handling (shared by the TCP server and in-process clients)
# ---------------------------------------------------------------------------

class Bridge:
    def __init__(self, link, port_name="?"):
        self.link = link
        self.port_name = port_name
        self.t_start = time.time()
        self.requests = 0

    def handle_request(self, line, send):
        """Process one request line; call send(dict) for each output line."""
        self.requests += 1
        line = line.strip()
        if not line:
            return
        rid = None
        timeout = None
        if line.startswith("{"):
            try:
                req = json.loads(line)
                cmd = str(req["cmd"])
                rid = req.get("id")
                timeout = req.get("timeout")
            except (ValueError, KeyError, TypeError) as exc:
                send({"ok": False, "err": "bad JSON request: {}".format(exc)})
                return
        else:
            cmd = line
        try:
            if cmd.startswith("."):
                out = self._bridge_command(cmd, send)
            else:
                out = self.link.command(cmd, timeout)
        except BridgeError as exc:
            out = {"ok": False, "cmd": cmd, "err": str(exc)}
        except Exception as exc:  # noqa: BLE001 - keep serving
            LOG.exception("request failed")
            out = {"ok": False, "cmd": cmd, "err": repr(exc)}
        if rid is not None:
            out["id"] = rid
        send(out)

    def _bridge_command(self, cmd, send):
        parts = cmd.split()
        verb = parts[0]
        if verb == ".ping":
            return {"ok": True, "cmd": verb, "pong": True, "t": round(time.time(), 3)}
        if verb == ".info":
            return {"ok": True, "cmd": verb, "port": self.port_name, "uptime_s": round(time.time() - self.t_start, 1),
                    "requests": self.requests, "commands": self.link.n, "rpm": self.link.rpm,
                    "stray": self.link.stray[-10:]}
        if verb == ".abort":
            return self.link.abort()
        if verb == ".weigh":
            hz = float(parts[1]) if len(parts) > 1 else 5.0
            secs = float(parts[2]) if len(parts) > 2 else 10.0
            if not (0 < hz <= 20 and 0 < secs <= 3600):
                raise BridgeError(".weigh <Hz 0-20> <seconds 0-3600>")
            return self._weigh_stream(hz, secs, send)
        raise BridgeError("unknown bridge command {}".format(verb))

    def _weigh_stream(self, hz, secs, send):
        period = 1.0 / hz
        t_end = time.monotonic() + secs
        n = bad = 0
        next_t = time.monotonic()
        while time.monotonic() < t_end:
            r = self.link.command("w", timeout=3.0)
            if r.get("ok"):
                send({"ev": "w", "t": round((r["t0"] + r["t1"]) / 2.0, 3), "g": r["grams"],
                      "st": r["stable"]})
                n += 1
            else:
                bad += 1
            next_t += period
            delay = next_t - time.monotonic()
            if delay > 0:
                time.sleep(delay)
            else:
                next_t = time.monotonic()
        return {"ok": True, "cmd": ".weigh", "n": n, "failed": bad}


class _Handler(socketserver.StreamRequestHandler):
    def handle(self):
        bridge = self.server.bridge
        LOG.info("client %s connected", self.client_address)

        def send(obj):
            self.wfile.write((json.dumps(obj) + "\n").encode())
            self.wfile.flush()
        for raw in self.rfile:
            try:
                bridge.handle_request(raw.decode(errors="replace"), send)
            except (BrokenPipeError, ConnectionResetError):
                break
        LOG.info("client %s gone", self.client_address)


class BridgeServer(socketserver.ThreadingTCPServer):
    allow_reuse_address = True
    daemon_threads = True

    def __init__(self, bridge, host="127.0.0.1", port=DEFAULT_PORT):
        if not ipaddress.ip_address(host).is_loopback:
            raise BridgeError("the bridge only listens on loopback; use an SSH forward")
        self.bridge = bridge
        super().__init__((host, port), _Handler)


def open_serial(port, baud=115200):
    import serial  # pyserial; imported here so --mock needs no hardware stack
    ser = serial.Serial(port, baud, timeout=0.1, write_timeout=2)
    time.sleep(0.2)
    ser.reset_input_buffer()
    return ser


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--port", default="/dev/ttyACM0", help="doser Pico serial port")
    ap.add_argument("--listen", type=int, default=DEFAULT_PORT, help="TCP port on 127.0.0.1")
    ap.add_argument("--host", default="127.0.0.1", help="loopback address to bind")
    ap.add_argument("--mock", action="store_true", help="simulated doser, no hardware")
    ap.add_argument("-v", "--verbose", action="store_true")
    args = ap.parse_args(argv)
    logging.basicConfig(level=logging.DEBUG if args.verbose else logging.INFO,
                        format="%(asctime)s %(levelname)s %(message)s")
    ser = MockDoserSerial() if args.mock else open_serial(args.port)
    bridge = Bridge(DoserLink(ser), "mock" if args.mock else args.port)
    with BridgeServer(bridge, args.host, args.listen) as srv:
        LOG.info("doser bridge on %s:%d (%s)", args.host, args.listen, bridge.port_name)
        try:
            srv.serve_forever()
        except KeyboardInterrupt:
            pass


if __name__ == "__main__":
    main()
