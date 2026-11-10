import re, json, sys

path = "/tmp/meeting/inputs/teams/powder doser paper.vtt"
raw = open(path, encoding="utf-8-sig").read().replace("\r\n", "\n")

blocks = raw.split("\n\n")
cues = []
for b in blocks:
    lines = [l for l in b.split("\n") if l.strip()]
    if not lines: continue
    ts_line = None; ts_idx = None
    for i, l in enumerate(lines):
        if "-->" in l:
            ts_line = l; ts_idx = i; break
    if ts_line is None: continue
    start, end = [x.strip() for x in ts_line.split("-->")]
    text = " ".join(lines[ts_idx+1:]).strip()
    m = re.match(r"<v ([^>]+)>(.*?)</v>\s*$", text, re.S)
    if m:
        speaker, body = m.group(1), m.group(2)
    else:
        speaker, body = "UNKNOWN", re.sub(r"</?v[^>]*>", "", text)
    cues.append({"start": start, "end": end, "speaker": speaker.strip(), "text": body.strip()})

def to_s(t):
    h, m, s = t.split(":")
    return int(h)*3600 + int(m)*60 + float(s)

for c in cues:
    c["t"] = to_s(c["start"])
    c["te"] = to_s(c["end"])

speakers = {}
for c in cues:
    speakers[c["speaker"]] = speakers.get(c["speaker"], 0) + 1
print("SPEAKERS:", speakers, file=sys.stderr)
print("N cues:", len(cues), "last:", cues[-1]["end"], file=sys.stderr)

json.dump(cues, open("/tmp/meeting/work/cues.json","w"), indent=0)

# Merge into ~paragraph chunks for reading
out = []
cur = None
for c in cues:
    if cur and c["t"] - cur["te"] < 6 and (c["te"] - cur["t"]) < 45:
        cur["text"] += " " + c["text"]; cur["te"] = c["te"]
    else:
        if cur: out.append(cur)
        cur = dict(c)
if cur: out.append(cur)

def fmt(t):
    return "%02d:%02d:%02d" % (int(t)//3600, (int(t)%3600)//60, int(t)%60)

with open("/tmp/meeting/work/transcript_merged.txt","w") as f:
    for o in out:
        f.write("[%s-%s] %s\n" % (fmt(o["t"]), fmt(o["te"]), o["text"]))
print("merged chunks:", len(out), file=sys.stderr)
