# GPU DEM engines on the CPU-only runner (DEM-Engine, Isaac Sim / MATTERIX, Warp / Newton)

Test date: 2026-10-10. The runner was a GitHub Actions Ubuntu 24.04 host with an AMD EPYC 7763 (2 cores / 4 vCPUs) and 15 GB RAM. It has no GPU and no NVIDIA driver; Mesa 25.2.8 lavapipe is installed.

Every run used at most 2 threads. A 2-rank LIGGGHTS job and the Chrono CPU test (2 threads) shared the same 4 vCPUs for most of the time, so all timings below are pessimistic.

| Engine | Installs? | Runs on CPU? | CPU route for powders |
|---|---|---|---|
| DEM-Engine (DEME) 3.0.18 | yes (`pip`, 2 s) | **no**: needs the CUDA driver at import and at solver construction | none (CUDA only; DEME 2.4.2 adds AMD HIP, which is still a GPU) |
| Isaac Sim 6.1.0 (pip) | yes (26 GB, 2.5 min) | **partly**: headless app starts in 30–60 s with about 600 logged errors; CPU PhysX rigid bodies work | rigid spheres only; PBD particles are GPU-only |
| MATTERIX (main `687e2ce`) | yes, with Isaac Lab 3.0.0b2.post1 | env runs on CPU after 2 small patches; **powder does not simulate** | none: its powders are PhysX PBD particles |
| NVIDIA Warp 1.18 | yes (`pip`) | **yes** | toy DEM, 0.73 M particle-steps/s on 1 thread |
| Newton 1.6.1 | yes (`pip`) | **yes** | implicit-MPM granular continuum, 30 k particles at 3 frames/s |

## 1. DEM-Engine (projectchrono/DEM-Engine)

**What I tried.** `pip install "DEME[cuda12]==3.0.18"`. This is the PyPI wheel plus the NVIDIA CUDA 12.8 runtime, NVRTC and CCCL wheels; no toolkit is needed.

**Plain `import deme` fails:**
```
ImportError: libcuda.so.1: cannot open shared object file: No such file or directory
```
The extension links the CUDA driver library directly.

**With NVIDIA's driver stub on `LD_LIBRARY_PATH`** (from conda-forge `cuda-driver-dev=12.8`, `lib/stubs/libcuda.so` linked as `libcuda.so.1`):
- The import succeeds.
- The documented check `deme.DEMSolver([0])` fails with `RuntimeError: GPU Error: CUDA driver is a stub library`.
- The upstream demo `python/demos/single_sphere_collide.py --smoke-test` fails with:
```
[ERROR]   constructWorkers: GPU Error: CUDA driver is a stub library ... (/project/src/DEM/APIPublic.cpp:62)
```

**No CPU backend.** The repo's `docs/installation.rst` says "DEME requires: … an NVIDIA GPU". `docs/deme3-new-features.rst` says "DEME 3 currently requires NVIDIA GPUs and CUDA; it does not yet provide a non-NVIDIA GPU backend". DEME 2.4.2 had an AMD HIP/ROCm source build, which still needs a GPU.

**How DEME runs its kernels.** The kernels ship as `.cu` sources (`share/DEME/kernel/*.cu`) and are JIT-compiled at run time through jitify. The extension imports `nvrtcCompileProgram`, `nvrtcGetPTX`, `cuLinkCreate_v2`, `cuModuleLoadDataEx` and `cuLaunchKernel`.

**CUDA-on-CPU options (assessed, not attempted):**
- **NVIDIA:** no CPU emulation since `nvcc -deviceemu` was removed (CUDA 3.x).
- **ZLUDA:** targets AMD/Intel GPUs, not CPUs.
- **HIP-CPU:** needs a HIP port and has no hipRTC/module loading. DEME 3 has no HIP path at all.
- **gpgpu-sim:** simulates PTX at cycle level (orders of magnitude slower). It targets older toolkits and the runtime API, not CUDA 12.8 NVRTC plus driver-API linking.
- **chipStar + PoCL (CPU OpenCL):** the only plausible route, but it means porting jitify/NVRTC/CUB to hipRTC/hipCUB. That is a porting project, not an install.

**Verdict:** DEME cannot run on this runner.

## 2. Isaac Sim 6.1 (pip) on CPU PhysX

