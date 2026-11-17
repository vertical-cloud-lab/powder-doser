"""Write an OpenFOAM v1912 DPMFoam (CFD-DEM: volume-averaged gas + soft-sphere DEM
parcels, nParticle = 1) case: a plug of coarse-grained AlSi10Mg-like particles released
from rest 45 mm above a plate, inside a 10 x 50 x 10 mm closed box open at the top.
Modes:
  twoway : drag (ErgunWenYu) + two-way momentum coupling (gas is dragged by the plug)
  oneway : drag on particles, gas stays at rest (coupled false), NO particle contacts
           (cheap isolated-particle reference; DPM rather than DEM)
  vacuum : no drag, no coupling (DEM + gravity only)
Usage: python make_case.py <mode> <case_dir>
"""
import os, sys
import numpy as np

mode, case = sys.argv[1], sys.argv[2]
D = 100e-6        # particle diameter (coarse-grained from d50 = 35 um)
RHO = 2670.0      # AlSi10Mg
YP = 31.0e-3      # plug centre height (fall ~30 mm)
NX, NY, NZ = 16, 70, 16          # 0.5 mm cells
X0, X1, Y0, Y1 = -4.0, 4.0, 0.0, 35.0   # mm

hdr = """FoamFile
{{
    version     2.0;
    format      ascii;
    class       {cls};
    location    "{loc}";
    object      {obj};
}}
"""
def w(rel, cls, obj, body):
    p = os.path.join(case, rel)
    os.makedirs(os.path.dirname(p), exist_ok=True)
    with open(p, 'w') as f:
        f.write(hdr.format(cls=cls, loc=os.path.dirname(rel), obj=obj) + body)

w('system/blockMeshDict', 'dictionary', 'blockMeshDict', f"""
scale 0.001;
vertices
(
    ({X0} {Y0} {X0}) ({X1} {Y0} {X0}) ({X1} {Y1} {X0}) ({X0} {Y1} {X0})
    ({X0} {Y0} {X1}) ({X1} {Y0} {X1}) ({X1} {Y1} {X1}) ({X0} {Y1} {X1})
);
blocks ( hex (0 1 2 3 4 5 6 7) ({NX} {NY} {NZ}) simpleGrading (1 1 1) );
edges ();
boundary
(
    top    {{ type patch; faces ( (3 7 6 2) ); }}
    bottom {{ type wall;  faces ( (0 1 5 4) ); }}
    walls  {{ type wall;  faces ( (0 4 7 3) (1 2 6 5) (0 3 2 1) (4 5 6 7) ); }}
);
""")
w('system/controlDict', 'dictionary', 'controlDict', """
application     DPMFoam;
startFrom       startTime;
startTime       0;
stopAt          endTime;
endTime         0.13;
deltaT          2e-4;
writeControl    runTime;
writeInterval   0.002;
purgeWrite      0;
writeFormat     ascii;
writePrecision  7;
writeCompression off;
timeFormat      general;
timePrecision   6;
runTimeModifiable no;
""")
w('system/fvSchemes', 'dictionary', 'fvSchemes', """
ddtSchemes { default Euler; }
gradSchemes { default Gauss linear; }
divSchemes
{
    default none;
    div(alphaPhi.air,U.air) Gauss linearUpwindV unlimited;
    div(((alpha.air*nuEff.air)*dev2(T(grad(U.air))))) Gauss linear;
}
laplacianSchemes { default Gauss linear corrected; }
interpolationSchemes { default linear; }
snGradSchemes { default corrected; }
""")
w('system/fvSolution', 'dictionary', 'fvSolution', """
solvers
{
    "(p|kinematicCloud:theta)" { solver GAMG; tolerance 1e-06; relTol 0.01; smoother GaussSeidel; }
    "(p|kinematicCloud:theta)Final" { solver GAMG; tolerance 1e-06; relTol 0; smoother GaussSeidel; }
    "(U.air|k|omega)" { solver smoothSolver; smoother symGaussSeidel; tolerance 1e-05; relTol 0.1; }
    "(U.air|k|omega)Final" { solver smoothSolver; smoother symGaussSeidel; tolerance 1e-05; relTol 0; }
}
PIMPLE { nOuterCorrectors 1; nCorrectors 2; momentumPredictor yes; nNonOrthogonalCorrectors 0; pRefCell 0; pRefValue 0; }
relaxationFactors { }
""")
w('constant/g', 'uniformDimensionedVectorField', 'g', """
dimensions [0 1 -2 0 0 0 0];
value (0 -9.81 0);
""")
w('constant/transportProperties', 'dictionary', 'transportProperties', """
continuousPhase air;
rho.air         1.2;
transportModel  Newtonian;
nu              1.5e-05;
""")
w('constant/turbulenceProperties.air', 'dictionary', 'turbulenceProperties.air', "simulationType laminar;\n")
w('0/U.air', 'volVectorField', 'U.air', """
dimensions [0 1 -1 0 0 0 0];
internalField uniform (0 0 0);
boundaryField
{
    top    { type pressureInletOutletVelocity; phi phi.air; inletValue uniform (0 0 0); value uniform (0 0 0); }
    bottom { type noSlip; }
    walls  { type noSlip; }
}
""")
w('0/p', 'volScalarField', 'p', """
dimensions [0 2 -2 0 0 0 0];
internalField uniform 0;
boundaryField
{
    top    { type fixedValue; value uniform 0; }
    bottom { type fixedFluxPressure; phi phi.air; value uniform 0; }
    walls  { type fixedFluxPressure; phi phi.air; value uniform 0; }
}
""")

