"""Re-transcribe short windows with several models (no batching, no VAD).
python3 snips.py <audio16k.f32> <out_txt>"""
import sys, numpy as np, time
from faster_whisper import WhisperModel
audio = np.fromfile(sys.argv[1], dtype=np.float32)
out = open(sys.argv[2], 'w')
wins = [(3.0, 12.5), (183.0, 202.5), (229.0, 248.5), (633.0, 660.0), (110.0, 128.0), (268.0, 287.0)]
for name in ['large-v3', 'large-v2', 'medium.en']:
    t0 = time.time()
    m = WhisperModel(name, device='cpu', compute_type='int8', cpu_threads=4)
    for a, b in wins:
        seg = audio[int(a * 16000):int(b * 16000)]
        for temp in ([0.0] if name != 'large-v3' else [0.0, 0.4]):
            segs, _ = m.transcribe(seg, language='en', beam_size=5, temperature=temp, vad_filter=False,
                                   condition_on_previous_text=False)
            txt = ' '.join(s.text.strip() for s in segs)
            line = f'[{name} T={temp}] {a:.1f}-{b:.1f}: {txt}'
            print(line, flush=True); out.write(line + '\n'); out.flush()
    print(name, 'done in', round(time.time() - t0), 's', flush=True)
