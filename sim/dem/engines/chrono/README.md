# Chrono on this CPU-only runner ("can't you try Chrono::GPU with CPU?")

Tried on 2026-10-10 on the GitHub Actions runner used for the LIGGGHTS twin: Ubuntu 24.04, AMD EPYC 7763
(2 physical cores / 4 vCPUs), 15 GB RAM, **no GPU**. There is no `/dev/nvidia*`, no `nvidia-smi` and no `libcuda.so.1`.

## Short answer

* **Chrono::GPU cannot run on a CPU.** In Chrono 10.0.0 it is called Chrono::DEM, and it is CUDA-only (on Chrono `main` it is
  CUDA or AMD HIP, still GPU-only). DEM-Engine is NVIDIA-only. Neither has a CPU backend.
* **PyChrono 10.0.0 has no Python bindings for Chrono::GPU/DEM or for Chrono::Multicore** in any conda build. So the
  OpenMP sibling, `ChSystemMulticoreSMC`, is not reachable from Python either. You would need a C++ build of
  Chrono::Multicore.
* **What does run is core `ChSystemSMC` with Chrono's OpenMP multicore collision detection.** It is the same Hertz
  smooth-contact DEM family on the CPU. It runs the full 28,905-grain rig section stably at LIGGGHTS' time step, but only
  after two fixes: a two-sided mesh and a broadphase grid set through ctypes.
  * It manages **0.16 M particle-steps/s on 2 threads (0.10 M per core-second)**. LIGGGHTS manages
    **0.89 M on one core** for the same case, so Chrono is **5.5× slower in wall-clock with twice the threads, and 8.6× slower per core**.
  * It also **silently ignores rolling friction**, which the LIGGGHTS twin relies on (EPSD2, μr = 0.3).
  * So it is not a better CPU engine for this twin. The GPU engines remain the route to whole-auger runs.

## 1. Installing PyChrono

| Command | What it installs | Python modules that import |
|---|---|---|
| `conda create -p /tmp/chrono_env -c conda-forge -c projectchrono python=3.12 pychrono=10.0.0 numpy` | `conda-forge::pychrono 10.0.0 py312h3a49c4c_0`. The conda-forge build wins channel priority. Install takes 24 s. It is built without Thrust, so it has no multicore collision system either. | `core`, `fea`, `robot` |
| `conda create -p /tmp/chrono_pc -c projectchrono -c conda-forge --override-channels "projectchrono::pychrono=10.0.0=py312h98ab86c_1197" python=3.12` | The official CUDA 12.8 build. It pulls `cuda-runtime` 12.8, cuBLAS, cuSPARSE, NPP and MKL. The env is 5.4 GB and installs in 65 s. | `core`, `fea`, `fsi`, `irrlicht`, `pardisomkl`, `parsers`, `postprocess`, `robot`, `sensor`, `vehicle`, `vsg3d` |

In both envs, `import pychrono.gpu` fails with `ModuleNotFoundError: No module named 'pychrono.gpu'`, and
`import pychrono.multicore` fails with `ModuleNotFoundError: No module named 'pychrono.multicore'`.

