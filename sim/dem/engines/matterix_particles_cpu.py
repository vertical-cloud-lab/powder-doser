"""Run MATTERIX's particle test task (PhysX PBD powder + fluid) on a GPU-less host and check whether particles move.

Used for sim/dem/engines/gpu_engines_on_cpu.md. Setup on top of an isaacsim[all,extscache]==6.1.0.0 venv:

    git clone --depth 1 https://github.com/AccelerationConsortium/Matterix.git && cd Matterix
    git submodule update --init --depth 1 source/matterix_assets/data      # USD assets (git lfs)
    pip install isaaclab==3.0.0rc1 --extra-index-url https://pypi.nvidia.com    # pulls Isaac Lab deps
    pip install --no-deps isaaclab==3.0.0b2.post1 --extra-index-url https://pypi.nvidia.com  # MATTERIX's pin
    pip install -e source/matterix -e source/matterix_assets -e source/matterix_sm -e source/matterix_tasks
    MATTERIX_PATH=$PWD OMNI_KIT_ACCEPT_EULA=YES python matterix_particles_cpu.py --device cpu --steps 60 \
        --kit_args "--/plugins/carb.tasking.plugin/threadCount=2 --/physics/numThreads=2"
"""
import argparse
import time

from isaaclab.app import AppLauncher

p = argparse.ArgumentParser()
p.add_argument("--task", default="Matterix-Test-Particle-systems-Franka-v1")
p.add_argument("--steps", type=int, default=30)
AppLauncher.add_app_launcher_args(p)
a = p.parse_args()
T0 = time.time()
app = AppLauncher(a).app
print(f"[MARK {time.time()-T0:.1f}s] app launched", flush=True)

import warp as wp  # noqa: E402

# Workaround 1: Isaac Lab's PhysX assets allocate pinned host buffers (cudaHostAlloc), which fail without a CUDA
# driver ("Failed to allocate 4 bytes on device 'cpu'"). Route pinned CPU allocations to plain host memory.
_cpu = wp.get_device("cpu")
_cpu.pinned_allocator = _cpu.default_allocator

import gymnasium as gym  # noqa: E402
import isaaclab_tasks  # noqa: E402,F401
import matterix_tasks  # noqa: E402,F401
import omni.usd  # noqa: E402
import torch  # noqa: E402
from isaaclab_tasks.utils import parse_env_cfg  # noqa: E402
from pxr import UsdGeom  # noqa: E402

# Workaround 2: the MDL material command (omni.kit.material.library, RTX stack) is not registered without a GPU,
# so MATTERIX's visual-material helper crashes. Use a bare UsdShade.Material (physics material still applied to it).
from matterix.particle_systems import particle_system as _mps  # noqa: E402
from pxr import Sdf, UsdShade  # noqa: E402


def _plain_material(self, target_path, color_rgb=None, stage=None):
    UsdShade.Material.Define(stage or self.stage, target_path)
    UsdShade.Shader.Define(stage or self.stage, target_path + _mps.SHADER_CHILD_NAME)  # dummy shader for color inputs
    return Sdf.Path(target_path)


for _name in dir(_mps):
    _cls = getattr(_mps, _name)
    if isinstance(_cls, type) and hasattr(_cls, "create_pbd_material"):
        _cls.create_pbd_material = _plain_material
        _cls.create_transparent_pbd_material = _plain_material

cfg = parse_env_cfg(a.task, device=a.device, num_envs=1)
env = gym.make(a.task, cfg=cfg)
print(f"[MARK {time.time()-T0:.1f}s] env created; env device = {env.unwrapped.device}", flush=True)
env.reset()
stage = omni.usd.get_context().get_stage()


def particle_sets():
    from pxr import PhysxSchema

    out = {}
    for prim in stage.Traverse():
        if not prim.HasAPI(PhysxSchema.PhysxParticleSetAPI):
            continue
        if prim.IsA(UsdGeom.PointInstancer):
            pts = UsdGeom.PointInstancer(prim).GetPositionsAttr().Get()
        elif prim.IsA(UsdGeom.Points):
            pts = UsdGeom.Points(prim).GetPointsAttr().Get()
        else:
            pts = None
        n = 0 if pts is None else len(pts)
        out[str(prim.GetPath())] = (prim.GetTypeName(), n, round(sum(q[2] for q in pts) / n, 5) if n else None)
    return out


print(f"[MARK {time.time()-T0:.1f}s] particle sets after reset (n, mean local z):", particle_sets(), flush=True)
t = time.time()
for _ in range(a.steps):
    with torch.inference_mode():
        env.step(torch.zeros(env.action_space.shape, device=env.unwrapped.device))
el = time.time() - t
print(f"[MARK {time.time()-T0:.1f}s] after {a.steps} env steps ({el:.1f} s, {a.steps/el:.2f} env steps/s):",
      particle_sets(), flush=True)
env.close()
app.close()
