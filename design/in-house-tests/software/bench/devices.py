"""Devices as the bench Pi sees them, with simulated stand-ins.

  DoserClient        the doser, through doser_bridge.py on the Zero 2 W
                     (TCP 127.0.0.1:8765, reached by an SSH port forward)
  LocalDoser         the same API over an in-process bridge + mock doser (--sim)
  AccessoryClient    the accessory Pico 2 W on USB serial (JSON lines)
  SimAccessoryClient the real accessory firmware on register-level fakes (--sim)
  PiCamera           Picamera2 (Camera Module 3 or HQ camera)
  FileCamera         replays image files from a folder (tests, re-analysis)
  SimCamera          renders the simulated scene
  BoxSensors         SHT45s in the humidity boxes via a TCA9548A on the Pi's I2C
"""

import glob
import json
import os
import socket
import sys
import threading
import time

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
SOFTWARE = os.path.dirname(HERE)
FIRMWARE = os.path.join(os.path.dirname(SOFTWARE), "firmware")


class DeviceError(Exception):
    pass


# ---------------------------------------------------------------------------
# Doser (via the bridge)
# ---------------------------------------------------------------------------

class _DoserAPI:
    """Helpers shared by the TCP client and the in-process one."""

    rpm_supported = None

    def cmd(self, text, timeout=None, check=True):
        r = self.request(text, timeout)
        if check and not r.get("ok"):
            raise DeviceError("doser '{}': {}".format(text, r.get("err")))
        return r

    def rotate(self, auger_deg, timeout=None):
        return self.cmd("r {:g}".format(auger_deg), timeout)

    def tilt(self, plate_deg):
        return self.cmd("a {:g}".format(plate_deg))

    def preset(self, name):
        return self.cmd("p {}".format(name))

    def tap(self):
        return self.cmd("t")

    def weigh(self):
        r = self.cmd("w")
        return r["grams"], r["stable"]

    def weigh_stable(self, tries=10, pause=0.5, sleep=time.sleep):
        g = None
        for _ in range(tries):
            g, st = self.weigh()
            if st:
                return g
            sleep(pause)
        return g

    def tare(self):
        return self.cmd("z")

    def set_rpm(self, rpm):
        """Needs the doser firmware's `rpm` command (software/doser_patches).
        Returns False (and leaves the doser's default speed) without it."""
        r = self.request("rpm {:g}".format(rpm))
        self.rpm_supported = bool(r.get("ok"))
        return self.rpm_supported

    def estop(self):
        return self.request("!")


class DoserClient(_DoserAPI):
    def __init__(self, host="127.0.0.1", port=8765, connect_timeout=5.0):
        self.addr = (host, int(port))
        self.sock = socket.create_connection(self.addr, timeout=connect_timeout)
        self.sock.settimeout(None)
        self.f = self.sock.makefile("rwb")
        self.n = 0
        self.lock = threading.Lock()

    def _send(self, obj):
        self.f.write((json.dumps(obj) + "\n").encode())
        self.f.flush()

    def _recv(self):
        line = self.f.readline()
        if not line:
            raise DeviceError("bridge closed the connection")
        return json.loads(line)

    def request(self, text, timeout=None):
        with self.lock:
            self.n += 1
            req = {"cmd": text, "id": self.n}
            if timeout is not None:
                req["timeout"] = timeout
            self._send(req)
            while True:
                msg = self._recv()
                if "ev" not in msg:
                    return msg

    def weigh_stream(self, hz, seconds, on_sample=None):
        with self.lock:
            self._send({"cmd": ".weigh {:g} {:g}".format(hz, seconds)})
            out = []
            while True:
                msg = self._recv()
                if msg.get("ev") == "w":
                    out.append((msg["t"], msg["g"], msg["st"]))
                    if on_sample:
                        on_sample(msg)
                else:
                    return out

    def rotate_async(self, auger_deg, timeout=None):
        """Turn the auger in a worker thread (r blocks the doser until done),
        so the caller can capture frames meanwhile. Uses its own connection."""
        res = {}

        def work():
            c = DoserClient(*self.addr)
            try:
                res["r"] = c.rotate(auger_deg, timeout)
            except Exception as exc:  # noqa: BLE001
                res["err"] = exc
            finally:
                c.close()
        th = threading.Thread(target=work, daemon=True)
        th.start()
        return _AsyncMove(th, res)

    def close(self):
        try:
            self.f.close()
            self.sock.close()
        except OSError:
            pass


class _AsyncMove:
    def __init__(self, thread, res):
        self.thread = thread
        self.res = res

    def wait(self, timeout=None):
        self.thread.join(timeout)
        if "err" in self.res:
            raise self.res["err"]
        return self.res.get("r")


def _import_bridge():
    if SOFTWARE not in sys.path:
        sys.path.insert(0, SOFTWARE)
    import doser_bridge
    return doser_bridge


