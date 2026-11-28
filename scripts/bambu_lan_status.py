"""Read a Bambu printer's status over LAN MQTT, read only, with the standard library only.

It subscribes to the printer's report topic, sends one ``pushall`` (a status request that
changes nothing on the printer), collects reports for a few seconds and prints selected
fields as JSON: job state and name, layer, errors, HMS, camera/timelapse flags, and each
nozzle's diameter and type. The printer's IP, serial and access code are never printed.

The printers are only reachable from the doser Pi's LAN, and the Pi has no MQTT library,
so the usual way to run it is from the runner, sending the program over stdin with a
``CFG`` line in front. Nothing is installed or written on the Pi, and the access code
never reaches a command line::

    { python3 -I -c 'import json,os; print("CFG = " + json.dumps({"ip": os.environ["H2D_IP"],
        "serial": os.environ["H2D_SERIAL"], "code": os.environ["H2D_ACCESS_CODE"]}))';
      cat scripts/bambu_lan_status.py; } \
      | ssh "$RPI_POWDER_DOSER_USERNAME@$RPI_POWDER_DOSER_HOSTNAME" 'LISTEN_S=12 python3 -'

On a machine that is on the printers' LAN itself, set PRINTER_IP, PRINTER_SERIAL and
PRINTER_ACCESS_CODE and run it directly.

Nozzles on the H2D: in ``device.nozzle.info``, id 1 is the left nozzle and id 0 the right
one (Bambu Studio's ``DEPUTY_EXTRUDER_ID`` and ``MAIN_EXTRUDER_ID``; see
src/slic3r/GUI/DeviceTab/wgtDeviceNozzleSelect.cpp). Type codes seen so far: ``HS01``
hardened steel, standard flow; ``HU01`` hardened steel, TPU high flow.
"""
import json
import os
import socket
import ssl
import struct
import time

LISTEN_S = float(os.environ.get("LISTEN_S", "12"))

try:
    CFG  # noqa: F821  (set by a preceding line when the program arrives over stdin)
except NameError:
    CFG = {
        "ip": os.environ["PRINTER_IP"],
        "serial": os.environ["PRINTER_SERIAL"],
        "code": os.environ["PRINTER_ACCESS_CODE"],
    }


def enc_len(n):
    out = bytearray()
    while True:
        b = n % 128
        n //= 128
        if n:
            b |= 0x80
        out.append(b)
        if not n:
            return bytes(out)


def mqtt_str(x):
    b = x.encode() if isinstance(x, str) else x
    return struct.pack("!H", len(b)) + b


def packet(first, body):
    return bytes([first]) + enc_len(len(body)) + body


def recv_exact(sock, n):
    buf = b""
    while len(buf) < n:
        chunk = sock.recv(n - len(buf))
        if not chunk:
            raise ConnectionError("closed")
        buf += chunk
    return buf


def read_packet(sock):
    first = recv_exact(sock, 1)[0]
    mult, n = 1, 0
    while True:
        b = recv_exact(sock, 1)[0]
        n += (b & 0x7F) * mult
        if not b & 0x80:
            break
        mult *= 128
    return first, recv_exact(sock, n) if n else b""


def merge(dst, src):
    for k, v in src.items():
        if isinstance(v, dict) and isinstance(dst.get(k), dict):
            merge(dst[k], v)
        else:
            dst[k] = v


def main():
    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE  # the printer's LAN certificate is self-signed
    sock = ctx.wrap_socket(socket.create_connection((CFG["ip"], 8883), timeout=10))
    cid = "ro-status-%d" % (time.time() * 1000 % 1e9)
    body = (mqtt_str("MQTT") + bytes([4, 0xC2]) + struct.pack("!H", 60)
            + mqtt_str(cid) + mqtt_str("bblp") + mqtt_str(CFG["code"]))
    sock.sendall(packet(0x10, body))
    first, b = read_packet(sock)
    if first >> 4 != 2 or len(b) < 2 or b[1] != 0:
        print(json.dumps({"error": "connack", "code": b[1] if len(b) > 1 else None}))
        return
    report_t = "device/%s/report" % CFG["serial"]
    request_t = "device/%s/request" % CFG["serial"]
    sock.sendall(packet(0x82, struct.pack("!H", 1) + mqtt_str(report_t) + b"\x00"))
    state, n_msgs, sent_pushall = {}, 0, False
    t0 = time.time()
    sock.settimeout(1.0)
    while time.time() - t0 < LISTEN_S:
        if not sent_pushall and time.time() - t0 > 1.0:
            payload = json.dumps({"pushing": {"sequence_id": "0", "command": "pushall"}}).encode()
            sock.sendall(packet(0x30, mqtt_str(request_t) + payload))
            sent_pushall = True
        try:
            first, b = read_packet(sock)
        except socket.timeout:
            continue
        if first >> 4 == 3:
            tl = struct.unpack("!H", b[:2])[0]
            off = 2 + tl + (2 if (first >> 1) & 3 else 0)
            try:
                msg = json.loads(b[off:].decode("utf-8", "replace"))
            except ValueError:
                continue
            n_msgs += 1
            merge(state, msg)
    try:
        sock.sendall(b"\xe0\x00")  # DISCONNECT
        sock.close()
    except OSError:
        pass
    p = state.get("print", {})
    keep = [
        "gcode_state", "subtask_name", "gcode_file", "mc_percent", "layer_num", "total_layer_num",
        "mc_remaining_time", "print_error", "mc_print_stage", "stg_cur", "print_type",
        "nozzle_diameter", "nozzle_type", "bed_temper", "bed_target_temper", "nozzle_temper",
        "nozzle_target_temper", "sdcard", "hms", "fail_reason", "spd_lvl", "wifi_signal",
    ]
    out = {k: p[k] for k in keep if k in p}
    ipcam = p.get("ipcam", {})
    out["ipcam"] = {k: ipcam[k] for k in ("timelapse", "resolution", "ipcam_record") if k in ipcam}
    dev = p.get("device", {})
    if isinstance(dev, dict):
        out["device.nozzle"] = dev.get("nozzle")
        ext = dev.get("extruder", {})
        if isinstance(ext, dict):
            # "temp" packs target << 16 | current, in degrees C
            out["device.extruder.temps_c"] = [
                {"id": e.get("id"), "current": e.get("temp", 0) & 0xFFFF, "target": e.get("temp", 0) >> 16}
                for e in ext.get("info", []) if isinstance(e, dict)
            ]
    out["_messages"] = n_msgs
    out["_read_utc"] = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    text = json.dumps(out, indent=1, default=str)
    for secret in (CFG["ip"], CFG["serial"], CFG["code"]):
        text = text.replace(secret, "<redacted>")
    print(text)


main()