**Install:**
```
uv venv --python 3.12 isaac_venv
uv pip install "isaacsim[all,extscache]==6.1.0.0" --extra-index-url https://pypi.nvidia.com --index-strategy unsafe-best-match
```
Python 3.12 is the required version. The install pulled 171 packages (including torch 2.11) and took about 26 GB on disk.

**Launch:** `SimulationApp({"headless": True, "renderer": "MinimalRendering"})` with `OMNI_KIT_ACCEPT_EULA=YES`. The app comes up in 30–60 s, but the renderer has no device:
```
[Warning] [carb.cudainterop.plugin] Could not load CUDA driver library. CUDA may be unavailable. Error: libcuda.so.1: cannot open shared object file
[Error] [omni.rtx] No device could be created. ... Your GPUs do not support RayTracing ... or hardware is excluded due to performance.
[Error] [omni.gpu_foundation_factory.plugin] Failed to create any GPU devices, including an attempt with compatibility mode.
[Error] [omni.kit.renderer.plugin] GPU Foundation is not initialized!
```
- Forcing lavapipe (`VK_DRIVER_FILES=.../lvp_icd.json`) changes nothing: the RTX GPU table stays empty.
- 16 native plugins fail to load because they link `libcuda.so.1`, either directly or through `librtx.hydra.so`. They include RTX hydra/scenedb, the camera, lidar and replicator sensors, video encoding, and `isaacsim.core.experimental.primdata`.
- As a result, the `isaacsim.core.experimental` prim API is also missing. Scenes must be built with raw USD plus `omni.physx`.
- There is no rendering, no cameras and no sensors.

**CPU PhysX rigid funnel test** ([`isaac_cpu_probe.py`](isaac_cpu_probe.py)):
- Setup: d = 5 mm glass-density spheres in an 80 mm funnel (48 static box staves), TGS solver, dt = 1/600 s, 2 PhysX threads.

| Case | Spheres | Outlet | Steps/s | Outcome |
|---|---|---|---|---|
| Jammed | 400 | 12 mm (D/d = 2.4) | 361 | arched with 3 discharged, 397 held (median z 31 mm) |
| Flowing | 852 | 20 mm (D/d = 4) | 28 | 773 discharged in 2 s |

- The same scene ran at anywhere from 260 to 550 steps/s across reruns, depending on the other session's load.
- PhysX uses rigid, solver-based contact (no Hertz–Mindlin stiffness). That is why Δt can be about 80× larger than LIGGGHTS' 21 µs. It is a game-physics granular model, not a calibrated DEM.
- Two gotchas:
  - A triangle-mesh funnel whose normals faced outward let every sphere fall through it.
  - With a single `update_transformations` call at the end, spheres that had come to rest read back at their initial positions. The script therefore syncs poses every 50 steps.

**PBD particles (granular/powder) on CPU** use the same `particleUtils` calls that MATTERIX makes:
```
[Error] [omni.physx.plugin] Particles feature is only supported on GPU. Please enable GPU dynamics flag in Property/Scene of physics scene!
```
The 1000 particles stay frozen: mean z is 0.08540 m before and after 60 steps.

Requesting GPU the way MATTERIX does (`overwrite_gpu_setting(1)` and `enableGPUDynamics=True`) only adds:
```
[Warning] [omni.physx.plugin] GPU broadphase requires a CUDA context manager; falling back to ePABP.
```
Rigid bodies then run on CPU and the particles fail with the same error.

