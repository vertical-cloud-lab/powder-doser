"""Read-only: ask a Bambu printer for its status report over LAN MQTT (through an SSH tunnel) and
print only the nozzle fields and state. Never prints the IP, serial or access code."""
import json, os, ssl, sys, time
import paho.mqtt.client as mqtt
port, serial_env, code_env, label = int(sys.argv[1]), sys.argv[2], sys.argv[3], sys.argv[4]
serial, code = os.environ[serial_env], os.environ[code_env]
got = {}
def on_connect(c, u, f, rc, props=None):
    c.subscribe(f"device/{serial}/report")
    c.publish(f"device/{serial}/request", json.dumps({"pushing": {"sequence_id": "0", "command": "pushall"}}))
def on_message(c, u, msg):
    try:
        d = json.loads(msg.payload).get("print", {})
    except Exception:
        return
    for k in ("nozzle_diameter", "nozzle_type", "gcode_state", "mc_percent", "subtask_name", "hms", "device"):
        if k in d:
            got[k] = d[k]
c = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
c.username_pw_set("bblp", code)
ctx = ssl.create_default_context(); ctx.check_hostname = False; ctx.verify_mode = ssl.CERT_NONE
c.tls_set_context(ctx)
c.on_connect = on_connect; c.on_message = on_message
try:
    c.connect("127.0.0.1", port, 30)
except Exception as e:
    print(label, "connect failed:", type(e).__name__); sys.exit(0)
c.loop_start(); t0 = time.time()
while time.time() - t0 < 25 and not ("nozzle_diameter" in got and "gcode_state" in got and "device" in got):
    time.sleep(0.5)
c.loop_stop(); c.disconnect()
out = {"printer": label, "utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())}
out["nozzle_diameter"] = got.get("nozzle_diameter"); out["nozzle_type"] = got.get("nozzle_type")
out["gcode_state"] = got.get("gcode_state"); out["hms_count"] = len(got.get("hms") or [])
dev = got.get("device") or {}
ext = (dev.get("extruder") or {}).get("info") if isinstance(dev, dict) else None
if ext:
    out["extruders"] = [{"id": e.get("id"), "nozzle_diameter": e.get("diameter") or e.get("nozzle_diameter"), "hnow": e.get("hnow"), "info": e.get("info")} for e in ext]
noz = (dev.get("nozzle") or {}).get("info") if isinstance(dev, dict) else None
if noz:
    out["nozzles"] = [{k: n.get(k) for k in ("id", "diameter", "type", "wear")} for n in noz]
print(json.dumps(out))
