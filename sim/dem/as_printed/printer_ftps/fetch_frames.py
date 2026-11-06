# Runs on the Pi after ftps_common.py and a file defining PATHS (remote paths) and RATE (bytes/s cap).
# Streams each file back as "FILE<TAB>path<TAB>size" + raw bytes, rate-capped; unframe.py splits it.
import time
f = open_ftps()
out = sys.stdout.buffer
for p in PATHS:
    try:
        size = f.size(p)
    except Exception as e:
        sys.stderr.write(f"SIZE ERR {p}: {e}\n"); continue
    out.write(f"FILE\t{p}\t{size}\n".encode()); out.flush()
    sent = [0]; t0 = time.time()
    def cb(chunk):
        room = size - sent[0]
        if room <= 0: return
        chunk = chunk[:room]
        out.write(chunk); sent[0] += len(chunk)
        lag = sent[0] / RATE - (time.time() - t0)
        if lag > 0: time.sleep(lag)
    f.retrbinary(f"RETR {p}", cb, blocksize=65536)
    if sent[0] < size:
        out.write(b"\0" * (size - sent[0]))
        sys.stderr.write(f"SHORT {p}: {sent[0]} of {size}\n")
    out.flush()
f.quit()
