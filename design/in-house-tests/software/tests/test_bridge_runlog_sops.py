"""The doser bridge (mock serial and TCP), the run logger, and every SOP
runner end to end in --sim (short settings)."""

import json
import os
import socket
import threading

import pytest

import doser_bridge as db
from bench import run as bench_run
from bench.runlog import RunLogger


# -- bridge -----------------------------------------------------------------------------

def test_link_commands_and_parsing():
    link = db.DoserLink(db.MockDoserSerial())
    assert link.command("z")["ok"]
    r = link.command("r 720")
    assert r["ok"] and r["lines"] == []
    w = link.command("w")
    assert w["ok"] and w["stable"] and w["grams"] > 0
    bad = link.command("p sideways")
    assert not bad["ok"] and "unknown preset" in bad["err"]
    assert not link.command("frob")["ok"]
    assert not link.command("r abc")["ok"]
    assert link.command("rpm 12")["ok"] and link.rpm == 12.0
    s = link.command("s")
    assert s["rpm"] == 12.0
    assert link.command("!")["ok"]
    assert link.default_timeout("r 3600") > 60


def test_link_timeout_and_partial_lines():
    class Silent:
        def write(self, data):
            return len(data)

        def readline(self):
            return b""
    r = db.DoserLink(Silent()).command("r 360", timeout=0.2)
    assert not r["ok"] and "timeout" in r["err"]

    class Chunky(db.MockDoserSerial):
        """Hands lines back in two pieces, as pyserial does on a read timeout."""
        def readline(self):
            if not self.out:
                return b""
            line = (self.out[0] + "\r\n").encode()
            if not hasattr(self, "_half"):
                self._half = True
                return line[:5]
            del self._half
            self.out.pop(0)
            return line[5:]
    link = db.DoserLink(Chunky())
    w = link.command("w")
    assert w["ok"] and w["status"] == "ST"


def test_abort_soft_resets():
    link = db.DoserLink(db.MockDoserSerial())
    r = link.abort(wait_s=1.0)
    assert r["ok"]


def test_bridge_tcp_loopback_only_and_weigh_stream():
    with pytest.raises(db.BridgeError):
        db.BridgeServer(db.Bridge(db.DoserLink(db.MockDoserSerial())), host="0.0.0.0", port=0)
    srv = db.BridgeServer(db.Bridge(db.DoserLink(db.MockDoserSerial())), host="127.0.0.1", port=0)
    th = threading.Thread(target=srv.serve_forever, daemon=True)
    th.start()
    try:
        port = srv.server_address[1]
        with socket.create_connection(("127.0.0.1", port), timeout=5) as s:
            f = s.makefile("rwb")

            def req(line):
                f.write((line + "\n").encode())
                f.flush()
                return json.loads(f.readline())
            assert req(".ping")["pong"]
            assert req('{"cmd": "r 360", "id": 9}')["id"] == 9
            assert req("w")["ok"]
            f.write(b".weigh 20 0.3\n")
            f.flush()
            msgs = []
            while True:
                m = json.loads(f.readline())
                msgs.append(m)
                if "ok" in m:
                    break
            assert msgs[-1]["ok"] and msgs[-1]["n"] >= 3
            assert all(m["ev"] == "w" for m in msgs[:-1])
            assert not req(".nope")["ok"]
            assert not req("{bad json")["ok"]
    finally:
        srv.shutdown()
        srv.server_close()


# -- run logger -------------------------------------------------------------------------------

def test_run_logger(tmp_path):
    log = RunLogger(str(tmp_path), "heap", "NaCl 01/x", "tester", {"pours": 3}, sim=True, note="n")
    log.env("start", 22.1, 40.2)
    s = log.stream("balance", ["t", "g"])
    s.write([1.0, 0.5])
    s.write({"t": 2.0, "g": 0.6})
    log.event("hello", x=1)
    import numpy as np
    log.image("a", np.zeros((10, 10)))
    out = log.finish({"x": np.float64(1.5)}, [{"check": "c", "pass": True, "value": 1, "limit": 2}])
    assert out["all_pass"]
    man = json.load(open(os.path.join(log.dir, "manifest.json")))
    assert man["jar"] == "NaCl 01/x" and man["operator"] == "tester" and man["env"]["start"]["rh"] == 40.2
    assert "git" not in man and "commit" in man["software"]
    assert sorted(man["files"]) == sorted(["balance.csv", "events.jsonl", "images/a.png", "manifest.json",
                                           "results.json"])
    assert os.path.basename(log.dir).endswith("_heap_NaCl_01_x")


# -- SOP runners in --sim -------------------------------------------------------------------------

def _run(tmp_path, *argv):
    rc = bench_run.main(list(argv) + ["--sim", "--out", str(tmp_path)])
    d = sorted(p for p in tmp_path.iterdir() if p.is_dir())[-1]
    res = json.load(open(d / "results.json"))
    return rc, res