drag = "" if mode == 'vacuum' else "ErgunWenYuDrag { alphac alpha.air; }"
coupled = 'true' if mode == 'twoway' else 'false'
w('constant/kinematicCloudProperties', 'dictionary', 'kinematicCloudProperties', f"""
solution
{{
    active true; coupled {coupled}; transient yes; cellValueSourceCorrection off;
    interpolationSchemes {{ rho.air cell; U.air cellPoint; mu.air cell; }}
    integrationSchemes {{ U Euler; }}
    sourceTerms {{ schemes {{ U semiImplicit 1; }} }}
}}
constantProperties
{{
    parcelTypeId 1; rhoMin 1e-15; minParcelMass 1e-15;
    rho0 {RHO}; youngsModulus 1e4; poissonsRatio 0.35; constantVolume false; alphaMax 0.99;
}}
subModels
{{
    particleForces {{ {drag} gravity; }}
    injectionModels
    {{
        model1
        {{
            type manualInjection; massTotal 0; parcelBasisType fixed; nParticle 1; SOI 0;
            positionsFile "kinematicCloudPositions"; U0 (0 0 0);
            sizeDistribution {{ type fixedValue; fixedValueDistribution {{ value {D}; }} }}
        }}
    }}
    dispersionModel none;
    patchInteractionModel localInteraction;
    localInteractionCoeffs
    {{
        patches
        (
            top    {{ type escape; }}
            bottom {{ type rebound; e 0.5; mu 0.4; }}
            walls  {{ type rebound; e 0.5; mu 0.4; }}
        );
    }}
    heatTransferModel none;
    surfaceFilmModel none;
    collisionModel {'none' if mode == 'oneway' else 'pairCollision'};
    pairCollisionCoeffs
    {{
        maxInteractionDistance {D};
        writeReferredParticleCloud no;
        pairModel pairSpringSliderDashpot;
        pairSpringSliderDashpotCoeffs
        {{ useEquivalentSize no; alpha 0.12; b 1.5; mu 0.5; cohesionEnergyDensity 0; collisionResolutionSteps 5; }};
        wallModel wallSpringSliderDashpot;
        wallSpringSliderDashpotCoeffs
        {{ useEquivalentSize no; collisionResolutionSteps 5; youngsModulus 1e4; poissonsRatio 0.35;
           alpha 0.12; b 1.5; mu 0.4; cohesionEnergyDensity 0; }};
        U U.air;
    }}
    stochasticCollisionModel none;
    radiation off;
}}
cloudFunctions {{}}
""")

# plug: jittered simple-cubic lattice inside a cylinder (diameter 1.4 mm, height 1.0 mm), solid fraction ~0.3
phi = 0.30
a = D * (np.pi / (6 * phi)) ** (1 / 3)
rng = np.random.default_rng(0)
RP, HP = 0.7e-3, 1.0e-3
g = np.arange(-RP, RP + 1e-12, a)
gy = np.arange(-HP / 2, HP / 2 + 1e-12, a)
pts = []
for x in g:
    for z in g:
        if x * x + z * z > (RP - D / 2) ** 2:
            continue
        for y in gy:
            j = rng.uniform(-0.45, 0.45, 3) * (a - D)
            pts.append((x + j[0], YP + y + j[1], z + j[2]))
pts = np.array(pts)
w('constant/kinematicCloudPositions', 'vectorField', 'kinematicCloudPositions',
  "(\n" + "\n".join("(%.7e %.7e %.7e)" % tuple(p) for p in pts) + "\n)\n")
print(mode, 'particles', len(pts), 'lattice a [um]', a * 1e6)
