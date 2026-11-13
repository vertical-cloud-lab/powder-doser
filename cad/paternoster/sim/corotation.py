"""How much does the powder turn with the rotating auger?  Ratio of the grains' mean angular speed about the auger
axis (in the tilted, non-spinning frame) to the auger's angular speed, over the forward-rotation phase.
1 = the bed turns with the tube (no conveying), 0 = the bed stays put while the flight turns through it.

  python corotation.py t0 t30 t60 t90
"""
import json, os, sys
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import auger_model as AM  # noqa: E402
import auger_geom as G  # noqa: E402

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "out", "auger")
res = {}
for tag in sys.argv[1:]:
    meta = json.load(open(os.path.join(OUT, f"run_{tag}.json")))
    dat = np.load(os.path.join(OUT, f"run_{tag}.npz"))
    fr, fq = dat["frames"], dat["fq"]
    O = np.array([0, 0, meta["H"]]); R = AM.frame_R(meta["tilt_deg"])
    t_rot = meta["revs"] / (meta["rpm"] / 60)
    loc = np.einsum("ij,tnj->tni", R.T, fr - O)            # tilted (non-spinning) auger frame, mm
    th = np.unwrap(np.arctan2(loc[..., 1], loc[..., 0]), axis=0)
    r = np.hypot(loc[..., 0], loc[..., 1])
    t = fq[:, 0]; spin = fq[:, 1]
    sel = (t > 0.2) & (t < t_rot)
    inside = np.all((loc[sel, :, 2] > meta["z_cut_mm"] + 2) & (r[sel] < G.BORE_R), axis=0)   # grains inside all along
    i0, i1 = np.where(sel)[0][[0, -1]]
    w_grain = (th[i1, inside] - th[i0, inside]) / (t[i1] - t[i0])
    w_aug = (spin[i1] - spin[i0]) / (t[i1] - t[i0])
    res[tag] = dict(tilt=meta["tilt_deg"], n_grains_inside=int(inside.sum()),
                    corotation_mean=float(np.mean(w_grain) / w_aug), corotation_median=float(np.median(w_grain) / w_aug))
    print(tag, res[tag])
json.dump(res, open(os.path.join(OUT, "corotation.json"), "w"), indent=1)
