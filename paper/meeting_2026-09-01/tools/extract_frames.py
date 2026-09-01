import subprocess, os, csv
from PIL import Image

VID = "/tmp/meeting/video/meeting.mp4"
OUT = "/tmp/meeting/shots"
os.makedirs(OUT, exist_ok=True)

def hhmmss(t):
    return "%02d-%02d-%02d" % (t//3600, (t%3600)//60, t%60)

rows = []
with open("/tmp/meeting/work/shots.tsv") as f:
    for line in f:
        parts = line.rstrip("\n").split("\t")
        if len(parts) < 3: continue
        num, t, slug = parts[0], int(parts[1]), parts[2]
        burst = parts[3] if len(parts) > 3 else ""
        rows.append((num, t, slug, burst))

jobs = []
for num, t, slug, burst in rows:
    if burst.strip():
        times = [int(x) for x in burst.split(",")]
        for i, bt in enumerate(times):
            jobs.append((f"{num}{chr(97+i)}", bt, slug))
    else:
        jobs.append((num, t, slug))

print("total frames:", len(jobs))
for name, t, slug in jobs:
    dest = f"{OUT}/{name}_{hhmmss(t)}_{slug}.png"
    if os.path.exists(dest): continue
    tmp = "/tmp/meeting/_f.png"
    subprocess.run(["ffmpeg","-v","error","-ss",str(t),"-i",VID,"-frames:v","1","-y",tmp], check=True)
    im = Image.open(tmp).crop((0,0,1390,1010))
    im.save(dest, optimize=True)
print("done")
