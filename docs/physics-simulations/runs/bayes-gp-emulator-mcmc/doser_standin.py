"""Cheap stand-in for the LIGGGHTS auger-doser DEM twin (NOT a DEM).

Maps contact parameters (sliding friction mu_s, rolling friction mu_r, granular
Bond number Bo) to the dosing fingerprint (mg per auger revolution vs tilt) and
to a static angle of repose. Every relation below is a textbook scaling law or
an explicitly assumed closure; the constants marked "set by hand" were chosen so
that the DEM twin's nominal salt parameters (mu_s=0.5, mu_w=0.4, mu_r=0.3, no
cohesion) land in the measured range. They are held fixed during inference.

Equations (SI inside, mm and mg at the interface):
  mu_w      = 0.8 mu_s                                    (DEM ratio 0.4/0.5)
  w_eff     = w - k d (1 + gamma Bo)                      (Beverloo empty annulus; cohesive arching widens it)
  A_eff     = pi (r_o + r_i) w_eff                        (effective annulus area)
  m_push    = eta_p rho_b A_eff p                         (flight extrudes a plug through the annulus each rev)
  C         = C_slot / (1 + a_r mu_r)                     (rolling resistance lowers the discharge coefficient)
  W_B       = C rho_b sqrt(g) pi (r_o + r_i) w_eff^1.5    (Beverloo slot form, Nedderman 1992)
  theta_s   = atan(mu_w (1 + beta Bo)) - atan(w / L_x)    (exit channel must tilt past its wall-friction angle)
  S(theta)  = [sin(theta - theta_s)]_+ ^ 0.5              (Beverloo sqrt(g_eff), g_eff = g sin(theta - theta_s))
  m(theta)  = m_push + W_B (60 / N) S(theta)              (mg per auger revolution)
  AoR       = 68.61 deg mu_s^0.27 mu_w^0.22 l_r^0.18 d_mm^-0.2, then tan(AoR) *= (1 + beta Bo)
              (power-law form of Zhou et al. 2002, Powder Technol. 125:45, with the CDT rolling length
               l_r = mu_r R*, R* = d/4 in mm; used outside its calibrated range, as a plausible trend only)
"""
import numpy as np

G = 9.81
RHO_P = 2165.0            # kg/m3, NaCl
PHI_PACK = 0.58           # assumed loose packing fraction -> rho_b = 1256 kg/m3
RHO_B = RHO_P * PHI_PACK
D_GRAIN = 0.42e-3         # m, mid of 0.36-0.49 mm
R_OUT = 1.5e-3            # m, exit radius (3 mm hole)
R_IN = 0.43e-3            # m, core-tip radius -> 1.07 mm gap, 6.5 mm2 open area
PITCH = 10.4e-3           # m
K_BEV = 1.5               # Beverloo empty-annulus constant (Nedderman 1992)
C_SLOT = 1.03             # Beverloo constant for slots (Nedderman 1992)
ETA_P = 0.8               # set by hand: volumetric efficiency of the plug push
L_X = 4.0e-3              # m, set by hand: effective exit-channel length
A_R = 1.0                 # assumed: sensitivity of C to rolling friction
BETA = 0.5                # assumed: tan(friction angle) grows by 50 % at Bo = 1
GAMMA = 0.3               # assumed: empty annulus grows by 30 % at Bo = 1
RPM = 60.0

TILTS_DEG = np.array([0.0, 22.5, 27.5, 45.0])
# measured salt delivery, mg/rev at 60 rpm (README of PR #184 / issue #179)
OBS_MG = np.array([28.0, 108.0, 105.0, 195.0])
# 27.5 deg: measured +/- 11 mg/rev; elsewhere assumed 10 % with a 3 mg floor
OBS_SD = np.array([3.0, 11.0, 11.0, 19.5])
DEM_TWIN_MG = np.array([33.0, 71.0, 105.0, 153.0])  # LIGGGHTS twin (PR #180)


def mg_per_rev(theta_deg, mu_s, mu_r=0.3, bo=0.0):
    """Stand-in delivery per auger revolution [mg]; broadcasts over arrays."""
    theta = np.deg2rad(np.asarray(theta_deg, float))
    mu_s = np.asarray(mu_s, float)
    mu_r = np.asarray(mu_r, float)
    bo = np.asarray(bo, float)
    mu_w = 0.8 * mu_s
    w = R_OUT - R_IN
    w_eff = np.clip(w - K_BEV * D_GRAIN * (1.0 + GAMMA * bo), 0.0, None)
    lm = np.pi * (R_OUT + R_IN)
    m_push = ETA_P * RHO_B * lm * w_eff * PITCH                     # kg
    c = C_SLOT / (1.0 + A_R * mu_r)
    w_b = c * RHO_B * np.sqrt(G) * lm * w_eff ** 1.5                # kg/s
    theta_s = np.arctan(mu_w * (1.0 + BETA * bo)) - np.arctan(w / L_X)
    s = np.sqrt(np.clip(np.sin(theta - theta_s), 0.0, None))
    return 1e6 * (m_push + w_b * (60.0 / RPM) * s)                  # mg


def angle_of_repose(mu_s, mu_r=0.3, bo=0.0):
    """Stand-in static angle of repose [deg]."""
    mu_s = np.asarray(mu_s, float)
    mu_w = 0.8 * mu_s
    l_r = np.asarray(mu_r, float) * (D_GRAIN * 1e3 / 4.0)          # mm
    phi0 = 68.61 * mu_s ** 0.27 * mu_w ** 0.22 * l_r ** 0.18 * (D_GRAIN * 1e3) ** -0.2
    return np.rad2deg(np.arctan(np.tan(np.deg2rad(phi0)) * (1.0 + BETA * np.asarray(bo, float))))


if __name__ == "__main__":
    print("nominal (0.5, 0.3, 0):", np.round(mg_per_rev(TILTS_DEG, 0.5, 0.3, 0.0), 1),
          "AoR", np.round(angle_of_repose(0.5, 0.3, 0.0), 1))
    print("measured:", OBS_MG, " DEM twin:", DEM_TWIN_MG)
