# Physics-based simulations for the doser and the powder tests

Requested on PR #184 ([comment](https://github.com/vertical-cloud-lab/powder-doser/pull/184#issuecomment-6537306678)):
find which physics-based simulations could be run for what the optimization paper (#179, PR #184) and the
28 Oct meeting discuss, using a series of Edison queries and full texts read through the doser Pi, then
attempt to run **all** of the methods found.

| Folder / file | What |
|---|---|
| [`LITERATURE.md`](LITERATURE.md) | The 21 method families found, where each is used, which doser question it could answer, and the open-source codes |
| [`edison/`](edison/) | The nine Edison queries ([`run_queries.py`](edison/run_queries.py)); the API key was refused with 403 on every login ([`STATUS.md`](edison/STATUS.md)) |
| [`fulltext/`](fulltext/) | Headed-Chrome reader that opens open-access papers through the Pi with pointer moves and clicks ([`fetch_fulltexts.py`](fulltext/fetch_fulltexts.py)); [`manifest.json`](fulltext/manifest.json) pins what was read (texts not committed) |
| [`runs/<id>/`](runs/) | One folder per simulation attempt: inputs and scripts to rerun, `README.md`, `result.json`, figure, and an animation where the run evolves in time |
| [`results.md`](results.md), [`results.json`](results.json) | All runs in one table, built by [`collect_results.py`](collect_results.py) |

<!-- RESULTS -->

## Rerunning

Each `runs/<id>/README.md` has its own commands. The codes come from:

- Debian packages: `liggghts` (LIGGGHTS-PUBLIC 3.8), `lammps`, `yade`, `openmpi-bin`;
- pip: `taichi`, `pysph`, `grainlearning`, `scikit-learn`, `emcee`, `torch` (CPU), `numba`, `imageio-ffmpeg`;
- conda: `pychrono`, `mfix` where a run used them;
- source: MercuryDPM.

Every run was sized for a shared 4-core GitHub runner with no GPU, single-threaded, mostly under 10 minutes. They
are smoke tests and small studies, not calibrated predictions. The numbers that matter for the paper still need
same-lot measurements (PR #184, OUTLINE §4A).
