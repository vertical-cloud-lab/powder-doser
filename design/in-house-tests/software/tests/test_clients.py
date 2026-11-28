"""The bench's real-hardware clients, against stand-ins on this machine:
DoserClient -> a live bridge (TCP, mock doser); AccessoryClient -> the
accessory firmware behind a pseudo-terminal (pyserial, reader thread)."""

import os
import sys
import threading
import time

import pytest

import doser_bridge as db
from bench import devices


@pytest.fixture
def bridge():
    srv = db.BridgeServer(db.Bridge(db.DoserLink(db.MockDoserSerial())), "127.0.0.1", 0)
    th = threading.Thread(target=srv.serve_forever, daemon=True)
    th.start()
    yield srv.server_address[1]
    srv.shutdown()
    srv.server_close()


def test_doser_client_over_tcp(bridge):
    c = devices.DoserClient("127.0.0.1", bridge)
    c.tare()
    c.tilt(45)
    c.rotate(720)
    g, stable = c.weigh()
    assert g > 0 and stable
    assert c.set_rpm(20) is True
    samples = c.weigh_stream(20, 0.3)
    assert len(samples) >= 3 and all(s[1] == pytest.approx(g, abs=0.01) for s in samples)
    mv = c.rotate_async(360)
    assert mv.wait(10)["ok"]
    with pytest.raises(devices.DeviceError):
        c.cmd("p sideways")
    c.close()


@pytest.mark.skipif(not sys.platform.startswith("linux"), reason="needs a pty")
def test_accessory_client_over_a_pty():
    fw = devices._import_firmware()
    cfg, sim_hw = fw
    master, slave = os.openpty()
    name = os.ttyname(slave)
    sim = sim_hw.SimAccessory(cfg)
    stop = threading.Event()

    def pico():
        buf = b""
        last = time.monotonic()
        os.set_blocking(master, False)
        while not stop.is_set():
            try:
                chunk = os.read(master, 256)
            except BlockingIOError:
                chunk = b""
            buf += chunk
            while b"\n" in buf:
                line, buf = buf.split(b"\n", 1)
                sim.acc.handle(line.decode())
            now = time.monotonic()
            sim.clock.advance((now - last) * 1000.0)
            last = now
            sim.acc.poll()
            for out in sim.lines:
                os.write(master, (out + "\r\n").encode())
            del sim.lines[:]
            time.sleep(0.002)
    th = threading.Thread(target=pico, daemon=True)
    th.start()
    try:
        acc = devices.AccessoryClient(name)
        st = acc.call("status")
        assert st["devices"]["imu"]
        r = acc.call("table 5 rate=10 stream=10")
        assert r["eta_s"] == pytest.approx(0.5)
        done = acc.wait_done("table", 5)
        assert done is not None and done["cmd_deg"] == pytest.approx(5.0)
        assert acc.take("imu")
        with pytest.raises(devices.DeviceError):
            acc.call("table 200")
        acc.close()
    finally:
        stop.set()
        th.join(1)
        os.close(master)
        os.close(slave)