class LocalDoser(_DoserAPI):
    """The doser API over an in-process bridge talking to MockDoserSerial.
    plant: object with rotate(deg, rpm) tilt(deg) tap(n) tare() grams() estop()."""

    def __init__(self, plant=None, world=None):
        db = _import_bridge()
        self.ser = db.MockDoserSerial(plant)
        self.bridge = db.Bridge(db.DoserLink(self.ser), "sim")
        self.world = world

    def request(self, text, timeout=None):
        out = []
        line = json.dumps({"cmd": text, "timeout": timeout}) if timeout else text
        self.bridge.handle_request(line, out.append)
        return [m for m in out if "ev" not in m][-1]

    def weigh_stream(self, hz, seconds, on_sample=None):
        samples = []
        n = int(round(hz * seconds))
        for _ in range(n):
            g, st = self.weigh()
            t = self.world.now() if self.world else time.time()
            samples.append((t, g, st))
            if on_sample:
                on_sample({"ev": "w", "t": t, "g": g, "st": st})
            if self.world:
                self.world.advance(1.0 / hz)
        return samples

    def rotate_async(self, auger_deg, timeout=None):
        if self.world is not None:
            return self.world.start_rotation(auger_deg, self.ser.rpm)
        r = self.rotate(auger_deg, timeout)
        return _Done(r)


class _Done:
    def __init__(self, r):
        self.r = r

    def wait(self, timeout=None):
        return self.r


# ---------------------------------------------------------------------------
# Accessory Pico
# ---------------------------------------------------------------------------

class _AccessoryAPI:
    def call(self, line, timeout=5.0, check=True):
        raise NotImplementedError

    def wait_done(self, task, timeout):
        return self.wait_event(lambda e: e.get("ev") == "done" and e.get("task") == task, timeout)

    def take(self, ev=None):
        """Remove and return buffered events (of one kind)."""
        raise NotImplementedError


class AccessoryClient(_AccessoryAPI):
    """USB serial to the accessory Pico. A reader thread sorts lines into
    replies (matched by request id) and events (queued)."""

    def __init__(self, port="/dev/ttyACM0", baud=115200):
        import serial
        self.ser = serial.Serial(port, baud, timeout=0.05)
        self.n = 0
        self.replies = {}
        self.cv = threading.Condition()
        self.events = []
        self.running = True
        self.th = threading.Thread(target=self._reader, daemon=True)
        self.th.start()
        self.call("ping")

    def _reader(self):
        buf = b""
        while self.running:
            chunk = self.ser.read(256)
            if not chunk:
                continue
            buf += chunk
            while b"\n" in buf:
                raw, buf = buf.split(b"\n", 1)
                try:
                    msg = json.loads(raw.decode(errors="replace").strip() or "{}")
                except ValueError:
                    continue
                if not msg:
                    continue
                msg["t_host"] = time.time()
                with self.cv:
                    if "ok" in msg and "id" in msg:
                        self.replies[msg["id"]] = msg
                    elif "ev" in msg:
                        self.events.append(msg)
                    self.cv.notify_all()

    def call(self, line, timeout=5.0, check=True):
        with self.cv:
            self.n += 1
            rid = self.n
        self.ser.write("{} #{}\n".format(line, rid).encode())
        deadline = time.time() + timeout
        with self.cv:
            while rid not in self.replies:
                left = deadline - time.time()
                if left <= 0:
                    raise DeviceError("accessory: no reply to '{}'".format(line))
                self.cv.wait(left)
            r = self.replies.pop(rid)
        if check and not r.get("ok"):
            raise DeviceError("accessory '{}': {}".format(line, r.get("err")))
        return r

    def wait_event(self, pred, timeout):
        deadline = time.time() + timeout
        with self.cv:
            while True:
                for i, e in enumerate(self.events):
                    if pred(e):
                        return self.events.pop(i)
                left = deadline - time.time()
                if left <= 0:
                    return None
                self.cv.wait(left)

    def take(self, ev=None):
        with self.cv:
            out = [e for e in self.events if ev is None or e.get("ev") == ev]
            self.events = [e for e in self.events if not (ev is None or e.get("ev") == ev)]
        return out

    def advance(self, seconds):
        time.sleep(seconds)

    def close(self):
        self.running = False
        try:
            self.call("estop", timeout=1.0, check=False)
        except DeviceError:
            pass
        self.ser.close()


def _import_firmware():
    if FIRMWARE not in sys.path:
        sys.path.insert(0, FIRMWARE)
    import config as fw_config
    import sim_hw
    return fw_config, sim_hw


