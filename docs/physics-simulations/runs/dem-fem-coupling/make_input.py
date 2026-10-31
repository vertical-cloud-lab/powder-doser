"""Build a 4C particle-structure-interaction (PASI) input: a 'dose' of NaCl-sized DEM
grains falls onto a clamped neo-Hookean membrane (a compliant weighing-pan proxy),
two-way partitioned DEM-FEM coupling with Aitken relaxation.

The membrane mesh (7x7 MEMBRANE4 quads, clamped edge nodes) is taken from 4C's own
regression test pasi_twoway_disprelax_particle_dem_1d_normalcontact_linspring_walldiscretcond
and scaled from its unit square to 17.5 mm.  Usage:
    python make_input.py <4C test yaml> <out yaml> [NUMSTEP]
"""
import sys
import yaml

src, dst = sys.argv[1], sys.argv[2]
numstep = int(sys.argv[3]) if len(sys.argv) > 3 else 24000
d = yaml.safe_load(open(src))

L = 0.01          # mesh scale: test coordinates (+-0.875) -> +-8.75 mm
r = 0.2125e-3     # NaCl d50 = 0.425 mm
rho = 2165.0
dt = 5e-6

d['BINNING STRATEGY'] = {'BIN_SIZE_LOWER_BOUND': 0.0006,
                         'DOMAINBOUNDINGBOX': '-0.0095 -0.0095 -0.006 0.0095 0.0095 0.006'}
d['PASI DYNAMIC'] = {'RESULTSEVERY': 400, 'RESTARTEVERY': 100000, 'TIMESTEP': dt,
                     'NUMSTEP': numstep, 'MAXTIME': dt * numstep,
                     'COUPLING': 'partitioned_twowaycoup_disprelaxaitken', 'ITEMAX': 20,
                     'CONVTOLSCALEDDISP': 1e-6, 'CONVTOLRELATIVEDISP': 1e-5,
                     'CONVTOLSCALEDFORCE': 1e-6, 'CONVTOLRELATIVEFORCE': 1e-5}
d['IO/RUNTIME VTK OUTPUT'] = {'INTERVAL_STEPS': 400, 'OUTPUT_DATA_FORMAT': 'ascii'}
d['IO/RUNTIME VTK OUTPUT/STRUCTURE'] = {'OUTPUT_STRUCTURE': True, 'DISPLACEMENT': True}
pd = d['PARTICLE DYNAMIC']
pd['GRAVITY_ACCELERATION'] = '0.0 0.0 -9.81'
d['PARTICLE DYNAMIC/DEM'] = {
    'NORMALCONTACTLAW': 'NormalLinearSpringDamp',
    'TANGENTIALCONTACTLAW': 'TangentialLinSpringDamp',
    'MAX_RADIUS': r, 'MAX_VELOCITY': 0.35, 'REL_PENETRATION': 0.05,
    'COEFF_RESTITUTION': 0.5, 'DAMP_REG_FAC': 0.2, 'POISSON_RATIO': 0.3,
    'FRICT_COEFF_TANG': 0.5, 'TENSION_CUTOFF': True}
d['STRUCTURAL DYNAMIC']['M_DAMP'] = 50.0     # 1/s  (Rayleigh, mass-proportional)
d['STRUCTURAL DYNAMIC']['K_DAMP'] = 1e-4     # s    (Rayleigh, stiffness-proportional)
d['MATERIALS'] = [
    {'MAT': 1, 'MAT_ParticleDEM': {'INITRADIUS': r, 'INITDENSITY': rho}},
    {'MAT': 2, 'MAT_ParticleWallDEM': {'FRICT_COEFF_TANG': 0.4}},
    {'MAT': 3, 'MAT_Membrane_ElastHyper': {'NUMMAT': 1, 'MATIDS': [31], 'DENS': 1100.0}},
    {'MAT': 31, 'ELAST_IsoNeoHooke': {'MUE': {'constant': 3.3e5}}},   # rubber-like sheet, E ~ 1 MPa
]
d['DESIGN SURFACE PARTICLE WALL'] = [{'E': 1, 'MAT': 2}]
d.pop('RESULT DESCRIPTION', None)

# scale node coordinates
nc = []
for line in d['NODE COORDS']:
    t = line.split()
    x, y, z = (float(v) * L for v in t[3:6])
    nc.append('NODE %s COORD %.10e %.10e %.10e' % (t[1], x, y, z))
d['NODE COORDS'] = nc
d['STRUCTURE ELEMENTS'] = [e.replace('THICK 0.01', 'THICK 0.0001') for e in d['STRUCTURE ELEMENTS']]

# dose: 8 x 8 x 2 lattice of grains, 3 mm above the membrane, centred
parts = []
sp = 2 * r * 1.06
n = 8
for k in range(2):
    for j in range(n):
        for i in range(n):
            x = (i - (n - 1) / 2) * sp + (0.25 * sp if k else 0.0)
            y = (j - (n - 1) / 2) * sp + (0.25 * sp if k else 0.0)
            z = 3.0e-3 + k * sp
            parts.append('TYPE phase1 POS %.6e %.6e %.6e' % (x, y, z))
d['PARTICLES'] = parts
yaml.safe_dump(d, open(dst, 'w'), sort_keys=False, width=200)
print('wrote', dst, 'particles', len(parts), 'dose mass [mg]', len(parts) * rho * 4 / 3 * 3.14159265 * r ** 3 * 1e6)
