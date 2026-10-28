"""Assign each Whisper word a speaker from the diarization timeline and group into turns.

Usage: python -I merge.py <whisper.json> <timeline.json> <out_turns.json>
"""
import json, sys, bisect

wj, tj, out = sys.argv[1:4]
segs = json.load(open(wj))["segments"]
tl = json.load(open(tj))["timeline"]
centers = [(t["start"] + t["end"]) / 2 for t in tl]

def speaker_at(t):
    i = bisect.bisect_left(centers, t)
    cands = [j for j in (i - 1, i) if 0 <= j < len(tl)]
    j = min(cands, key=lambda j: abs(centers[j] - t))
    return tl[j]["spk"], abs(centers[j] - t)

words = []
for s in segs:
    for w in s["words"]:
        spk, dist = speaker_at((w["start"] + w["end"]) / 2)
        words.append({**w, "spk": spk if dist < 1.5 else None})
# fill unknowns from neighbours
for i, w in enumerate(words):
    if w["spk"] is None:
        w["spk"] = words[i - 1]["spk"] if i else next((x["spk"] for x in words if x["spk"] is not None), 0)
# hysteresis: a speaker change must last >= 3 words or 0.8 s, else absorb into surrounding turn
i = 0
while i < len(words):
    j = i
    while j < len(words) and words[j]["spk"] == words[i]["spk"]:
        j += 1
    run = words[i:j]
    if 0 < i and j < len(words) and (len(run) < 3 and run[-1]["end"] - run[0]["start"] < 0.8) \
            and words[i - 1]["spk"] == words[j]["spk"]:
        for w in run:
            w["spk"] = words[i - 1]["spk"]
    i = j
turns = []
for w in words:
    gap = w["start"] - turns[-1]["end"] if turns else 0
    if turns and turns[-1]["spk"] == w["spk"] and gap < 2.0:
        turns[-1]["text"] += w["word"]; turns[-1]["end"] = w["end"]
    else:
        turns.append({"start": w["start"], "end": w["end"], "spk": w["spk"], "text": w["word"]})
json.dump(turns, open(out, "w"), indent=1)
for t in turns:
    m, s = divmod(int(t["start"]), 60)
    print(f"{m:02d}:{s:02d} S{t['spk']}: {t['text'].strip()}")