class SimAccessoryClient(_AccessoryAPI):
    """The real accessory firmware (accessory_main.Accessory) on sim_hw's
    fakes, sharing the world's fake clock."""

    def __init__(self, world=None, profile=None, hooks=None, seed=0):
        cfg, sim_hw = _import_firmware()
        clock = world.clock if world is not None else None
        if hooks is None and world is not None:
            hooks = world.accessory_hooks()
        self.sim = sim_hw.SimAccessory(cfg, hooks=hooks, seed=seed, clock=clock, profile=profile)
        self.clock = self.sim.clock
        self.world = world
        if world is not None:
            world.attach_accessory(self)

    @property
    def hw(self):
        return self.sim.hw

    def call(self, line, timeout=5.0, check=True):
        r = self.sim.call(line)
        if r is None:
            raise DeviceError("accessory: no reply to '{}'".format(line))
        if check and not r.get("ok"):
            raise DeviceError("accessory '{}': {}".format(line, r.get("err")))
        return r

    def _step(self, ms=2):
        evs = self.sim.step(ms)
        if self.world is not None:
            self.world.tick(ms / 1000.0)
        return evs

    def wait_event(self, pred, timeout):
        for i, e in enumerate(self.sim.events):
            if pred(e):
                return self.sim.events.pop(i)
        waited = 0
        while waited < timeout * 1000:
            for e in self._step(2):
                if pred(e):
                    self.sim.events.remove(e)
                    return e
            waited += 2
        return None

    def take(self, ev=None):
        return self.sim.take_events(ev)

    def advance(self, seconds):
        """Step the firmware in 2 ms ticks; with no task running and a long
        wait (hours in the humidity test), jump the clock instead."""
        if seconds > 2.0 and not self.sim.acc.tasks:
            self.sim.clock.advance(seconds * 1000.0)
            if self.world is not None:
                self.world.tick(seconds)
            self.sim.acc.poll()
            return
        for _ in range(int(round(seconds * 500))):
            self._step(2)

    def close(self):
        pass


# ---------------------------------------------------------------------------
# Cameras
# ---------------------------------------------------------------------------

class PiCamera:
    """Picamera2 still capture as a grey float image (0..1)."""

    def __init__(self, index=0, size=(4608, 2592), exposure_us=None, gain=None):
        from picamera2 import Picamera2
        self.cam = Picamera2(index)
        cfg = self.cam.create_still_configuration(main={"size": size, "format": "RGB888"})
        self.cam.configure(cfg)
        ctrl = {}
        if exposure_us:
            ctrl.update({"ExposureTime": int(exposure_us), "AeEnable": False})
        if gain:
            ctrl["AnalogueGain"] = float(gain)
        if ctrl:
            self.cam.set_controls(ctrl)
        self.cam.start()
        time.sleep(1.0)

    def capture(self):
        rgb = self.cam.capture_array("main")
        return (rgb[..., :3].astype(np.float32) @ np.array([0.114, 0.587, 0.299], np.float32)) / 255.0

    def close(self):
        self.cam.stop()
        self.cam.close()


class FileCamera:
    """Returns the images in a folder in name order (cycling)."""

    def __init__(self, folder, pattern="*.png"):
        self.files = sorted(glob.glob(os.path.join(folder, pattern)))
        if not self.files:
            raise DeviceError("no images in {}".format(folder))
        self.i = 0

    def capture(self):
        from PIL import Image
        f = self.files[self.i % len(self.files)]
        self.i += 1
        a = np.asarray(Image.open(f).convert("L"), np.float32) / 255.0
        return a

    def close(self):
        pass


class SimCamera:
    def __init__(self, world, name="silhouette"):
        self.world = world
        self.name = name

    def capture(self):
        return self.world.render(self.name)

    def close(self):
        pass


# ---------------------------------------------------------------------------
# Humidity-box sensors on the bench Pi (TCA9548A + SHT45)
# ---------------------------------------------------------------------------

class BoxSensors:
    def __init__(self, bus=1, mux_addr=0x70, sht_addr=0x44, channels=None):
        from smbus2 import SMBus, i2c_msg
        self.SMBus, self.msg = SMBus, i2c_msg
        self.bus = SMBus(bus)
        self.mux = mux_addr
        self.sht = sht_addr
        self.channels = channels or {"MgCl2": 0, "MgNO3": 1, "NaCl": 2, "KCl": 3, "silica": 4}

    def read(self, box):
        sys.path.insert(0, FIRMWARE)
        import units
        ch = self.channels[box]
        self.bus.write_byte(self.mux, 1 << ch)
        self.bus.i2c_rdwr(self.msg.write(self.sht, [0xFD]))
        time.sleep(0.01)
        rd = self.msg.read(self.sht, 6)
        self.bus.i2c_rdwr(rd)
        b = bytes(rd)
        if units.crc8_sensirion(b[0:2]) != b[2] or units.crc8_sensirion(b[3:5]) != b[5]:
            raise DeviceError("SHT45 CRC error on channel {}".format(ch))
        return units.sht45_convert((b[0] << 8) | b[1], (b[3] << 8) | b[4])