The CUDA build's `lib/` has no `libChrono_gpu.so`, `libChrono_dem.so` or `libChrono_multicore.so`. Its only CUDA modules
are FSI and Sensor. This is a property of PyChrono, not of the conda packaging: the SWIG interface files at tag 10.0.0
([`src/chrono_swig/chrono_python`](https://github.com/projectchrono/chrono/tree/10.0.0/src/chrono_swig/chrono_python)) are
Cascade, Core, Fea, Fsi, Irrlicht, PardisoMkl, Parsers, Postprocess, ROS, Robot, Sensor, Vehicle and Vsg. There is no
Gpu, Dem or Multicore module.

## 2. What the GPU engines do without a GPU (exact errors)

| Test | Result |
|---|---|
| CUDA runtime shipped with the build (`libcudart.so.12.8.90`), `cudaGetDeviceCount` and `cudaMallocManaged` via ctypes | error 35, `CUDA driver version is insufficient for CUDA runtime version` (`cudaErrorInsufficientDriver`; no driver is installed at all) |
| **Chrono::FSI-SPH**, the CUDA module that *is* in the build: `ChFsiSystemSPH(ChSystemSMC(), ChFsiFluidSystemSPH())`, then `.Initialize()` | Construction succeeds. `Initialize()` raises `RuntimeError: std::bad_alloc: cudaErrorInsufficientDriver: CUDA driver version is insufficient for CUDA runtime version`. This is the first device allocation, which is where a Chrono::GPU/DEM system would stop too. |
| **DEM-Engine**, `pip install "deme[cuda12]==3.0.18"` (44 MB wheel plus pip CUDA 12.8 libraries), then `import DEME` | `ImportError: libcuda.so.1: cannot open shared object file: No such file or directory`. It fails at import, before any solver exists. |

What the docs and sources say about a CPU backend (there is none):

* Chrono 10.0.0, [`src/chrono_dem/CMakeLists.txt`](https://github.com/projectchrono/chrono/blob/10.0.0/src/chrono_dem/CMakeLists.txt)
  (Chrono::GPU's successor): *"Chrono::DEM requires CUDA, but CUDA was not found; disabling Chrono::DEM"*.
* Chrono `main`, [`src/chrono_dem/CMakeLists.txt`](https://github.com/projectchrono/chrono/blob/main/src/chrono_dem/CMakeLists.txt):
  `REQUIRES CUDA_OR_HIP`. The module *"ships one set of .cu kernels that are compiled either as CUDA or as HIP"*; with
  neither available it is disabled.
* [Chrono::GPU install guide](https://api.projectchrono.org/module_gpu_installation.html): an NVIDIA GPU and CUDA are
  required, and macOS is unsupported for that reason.
* [DEM-Engine README](https://github.com/projectchrono/DEM-Engine): *"DEM-Engine (DEME) simulates granular materials
  using one or two NVIDIA GPUs"* and *"DEME 3 currently supports only NVIDIA GPUs"*. The Python wheel needs *"a
  CUDA 12.8-compatible NVIDIA driver"*.
* [Chrono::Multicore](https://api.chrono.projectchrono.org/module_multicore_installation.html) is the CPU path:
  *"shared-memory parallel computing"* with OpenMP and Thrust. It is C++ only in 10.0.0 (see section 1).

## 3. The CPU path that runs: core `ChSystemSMC` with the multicore collision system

[`chrono_cpu_auger.py`](chrono_cpu_auger.py) mirrors `run_case.py` for `results/cases/rig_t27p5_r60/config.json`:

* **Geometry.** The rig auger mesh from `geometry.auger_triangles` is converted mm → m and written to an OBJ. It is
  loaded as one triangle-mesh body and turned at 60 rpm about +z by a `ChLinkMotorRotationAngle` (the sign was checked:
  +0.0314 rad after 5 ms).
* **Grains.** The 28,905 grains come from `run_case.initial_packing`, with the same seed, PSD and `fill_x_max_mm`.
  They are Hertz spheres with E 0.2 MPa, ν 0.3, e 0.5, μpp 0.5 and μpw 0.4 (Chrono composes friction as the minimum).
  Tangential history is on (`MultiStep`).
* **Gravity** is tilted 27.5°, as in `run_case.py`.
* **Exit.** A fixed box plugs the exit during a short settle, then is moved away. Grains whose centres cross
  z = -0.3 mm are counted and parked. There is no feed insertion.
* **Time step:** dt = 2.06e-5 s, the same 0.2 × Rayleigh rule as LIGGGHTS.
* **Envelope.** The default contact envelope and margin are static values of 0.03 m and 0.01 m, so they are set to
  0.05 d and 0.02 d first.

Problems found, and the fixes in the script:

1. **Triangle contact is one-sided in the multicore collision system.** It only makes contact on the side the facet
   normal points to, and `geometry.py` does not orient its facets towards the powder.
   * With the mesh as written, grains fall straight through the funnel cone: in 0.02 s, 174 of 2000 grains ended up
     outside the cone and 667 "left", vmax 5.4 m/s.
   * Fix: duplicate every facet with reversed winding (`write_obj(..., two_sided=True)`, the default). This gives 0 leaks
     through the bore, cone, core or tip in every later run.
2. **The broadphase is a fixed 10 × 10 × 10 grid over the whole domain by default, and PyChrono does not wrap
   `ChCollisionSystemMulticore`.**
   * With 2000 grains the broadphase took 13.5 s of a 17.4 s run; collision as a whole took 94 %.
   * The script calls the exported C++ setter `SetBroadphaseGridDensity` through ctypes on the object behind
     `GetCollisionSystem()`. At 4 shapes per bin this is 1.45× faster (0.111 → 0.161 M particle-steps/s at 2000
     grains). A fixed 1 mm bin size gave nothing (0.109).
   * Coarsening the mesh to `n_theta` 24 gives a similar 1.47× speed-up, but at the cost of geometry.
3. **Bullet** (`--collision bullet`, with a static or GImpact mesh) blows up while settling against the plug.
   * vmax reached 1.4e4 m/s, more than 900 of 2000 grains ended outside the bore, and 0 contacts were reported.
   * It was also about 15× slower (0.009 M particle-steps/s).
4. **Rolling friction is ignored by core `ChSystemSMC`.**
   * A single 0.425 mm sphere rolling at 50 mm/s on a plane keeps exactly 50.00 mm/s after 0.05 s with
     `SetRollingFriction(0.3)`. With a constant-torque model it would have stopped.
   * The contact itself works: a sliding start relaxes to 35.74 mm/s, the textbook 5/7.
   * So this twin has no rolling resistance, whereas the LIGGGHTS twin uses EPSD2 with μr = 0.3.

### Numbers

2000 lowest grains, 0.01 s plugged settle plus 0.01 s at 60 rpm, 2 threads, wall-clock
([`small_tests_n2000.json`](small_tests_n2000.json)):

| Set-up | M particle-steps/s | Grains out | vmax (m/s) | Leaks |
|---|---|---|---|---|
| multicore collision, two-sided mesh (9,392 facets), default grid | 0.111 | 3 | 0.20 | 0 |
| same, 1 mm bins | 0.109 | 3 | 0.20 | 0 |
| same, 4 shapes/bin (used below) | **0.161** | 3 | 0.20 | 0 |
| two-sided mesh coarsened to `n_theta` 24 | 0.164 | 4 | 0.23 | 0 |
| one-sided mesh as `geometry.py` writes it | 0.161 | 667 | 5.4 | 174 outside the cone |
| Bullet collision (BVH or GImpact mesh) | 0.009 | ≥ 910 | 1.4e4 | > 900 outside the bore |

Full rig section ([`rig_t27p5_r60_full.json`](rig_t27p5_r60_full.json),
[`rig_t27p5_r60_full_outflow.csv`](rig_t27p5_r60_full_outflow.csv)):

| Quantity | Chrono, core `ChSystemSMC` + multicore collision | LIGGGHTS, same case |
|---|---|---|
| Grains | 28,905 (no feed) | 28,905 at start, 30,824 on average (feed on) |
| Time step | 2.06e-5 s | 2.06e-5 s |
| Simulated | 0.020 s plugged settle + 0.050 s at 60 rpm. Stopped at the 600 s wall limit. | 0.12 s settle + 1.5 rev + 0.6 s stopped |
| Wall-clock | 616 s for 3,395 steps | 3,739 s for 107,894 steps |
| **M particle-steps/s** | **0.160** on 2 threads (1.56 cores busy on average) | **0.888** on 1 core |
| M particle-steps per core-second | 0.103 | 0.888 |
| One revolution of the section (48.6 k steps) | about 2.4 h | about 26 min |
| Where the time goes | collision detection and contact creation 72 % (broadphase 35 %, narrowphase 16 %), integration 19 %, solver and setup 2 % | – |
| Contacts at the end | 77 k | – |
| Max grain speed | 0.41 m/s: stable, no blow-up | – |
| Grains out (z < -0.3 mm) after 0.01 / 0.02 / 0.03 / 0.04 / 0.05 s of rotation | 8 / 45 / 63 / 89 / 107 (9.7 mg at 0.05 s) | 2 after 0.02 s, 46 after 0.05 s, 72 after 0.10 s (6.6 mg) |
| Leaks through the mesh | none. 153 grains were outside the bore at the end, but they spilled over the open top rim (see below). | – |

**The grains outside the bore are spill-over, not leaks.**
[`rig_t27p5_r60_leakcheck.json`](rig_t27p5_r60_leakcheck.json) and
[`_outflow.csv`](rig_t27p5_r60_leakcheck_outflow.csv) are a rerun that tracks the census at every check. It was stopped
by its 360 s limit at t = 0.048 s.
* It reproduces the first run step for step (8 and 45 grains out at 0.030 and 0.040 s).
* It shows the bed swelling over the **open top rim** of the meshed section, on the -x (gravity) side:
  * The packing starts 0.43 mm below the rim.
  * 26 grains had crested the rim 0.014 s after the motor started, and 122 by 0.048 s.
* All 37 grains outside the bore at that point had first been above the rim. They sit at z 33.3–34.4 mm (rim at
  33.1 mm) and θ 155–180°.
* No grain crossed the bore, cone, core or tip mesh.
* The LIGGGHTS twin has the same open top. Whether it also spills there was not checked.
* That rerun ran at 0.184 M particle-steps/s wall-clock (0.108 per core-second).

Both outflows in the first 0.05 s are start-up transients, not dosing rates. Chrono's faster start is consistent with
its shorter, looser settle (0.02 s against 0.12 s) and its missing rolling resistance. The run is far too short to
compare mg/rev with LIGGGHTS (105 mg/rev) or with the rig (105 ± 11 mg/rev).

LIGGGHTS reference (`results/cases/rig_t27p5_r60`, serial, one core): 2.22 s simulated in 3,739 s, with on average
30,824 grains, which is **0.888 M particle-steps/s**. In its first 0.05 / 0.10 s of rotation, 46 / 72 grains
(4.3 / 6.6 mg) left.

The runner was shared with the main session's LIGGGHTS jobs (about 3.3 of the 4 vCPUs busy), so the table also gives
CPU time, summed over both threads, per particle-step.

## Reproduce

```bash
conda create -y -p /tmp/chrono_pc -c projectchrono -c conda-forge --override-channels \
    "projectchrono::pychrono=10.0.0=py312h98ab86c_1197" python=3.12
cd sim/dem
/tmp/chrono_pc/bin/python engines/chrono/chrono_cpu_auger.py results/cases/rig_t27p5_r60/config.json \
    --t-settle 0.02 --t-rot 0.28 --grid-density 4 --threads 2 --wall-limit 600 --check-every 0.002 \
    --out engines/chrono/rig_t27p5_r60_full
# small checks: --n-max 2000 --t-settle 0.01 --t-rot 0.01 [--one-sided | --collision bullet | --n-theta 24]
```

Use the projectchrono build. The slim conda-forge build is not built with Thrust, so asking it for the multicore
collision system prints `Chrono was not built with Thrust support. Multicore collision system not available.` and the
script then stops with `AttributeError: 'ChCollisionSystem' object has no attribute 'GetType'`.
