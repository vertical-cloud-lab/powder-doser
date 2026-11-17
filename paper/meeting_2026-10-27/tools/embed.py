"""Speaker embeddings (SpeechBrain ECAPA) on 1.5 s windows inside VAD speech regions.

Usage: python -I embed.py <wav16k> <vad_regions.json> <out.npz>
"""
import json, sys
import numpy as np, soundfile as sf, torch
from huggingface_hub import snapshot_download
from speechbrain.inference.speaker import EncoderClassifier

wav, vad_json, out = sys.argv[1:4]
torch.set_num_threads(2)
src = snapshot_download("speechbrain/spkrec-ecapa-voxceleb", local_dir="/tmp/ws_models/ecapa")
enc = EncoderClassifier.from_hparams(source=src, savedir="/tmp/ws_models/ecapa_sb",
                                     run_opts={"device": "cpu"})
a, sr = sf.read(wav, dtype="float32")
assert sr == 16000
regions = json.load(open(vad_json))
WIN, HOP = 1.5, 0.75
starts = []
for s, e in regions:
    if e - s < 0.6:
        continue
    if e - s <= WIN:
        starts.append((s, e))
        continue
    t = s
    while t + WIN <= e + 1e-6:
        starts.append((t, t + WIN)); t += HOP
    if starts[-1][1] < e - 0.3:
        starts.append((e - WIN, e))
embs, rms = [], []
B = 32
for i in range(0, len(starts), B):
    chunk = starts[i:i+B]
    L = int(WIN * sr)
    batch = np.zeros((len(chunk), L), dtype="float32"); lens = []
    for j, (s, e) in enumerate(chunk):
        x = a[int(s*sr):int(e*sr)][:L]
        batch[j, :len(x)] = x; lens.append(len(x) / L)
        rms.append(float(np.sqrt(np.mean(x**2)) + 1e-9))
    with torch.no_grad():
        em = enc.encode_batch(torch.from_numpy(batch), torch.tensor(lens)).squeeze(1).numpy()
    embs.append(em)
E = np.concatenate(embs)
np.savez(out, emb=E, win=np.array(starts), rms=np.array(rms))
print("windows", len(starts), "emb", E.shape)
