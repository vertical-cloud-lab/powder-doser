"""Build the MuJoCo model (MJCF string) of the tilted rotating auger dosing into a vial on a balance."""
from __future__ import annotations

import numpy as np

import auger_geom as G

# Model units: mm, g, s (MuJoCo is unit-agnostic; mm/g keeps the tiny grains well conditioned)
MM = 1.0
LU = 1000.0   # mm per m
MU = 1000.0   # g per kg


def frame_quat(tilt_deg):
    """Quaternion of the auger frame: local +z (outlet -> cap) = (cos t, 0, sin t) in the world."""
    beta = np.radians(90.0 - tilt_deg)
    return np.array([np.cos(beta / 2), 0.0, np.sin(beta / 2), 0.0])


def frame_R(tilt_deg):
    b = np.radians(90.0 - tilt_deg)
    return np.array([[np.cos(b), 0, np.sin(b)], [0, 1, 0], [-np.sin(b), 0, np.cos(b)]])


def fmt(v):
    return " ".join(f"{x:.7g}" for x in np.ravel(v))


def particle_lattice(n, rp_mm, z_cut, spacing=2.08, z_min=None):
    """Lattice points (auger frame, mm) that clear the walls/flight, nearest the outlet first."""
    s = spacing * rp_mm
    pts = []
    zs = np.arange((z_min or (G.FUNNEL_H + rp_mm + 0.3)), 240.0, s)
    xs = np.arange(-G.BORE_R, G.BORE_R + 1e-9, s)
    for z in zs:
        off = (0.5 * s) * (int(round(z / s)) % 2)
        for x in xs + off:
            for y in xs + off:
                r = np.hypot(x, y)
                th = np.arctan2(y, x) % (2 * np.pi)
                if G.free_slot(r, th, z, rp_mm, z_cut):
                    pts.append((x, y, z))
        if len(pts) >= n:
            break
    pts = np.array(pts[:n])
    if len(pts) < n:
        raise RuntimeError(f"only {len(pts)} slots for {n} grains")
    return pts


