"""Pi side: download the livestream HLS segment covering a UTC time (rate-capped). Usage: camat.py <m3u8_url_file> <ISO-UTC> <out.ts>"""
import datetime as dt, subprocess, sys
url = open(sys.argv[1]).read().strip()
want = dt.datetime.fromisoformat(sys.argv[2].replace("Z", "+00:00"))
pl = subprocess.run(["curl", "-s", "--limit-rate", "300k", url], capture_output=True, text=True, timeout=60).stdout.splitlines()
t = None; dur = None
for line in pl:
    if line.startswith("#EXT-X-PROGRAM-DATE-TIME:"):
        t = dt.datetime.fromisoformat(line.split(":", 1)[1].replace("Z", "+00:00"))
    elif line.startswith("#EXTINF:"):
        dur = float(line.split(":", 1)[1].split(",")[0])
    elif line and not line.startswith("#"):
        if t is not None and dur is not None and t <= want < t + dt.timedelta(seconds=dur):
            subprocess.run(["curl", "-s", "--limit-rate", "300k", line, "-o", sys.argv[3]], timeout=60, check=True)
            print("segment start", t.isoformat(), "dur", dur); sys.exit(0)
        if t is not None and dur is not None:
            t = t + dt.timedelta(seconds=dur)
print("not in window"); sys.exit(1)
