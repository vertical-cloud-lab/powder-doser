# Runner side: split the FILE-framed stream from fetch_frames.py into files under argv[1].
import os, sys
dest = sys.argv[1]; os.makedirs(dest, exist_ok=True)
inp = sys.stdin.buffer
while True:
    hdr = inp.readline()
    if not hdr: break
    tag, path, size = hdr.decode().rstrip("\n").split("\t")
    size = int(size); name = os.path.basename(path)
    with open(os.path.join(dest, name), "wb") as fh:
        left = size
        while left:
            b = inp.read(min(left, 1 << 20))
            if not b: raise SystemExit(f"truncated {name}")
            fh.write(b); left -= len(b)
    print(f"{name}\t{size}")
