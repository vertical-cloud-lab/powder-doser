"""Cluster ECAPA window embeddings into speakers; write a smoothed speaker timeline.

Usage: python -I cluster.py <emb.npz> <out_timeline.json> [k]
"""
import json, sys
import numpy as np
from sklearn.cluster import SpectralClustering, AgglomerativeClustering

d = np.load(sys.argv[1]); E, W, R = d["emb"], d["win"], d["rms"]
X = E / np.linalg.norm(E, axis=1, keepdims=True)
S = X @ X.T
# eigengap on a pruned affinity (keep top-p neighbours per row) to estimate k
A = (S + 1) / 2
p = max(10, int(0.05 * len(A)))
for i in range(len(A)):
    thr = np.sort(A[i])[-p]
    A[i, A[i] < thr] = 0
A = (A + A.T) / 2
L = np.diag(A.sum(1)) - A
Dm = np.diag(1 / np.sqrt(A.sum(1)))
ev = np.sort(np.linalg.eigvalsh(Dm @ L @ Dm))[:8]
gaps = np.diff(ev)
print("eigvals", np.round(ev, 3), "eigengap k =", int(np.argmax(gaps[:6])) + 1)
k = int(sys.argv[3]) if len(sys.argv) > 3 else max(2, int(np.argmax(gaps[:6])) + 1)
lab = SpectralClustering(n_clusters=k, affinity="precomputed", random_state=0).fit_predict(A)
agg = AgglomerativeClustering(n_clusters=k, metric="cosine", linkage="average").fit_predict(X)
from sklearn.metrics import adjusted_rand_score
print("k", k, "spectral vs agglomerative ARI", round(adjusted_rand_score(lab, agg), 3))
for c in range(k):
    m = lab == c
    print(f"cluster {c}: {m.sum()} windows, {m.sum()*0.75/60:.1f} min, median rms {np.median(R[m]):.4f}, "
          f"first at {W[m][0][0]:.0f}s")
# smooth labels by majority vote over +-2 windows in time order
order = np.argsort(W[:, 0]); lab_s = lab.copy()
for idx in range(len(order)):
    nb = order[max(0, idx-2): idx+3]
    vals, cnt = np.unique(lab[nb], return_counts=True)
    lab_s[order[idx]] = vals[np.argmax(cnt)]
centroids = np.stack([X[lab_s == c].mean(0) for c in range(k)])
conf = (X @ centroids.T)
tl = [{"start": float(W[i, 0]), "end": float(W[i, 1]), "spk": int(lab_s[i]),
       "margin": float(np.sort(conf[i])[-1] - np.sort(conf[i])[-2])} for i in order]
json.dump({"k": k, "timeline": tl}, open(sys.argv[2], "w"))
# print coarse timeline (30 s bins)
bins = {}
for t in tl:
    b = int(t["start"] // 60); bins.setdefault(b, []).append(t["spk"])
print(" ".join(f"{b}:{''.join(str(x) for x in np.bincount(v, minlength=k))}" for b, v in sorted(bins.items())))
