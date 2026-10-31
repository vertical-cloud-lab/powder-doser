# dem-yade-directshear: periodic triaxial test with cohesive-frictional contacts (Yade)

## What it models and why it matters here
The FT4 shear cell (ASTM D7891) and the Schulze ring shear tester (D6773) give a powder's yield locus. A Mohr-Coulomb
fit of that locus gives the friction angle phi and the cohesion c, and from them the flow function ffc. This run is a
numerical counterpart. A periodic cube of salt-sized spheres with adhesive contacts is compressed triaxially at three
confining stresses. Mohr-Coulomb envelopes are then fitted to the peak and residual (end-of-test) stress states. The
stresses chosen, 50-400 Pa, are those in the doser's hopper and auger (rho_b g h for h of a few cm), not the kPa range
of the FT4. At these stresses an inter-particle adhesion of a few weights per grain is visible as an intercept, which
is the regime the doser fingerprint probes. A periodic triaxial test was used instead of a direct-shear box because
it needs no walls and runs as one small periodic cell.

## Code and version
* Yade `20261024-9637~157eec7~noble1` (the `yadedaily` build), single thread, headless (`yadedaily -j1 -n -x`).
* Ubuntu 24.04 has no `yade` package. The `libyadedaily`, `python3-yadedaily` and `yadedaily` .debs were downloaded
  from the Yade project's repository, http://www.yade-dem.org/packages/ (dists/noble), and installed with
  `apt-get install ./*.deb`.
* Contact law: `CohFrictMat`, `Ip2_CohFrictMat_CohFrictMat_CohFrictPhys` with `setCohesionOnNewContacts=True`, and
  `Law2_ScGeom6D_CohFrictPhys_CohesionMoment`. The stress control is `PeriTriaxController`.

## Setup
* **Particles.** N = 600 spheres at real salt size, with no coarse-graining. Diameters 0.361 / 0.425 / 0.489 mm,
  number fractions 0.3 / 0.4 / 0.3.
* **Material.** Density 2165 kg/m3, E = 2e5 Pa (the twin's reduced value), Poisson 0.3. Contact normal stiffness is
  kn = E R for equal spheres. No gravity, in a periodic cube.
* **Friction.** Sliding friction 0.5 while shearing. Rolling resistance `etaRoll` = 0.3, so the rolling moment is
  limited to 0.3 R Fn. The rolling stiffness is `alphaKr` = 2.
* **Cohesion.** Bond strength F_adh = Bo m g, with granular Bond number **Bo = 5** for the mean grain:
  F_adh = 4.3e-6 N. In Yade this is `normalCohesion` = `shearCohesion` = F_adh / R_mean^2 = 94.6 Pa. Yade scales the
  bond strength as normalCohesion x min(R1, R2)^2. Bonds are brittle (`fragile=True`). Every new contact becomes
  cohesive, so broken bonds re-form when grains touch again. This mimics van der Waals adhesion more than cementation.
* **Procedure.**
  1. A random loose cloud (solid fraction 0.22) is compacted isotropically to sigma3 by the periodic cell's stress
     servo. Inter-particle friction is 0.1 during compaction, to get a dense sample.
  2. Friction is set to 0.5 on all materials and contacts.
  3. The cell is shortened along z, strain-controlled, to a log strain of 0.15, with sigma_xx = sigma_yy = sigma3
     held constant.
* **Stresses and rates.** sigma3 = 50, 150 and 400 Pa. The axial strain rate keeps the inertial number at
  I = eps_dot d sqrt(rho / sigma3) = 2.5e-3 (quasi-static). Local damping is 0.2. dt = 0.5 x P-wave time step.
* **Mohr-Coulomb fit.** t = (s1 - s3)/2 is fitted linearly against s = (s1 + s3)/2. Then sin(phi) = slope and
  c = intercept / cos(phi).
  * Peak: the state at maximum deviator stress.
  * Residual: the mean over the last 3 % of axial strain.

## How to rerun
```
bash run.sh [scratch_dir]       # 3 confining stresses, then analyze.py -> triaxial_mohr_coulomb.png
```
One stress on its own: `OMP_NUM_THREADS=1 yadedaily -j1 -n -x peri_triax.py 150 /tmp/out 600`.

## Runtime
RESULTS_RUNTIME

## Result
RESULTS_TABLE

## Status
RESULTS_STATUS

## Limitations
* **Small sample.** N = 600 in a periodic cube about 9 grains wide: the stress-strain curves are noisy and there is no
  ensemble average. Strain localisation, which matters for the peak in a real shear cell, cannot form.
* **Not a shear-cell protocol.**
  * The test is triaxial compression, not an FT4/Schulze shear test, and there is no pre-shear.
  * The "residual" state is the state at 15 % axial strain, close to critical state but not a large-strain ring-shear
    residual.
  * Without pre-consolidation the run gives no ffc. The yield-locus-at-consolidation procedure would need a further
    unloading step.
* **Adhesion model.** Cohesion is a brittle bond strength that re-forms on new contacts, scaling with R^2. It is not
  JKR/DMT (no attraction at a distance, no load-dependent contact area). Bo = 5 is an assumption, not a measurement for
  the rig's salt.
* **Sample preparation.** The stiffness is reduced (E = 2e5 Pa), and compacting with low friction (0.1) gives a dense
  sample. Both choices change the peak.
