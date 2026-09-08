#!/usr/bin/env python3
"""Drive the issue-157 drift observation: alternating balance survey
segments (read-only A&D Q polls via the Pi/Pico) and livestream frames.

Runs entirely in the foreground of one Bash call; incremental artifacts
land in /tmp/drift157/ as each segment completes so a crash loses at most
one segment.
"""
import os, subprocess, sys, time, shutil

OUT = "/tmp/drift157"
TOOLS = "/tmp/pitools"
SEGMENTS = 5
SETTLE_S = 270

os.makedirs(OUT, exist_ok=True)
# keep the smoke artifacts with the rest
if os.path.exists("/tmp/drift_smoke.csv"):
    shutil.copy("/tmp/drift_smoke.csv", f"{OUT}/seg0_smoke.csv")
if os.path.exists("/tmp/frame_smoke.png"):
    shutil.copy("/tmp/frame_smoke.png", f"{OUT}/frame0_smoke.png")


def run(cmd, log_path, timeout):
    t0 = time.time()
    try:
        p = subprocess.run(cmd, cwd=TOOLS, timeout=timeout,
                           capture_output=True, text=True)
        out = (p.stdout or "") + (p.stderr or "")
        rc = p.returncode
    except subprocess.TimeoutExpired as e:
        out = ((e.stdout or b"").decode(errors="replace") if isinstance(e.stdout, bytes) else (e.stdout or "")) + "\nTIMEOUT"
        rc = -1
    with open(log_path, "w") as fh:
        fh.write(out)
    # never echo the hostname/username: print only whitelisted lines
    for line in out.splitlines():
        if line.startswith("[survey]") or line.startswith("[bench-frame]"):
            print("   " + line, flush=True)
    print(f"   -> rc={rc} in {time.time()-t0:.0f} s", flush=True)
    return rc


for i in range(1, SEGMENTS + 1):
    stamp = time.strftime("%H:%M:%S", time.gmtime())
    print(f"[driver] {stamp}Z frame {i}", flush=True)
    run([sys.executable, "scripts/bench_frame.py",
         "--out", f"{OUT}/frame{i}.png"],
        f"{OUT}/frame{i}.log", 240)
    stamp = time.strftime("%H:%M:%S", time.gmtime())
    print(f"[driver] {stamp}Z survey segment {i} ({SETTLE_S} s)", flush=True)
    t0 = time.time()
    run([sys.executable, "scripts/balance_environment_survey.py",
         "--settle", str(SETTLE_S), "--csv", f"{OUT}/seg{i}.csv"],
        f"{OUT}/seg{i}.survey.txt", SETTLE_S + 240)
    with open(f"{OUT}/seg{i}.t0", "w") as fh:
        fh.write(str(t0))

# one closing frame
print("[driver] closing frame", flush=True)
run([sys.executable, "scripts/bench_frame.py",
     "--out", f"{OUT}/frame_final.png"],
    f"{OUT}/frame_final.log", 240)
print("[driver] done", flush=True)