def test_sim_heap(tmp_path):
    rc, res = _run(tmp_path, "heap", "--jar", "NaCl-01", "--pours", "2")
    r = res["results"]
    assert r["flank_deg_mean"] == pytest.approx(r["sim_truth_aor_deg"], abs=1.5)
    assert all(p["stopped"] for p in r["pours"])


def test_sim_density(tmp_path):
    rc, res = _run(tmp_path, "density", "--jar", "NaCl-01", "--batches", "0,2,10,50,200,1250")
    r = res["results"]
    assert rc == 0 and res["all_pass"]
    assert r["rho_bulk"] == pytest.approx(r["sim_truth"]["rho_bulk"], rel=0.01)
    assert r["kawakita_a"] == pytest.approx(r["sim_truth"]["kawakita_a"], abs=0.01)


def test_sim_watercal_and_psdcal(tmp_path):
    rc, res = _run(tmp_path, "watercal", "--jar", "cyl-A", "--steps", "4")
    assert rc == 0 and res["results"]["calibration"]["bore_mm"] == pytest.approx(13.0, abs=0.05)
    rc, res = _run(tmp_path, "psdcal", "--jar", "NaCl-01", "--spacing-um", "100")
    assert rc == 0
    assert res["results"]["um_per_px"] == pytest.approx(res["results"]["sim_truth_um_per_px"], rel=0.005)
    rc, res = _run(tmp_path, "psdcal", "--jar", "NaCl-01", "--spacing-um", "10")
    assert rc == 1                     # 10 um lines are under 1 px apart at 12.9 um/px: refused


def test_sim_plate(tmp_path):
    rc, res = _run(tmp_path, "plate", "--jar", "NaCl-01", "--lids", "0,15", "--repeats", "1", "--fast-to", "20")
    r = res["results"]
    for t in r["trials"]:
        assert t["theta_cam_deg"] == pytest.approx(t["sim_theta_s"], abs=0.2)


def test_sim_psd(tmp_path):
    rc, res = _run(tmp_path, "psd", "--jar", "NaCl-01", "--fields", "3", "--min-grains", "300", "--boot", "100")
    r = res["results"]
    assert r["d50_n"] == pytest.approx(r["sim_truth"]["d50_n_um"], rel=0.05)


def test_sim_orifice(tmp_path):
    rc, res = _run(tmp_path, "orifice", "--jar", "NaCl-01", "--discs", "6,3,2,1.5,1,0.8", "--rho-b", "1250",
                   "--d50-um", "425")
    r = res["results"]
    assert r["dc_bracket_mm"] == [1.0, 1.5]
    assert r["dc_tapped_bracket_mm"] == [0.8, 1.0]
    assert r["beverloo"]["C"] == pytest.approx(0.58, rel=0.08)


def test_sim_humidity(tmp_path):
    rc, res = _run(tmp_path, "humidity", "--jar", "NaCl-01", "--box", "NaCl")
    r = res["results"]
    assert rc == 0
    assert r["fit"]["u_eq"] == pytest.approx(r["sim_truth"]["u_eq"], rel=0.03)


def test_sim_drum(tmp_path):
    rc, res = _run(tmp_path, "drum", "--jar", "NaCl-01", "--rpms", "1,10", "--seconds", "6", "--fps", "5",
                   "--save-every", "30")
    r = res["results"]
    assert r["speeds"][1]["dynamic_deg"] == pytest.approx(r["sim_truth"]["dynamic_at_rpm"]["10.0"], abs=0.5)
    assert r["fill_fraction"] == pytest.approx(0.40, abs=0.03)


def test_sim_ucs(tmp_path):
    rc, res = _run(tmp_path, "ucs", "--jar", "flour-01", "--sigma1-kpa", "0.5,2", "--max-travel", "4")
    r = res["results"]
    for s, truth in zip(r["samples"], r["sim_truth"]["sigma_c_pa"]):
        assert s["sigma_c_pa"] == pytest.approx(truth, rel=0.05)


def test_sim_spread(tmp_path):
    rc, res = _run(tmp_path, "spread", "--jar", "NaCl-01", "--speeds", "30", "--layers", "2", "--rho-true", "2165")
    r = res["results"]
    for row in r["layers"]:
        assert row["coverage"] == pytest.approx(row["sim_truth"]["coverage"], abs=0.015)


def test_sim_faraday(tmp_path):
    rc, res = _run(tmp_path, "faraday", "--jar", "NaCl-01", "--repeats", "3")
    r = res["results"]
    assert rc == 0
    assert r["q_per_m_mean_c_kg"] == pytest.approx(r["sim_truth_q_per_m_c_kg"], rel=0.15)


def test_list_and_status(capsys):
    assert bench_run.main(["list"]) == 0
    assert "faraday" in capsys.readouterr().out
    assert bench_run.main(["status", "--sim"]) == 0
    out = json.loads(capsys.readouterr().out)
    assert out["balance"]["ok"] and "0x6A" in out["i2c"]
