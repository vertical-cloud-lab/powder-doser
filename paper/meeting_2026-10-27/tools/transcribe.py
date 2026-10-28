"""Transcribe one audio file with faster-whisper large-v3 (CPU, int8, batched).

Usage: python -I transcribe.py <audio> <out_json>
Writes segments with word timings; prints progress lines as segments arrive.
"""
import json, sys, time
from faster_whisper import WhisperModel, BatchedInferencePipeline

audio, out_json = sys.argv[1], sys.argv[2]
HOTWORDS = ("Sam, Sterling, Will, Luke, Carl, Gage, powder doser, auger, tap collar, "
            "solenoid, servo, AlSi10Mg, Digital Discovery, Zoo Design Studio, Zookeeper, "
            "Fusion 360, Onshape, CadQuery, OpenSCAD, CADSmith, Copilot, Claude, Edison, "
            "Zenodo, ChemRxiv, CRediT, GitHub, Utah AI Convergence")
t0 = time.time()
model = WhisperModel("large-v3", device="cpu", compute_type="int8", cpu_threads=4)
print(f"model loaded in {time.time()-t0:.0f}s", flush=True)
pipe = BatchedInferencePipeline(model=model)
segments, info = pipe.transcribe(
    audio, language="en", batch_size=8, beam_size=5, word_timestamps=True,
    vad_filter=True, hotwords=HOTWORDS)
print(f"duration {info.duration:.1f}s, after VAD {info.duration_after_vad:.1f}s", flush=True)
out = []
t1 = time.time()
for s in segments:
    out.append({"start": s.start, "end": s.end, "text": s.text,
                "avg_logprob": s.avg_logprob, "no_speech_prob": s.no_speech_prob,
                "words": [{"start": w.start, "end": w.end, "word": w.word,
                           "p": w.probability} for w in (s.words or [])]})
    print(f"[{s.start:7.1f}-{s.end:7.1f}] (+{time.time()-t1:5.0f}s) {s.text.strip()[:110]}", flush=True)
    with open(out_json, "w") as f:
        json.dump({"model": "large-v3", "compute_type": "int8", "batch_size": 8,
                   "beam_size": 5, "hotwords": HOTWORDS, "segments": out}, f, indent=1)
print(f"done: {len(out)} segments in {time.time()-t0:.0f}s total", flush=True)
