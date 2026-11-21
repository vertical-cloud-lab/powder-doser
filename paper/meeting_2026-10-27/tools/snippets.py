"""Re-decode short unclear snippets with large-v3 (sequential, beam 5, context prompt)."""
import json, sys, wave, numpy as np, time
from faster_whisper import WhisperModel
wav = sys.argv[1]
with wave.open(wav) as w:
    a = np.frombuffer(w.readframes(w.getnframes()), dtype='<i2').astype('float32') / 32768
SN = [(0, 30), (60, 72), (455, 480), (528, 556), (577, 603), (705, 735), (812, 826), (950, 965), (985, 1000),
      (1310, 1345), (1385, 1400), (1415, 1445), (1455, 1470), (1590, 1625), (1660, 1690), (1675, 1710),
      (1855, 1868), (2000, 2045)]
CTX = ("Sterling and Sam discuss the powder doser manuscript for Digital Discovery: the abstract, "
       "figures, Claude, Zoo Design Studio, CADSmith, Onshape, tap collar, auger, solenoid taps.")
m = WhisperModel("large-v3", device="cpu", compute_type="int8", cpu_threads=4)
for s, e in SN:
    t0 = time.time()
    segs, _ = m.transcribe(a[int(s*16000):int(e*16000)], language="en", beam_size=5, temperature=0.0,
                           initial_prompt=CTX, vad_filter=False, condition_on_previous_text=False)
    txt = " ".join(x.text.strip() for x in segs)
    print(f"[{s//60:02d}:{s%60:02d}-{e//60:02d}:{e%60:02d}] ({time.time()-t0:.0f}s) {txt}", flush=True)
