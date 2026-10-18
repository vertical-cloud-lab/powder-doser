"""Run every MuJoCo mesh study in sequence and write the JSON summaries (out/mujoco/*.json).

    python run_studies.py            # about 30-40 min on one core
"""
import mesh_mujoco as M

if __name__ == "__main__":
    M.stall_sweep(configs=["as drawn", "magnet", "magnet + steel pinion", "pin (48,-58)", "proposed at 32.1 mm", "proposed"])
    M.engage_sweep()
    M.runout_sweep()
    M.speed_sweep(configs=("as drawn", "magnet + steel pinion", "proposed"), ecc=0.0, pitch_err=0.0, name="speed_sweep_ideal")
    M.speed_sweep(configs=("proposed",), ecc=0.05, pitch_err=0.0006, name="speed_sweep_errors")