NVIDIA's documentation agrees:
- [PhysX SDK, ParticleSystem](https://nvidia-omniverse.github.io/PhysX/physx/latest/docs/ParticleSystem.html): "Simulating particle systems requires a CUDA capable GPU".
- [Omni Physics, particles](https://docs.omniverse.nvidia.com/kit/docs/omni_physics/latest/dev_guide/particles/particles.html): "CPU simulation of particles is not supported".
- [PhysX GPU rigid bodies](https://nvidia-omniverse.github.io/PhysX/physx/5.6.1/docs/GPURigidBodies.html): "Both the deformable body and particle system features are GPU-only".
- The [Isaac Sim 6.1 requirements](https://docs.isaacsim.omniverse.nvidia.com/latest/installation/requirements.html) set a GeForce RTX 4080 / 16 GB minimum and state that "GPUs without RT Cores (A100, H100) are not supported".

## 3. MATTERIX

**References:**
- Paper: arXiv:[2601.13232](https://arxiv.org/abs/2601.13232), also Nature Computational Science 6:67–82 (2026), doi:10.1038/s43588-025-00924-4.
- Code: [AccelerationConsortium/Matterix](https://github.com/AccelerationConsortium/Matterix), built on Isaac Lab 3.0.0b2.post1 and Isaac Sim 6.0.1.

**How it simulates powders.** Powders are **PhysX PBD particles**. The paper says "In Isaac Sim, powders and fluids are modeled using a position-based dynamics (PBD) solver".
- `particle_systems/powder_system.py` builds a `PhysxParticleSystem` with `ENABLE_FLUID = False  # powder/solid`.
- `powder_cfg.py` sets `particle_contact_offset = 0.0012  # ... their diameter` (0.5 mm for `FinePowderCfg`), cohesion 0.01 and friction 0.5.

**What it says about CPU vs GPU:**
- `envs/matterix_base_env.py` puts the Isaac Lab tensor pipeline on `cpu` for particle scenes.
- `envs/matterix_base_env_cfg.py` forces GPU PhysX with `overwrite_gpu_setting(1)`.

**How I installed and ran it:**
- I installed it into the Isaac Sim 6.1 venv: `isaaclab==3.0.0rc1` for the dependencies, then `--no-deps isaaclab==3.0.0b2.post1` (MATTERIX's pin), then `pip install -e source/matterix*`, plus `git submodule update --init source/matterix_assets/data` (LFS assets) and `MATTERIX_PATH`.
- rc1 alone fails with `ModuleNotFoundError: No module named 'isaaclab_tasks.manager_based'`.
- I ran its test task `Matterix-Test-Particle-systems-Franka-v1` with `--device cpu` using [`matterix_particles_cpu.py`](matterix_particles_cpu.py).

**Patches needed before the env would build:**
1. Isaac Lab's PhysX assets allocate pinned host memory, which fails with `RuntimeError: Failed to allocate 4 bytes on device 'cpu'`. The fix sends Warp's pinned CPU allocator to plain memory.
2. The MDL visual-material command `CreateAndBindMdlMaterialFromLibrary` is not registered without RTX, which leads to `RuntimeError: Accessed schema on invalid prim`. The fix replaces it with a bare `UsdShade.Material`.

**Result.** The env then steps on CPU at 15 env steps/s (Franka plus beakers). PhysX logs `Particles feature is only supported on GPU…` 8 times. The 9,024 powder and 387 fluid particles never move: mean z is 0.09979 m before and after 60 env steps.

**Verdict:** MATTERIX's powder model has no CPU path. Only the rigid robot and labware part runs.

## 4. CPU-capable relatives: Warp and Newton

**Warp DEM example.** `pip install warp-lang==1.18.0 newton==1.6.1 usd-core`, then:
```
python -m warp.examples.core.example_dem --device cpu --stage-path None --num-frames 3
```
- 65,536 grains, HashGrid neighbours, spring-dashpot plus friction.
- 4.6 s kernel compile, then 5.75 s per frame of 64 substeps. That is **0.73 M particle-steps/s on one thread**, about the same as LIGGGHTS' 0.75 M/core here.
- It is a toy contact model with no meshes or rotating walls.

**Newton implicit-MPM granular.**
```
python -m newton.examples mpm_granular --device cpu --viewer null --voxel-size 0.2 --benchmark
```
- 29,791 particles at **2.96 frames/s** (1/60 s frames, default sparse grid, one thread).
- Newton's test comment calls the sparse grid GPU-only, but it ran here.
- This is a continuum (Drucker–Prager-type) model, not DEM.

**Isaac Lab 3 backend.** Isaac Lab 3 can use Newton as a backend ([physics backends](https://isaac-sim.github.io/IsaacLab/release/3.0.0/source/concepts/physics_backends.html)). However, its MPM is "experimental" and the launcher defaults to `cuda:0`. MATTERIX's PBD powders would need rewriting to use Newton.

## Bottom line

- None of DEME, PhysX PBD or MATTERIX powders can run without an NVIDIA GPU.
- Isaac Sim runs headless on CPU only as a rigid-body PhysX engine, with no rendering and no sensors.
- The genuinely CPU-capable GPU-family options are Warp and Newton. Their granular models (toy DEM, MPM) are less complete than the LIGGGHTS twin.
- The GPU engines' value (about 1 M grains, fine powders) still needs a CUDA GPU, such as a cloud GPU runner.