def build_xml(tilt_deg=30.0, n_grains=2000, rp_mm=0.75, z_cut=0.0, z_top=100.0,
              mu=0.5, mu_roll=0.2, mu_tors=0.2, rho=2160.0, dt=1e-3,
              solref="0.004 1", solver="CG", iterations=50, H=150.0, vial_gap_mm=35.0,
              vial_r_mm=12.0, vial_h_mm=40.0, balance_k=500.0, mount_k=25000.0, mount_c=10.0,  # SI (N/m, N s/m)
              grain_positions_world=None, cone="elliptic", noslip=0, impratio=1.0, rgba_wall="0.55 0.62 0.72 1"):
    R = frame_R(tilt_deg)
    O = np.array([0.0, 0.0, H])
    geoms = G.auger_boxes(z_cut=z_cut, z_top=z_top)
    gx = []
    colors = dict(wall=rgba_wall, funnel=rgba_wall, core="0.85 0.62 0.25 1", tip="0.85 0.62 0.25 1",
                  flight="0.25 0.45 0.85 1", cap="0.55 0.62 0.72 1")
    for i, g in enumerate(geoms):
        gx.append(f'<geom name="{g["kind"]}{i}" class="solid" type="{g["type"]}" size="{fmt(np.array(g["size"]) * MM)}" '
                  f'pos="{fmt(np.array(g["pos"]) * MM)}" quat="{fmt(g["quat"])}" rgba="{colors[g["kind"]]}"/>')
    # plug closing the outlet during settling
    plug_r = float(G.r_wall(z_cut)) + 1.5
    gx.append(f'<geom name="plug" class="solid" type="cylinder" size="{plug_r * MM:.6g} {0.5 * MM:.6g}" '
              f'pos="0 0 {(z_cut - 0.5 - rp_mm * 0.0) * MM:.6g}" rgba="0.9 0.2 0.2 1"/>')
    auger_geoms = "\n          ".join(gx)
    # vial (ring of boxes) on a balance (slide joint with a stiff spring)
    vial = []
    nv = 20
    for i in range(nv):
        th = 2 * np.pi * i / nv
        hw = vial_r_mm * np.tan(np.pi / nv) * 1.2 + 0.3
        c = np.array([np.cos(th), np.sin(th)]) * (vial_r_mm + 0.6)
        q = [np.cos(th / 2), 0, 0, np.sin(th / 2)]
        vial.append(f'<geom class="solid" type="box" size="{0.6 * MM:.6g} {hw * MM:.6g} {vial_h_mm / 2 * MM:.6g}" '
                    f'pos="{c[0] * MM:.6g} {c[1] * MM:.6g} {vial_h_mm / 2 * MM:.6g}" quat="{fmt(q)}" rgba="0.8 0.9 1 0.25" group="1"/>')
    vial.append(f'<geom class="solid" type="cylinder" size="{(vial_r_mm + 1.2) * MM:.6g} {0.6 * MM:.6g}" pos="0 0 {-0.6 * MM:.6g}" rgba="0.8 0.9 1 0.6"/>')
    vial_xml = "\n      ".join(vial)
    vial_bottom = H - (vial_gap_mm + vial_h_mm) * MM
    # grains
    m_grain = rho * 1e-6 * 4 / 3 * np.pi * rp_mm ** 3      # g (rho kg/m^3 -> g/mm^3)
    if grain_positions_world is None:
        loc = particle_lattice(n_grains, rp_mm, z_cut)
        grain_positions_world = (O[None, :] + (R @ (loc * MM).T).T)
    gr = []
    for i, p in enumerate(grain_positions_world):
        gr.append(f'<body name="g{i}" pos="{fmt(p)}"><freejoint/><geom class="grain"/></body>')
    grains_xml = "\n    ".join(gr)
    q = frame_quat(tilt_deg)
    xml = f"""
<mujoco model="auger_dosing">
  <compiler angle="radian" autolimits="true"/>
  <option timestep="{dt}" gravity="0 0 -9810" solver="{solver}" iterations="{iterations}" ls_iterations="10"
          cone="{cone}" integrator="implicitfast" noslip_iterations="{noslip}" impratio="{impratio}" tolerance="1e-6"/>
  <size memory="1500M"/>
  <visual>
    <global offwidth="1920" offheight="1080"/>
    <quality shadowsize="4096"/>
    <headlight ambient="0.35 0.35 0.35" diffuse="0.6 0.6 0.6"/>
  </visual>
  <default>
    <geom solref="{solref}" solimp="0.9 0.95 0.5"/>
    <default class="solid"><geom contype="1" conaffinity="0" condim="3" friction="{mu} {mu_tors} {mu_roll}"/></default>
    <default class="grain"><geom type="sphere" size="{rp_mm * MM:.6g}" mass="{m_grain:.6g}" contype="2" conaffinity="3"
       condim="6" friction="{mu} {mu_tors} {mu_roll}" rgba="0.95 0.85 0.55 1"/></default>
  </default>
  <worldbody>
    <light pos="50 -300 500" dir="-0.1 0.6 -0.8" diffuse="0.5 0.5 0.5"/>
    <geom name="floor" type="plane" size="300 300 10" class="solid" rgba="0.92 0.92 0.92 1"/>
    <body name="frame" pos="{fmt(O)}" quat="{fmt(q)}">
      <body name="mount">
        <joint name="mount" type="slide" axis="1 0 0" stiffness="{mount_k * MU:.6g}" damping="{mount_c * MU:.6g}"/>
        <inertial pos="0 0 50" mass="40" diaginertia="1e4 1e4 1e4"/>
        <body name="auger">
          <joint name="spin" type="hinge" axis="0 0 1" armature="1e4" damping="0"/>
          <inertial pos="0 0 80" mass="60" diaginertia="2.5e5 2.5e5 6e3"/>
          {auger_geoms}
        </body>
      </body>
    </body>
    <body name="balance" pos="0 0 {vial_bottom:.6g}">
      <joint name="balance" type="slide" axis="0 0 1" stiffness="{balance_k * MU:.6g}" damping="{2 * np.sqrt(balance_k * MU * 12):.6g}"/>
      <inertial pos="0 0 10" mass="12" diaginertia="1e3 1e3 1e3"/>
      {vial_xml}
    </body>
    {grains_xml}
  </worldbody>
  <actuator>
    <velocity name="motor" joint="spin" kv="2e7" ctrlrange="-20 20"/>
  </actuator>
</mujoco>
"""
    meta = dict(tilt_deg=tilt_deg, n_grains=int(len(grain_positions_world)), rp_mm=rp_mm, z_cut_mm=z_cut,
                z_top_mm=z_top, mu=mu, mu_roll_mm=mu_roll, mu_tors_mm=mu_tors, rho=rho, m_grain_g=m_grain, units="mm, g, s",
                dt=dt, solref=solref, solver=solver, iterations=iterations, impratio=impratio, noslip_iterations=noslip, H=H, vial_gap_mm=vial_gap_mm,
                vial_r_mm=vial_r_mm, vial_h_mm=vial_h_mm, vial_bottom=vial_bottom, balance_k=balance_k,
                mount_k=mount_k, mount_c=mount_c, exit_r_mm=float(G.r_wall(z_cut)), tip_r_mm=float(G.r_tip(z_cut)))
    return xml, meta
