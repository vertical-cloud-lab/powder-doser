// MercuryDPM driver: discharge of coarse-grained "table salt" spheres from a flat-bottomed
// cylindrical silo through a central circular orifice; writes the mass left in the silo vs time
// (SaltSilo_D<mm>.flow) so the discharge rate can be compared with the Beverloo correlation.
// Build: copy into MercuryDPM/Drivers/MercurySimpleDemos/, re-run cmake, `make SaltSilo`.
// Run:   SILO_D_MM=10 SILO_N=2500 ./SaltSilo   (optional: SILO_RS_MM=12.5 SILO_T_DISCHARGE=0.5)
#include "Mercury3D.h"
#include "Walls/AxisymmetricIntersectionOfWalls.h"
#include "Walls/InfiniteWall.h"
#include "Boundaries/DeletionBoundary.h"
#include "Species/LinearViscoelasticFrictionSpecies.h"
#include <cstdlib>
#include <fstream>
#include <cmath>

class SaltSilo : public Mercury3D
{
public:
    Mdouble Rs = 12.5e-3; // silo radius (m)
    Mdouble Ro = 5e-3;    // orifice radius (m)
    Mdouble t = 2e-3;     // bottom-plate thickness (m)
    Mdouble tOpen = 0.25; // orifice opens at this time (s)
    unsigned N = 2500;
    // salt PSD 0.361/0.425/0.489 mm scaled by a coarse-graining factor of 4
    Mdouble d[3] = {1.444e-3, 1.700e-3, 1.956e-3};
    Mdouble frac[3] = {0.3, 0.4, 0.3};
    std::ofstream flow;
    InfiniteWall* lid = nullptr;
    bool isOpen = false;

    void setupInitialConditions() override
    {
        auto sp = speciesHandler.getObject(0);
        auto sw = speciesHandler.getObject(1);

        AxisymmetricIntersectionOfWalls cyl;   // solid region r > Rs
        cyl.setSpecies(sw);
        cyl.setPosition(Vec3D(0, 0, 0));
        cyl.setAxis(Vec3D(0, 0, 1));
        cyl.addObject(Vec3D(1, 0, 0), Vec3D(Rs, 0, 0));
        wallHandler.copyAndAddObject(cyl);

        AxisymmetricIntersectionOfWalls plate; // solid region r > Ro, -t < z < 0
        plate.setSpecies(sw);
        plate.setPosition(Vec3D(0, 0, 0));
        plate.setAxis(Vec3D(0, 0, 1));
        plate.addObject(Vec3D(1, 0, 0), Vec3D(Ro, 0, 0));
        plate.addObject(Vec3D(0, 0, -1), Vec3D(0, 0, 0));
        plate.addObject(Vec3D(0, 0, 1), Vec3D(0, 0, -t));
        wallHandler.copyAndAddObject(plate);

        InfiniteWall closure;                  // closes the orifice while filling (solid z < 0)
        closure.setSpecies(sw);
        closure.set(Vec3D(0, 0, -1), Vec3D(0, 0, 0));
        lid = wallHandler.copyAndAddObject(closure);

        DeletionBoundary del;                  // remove grains 30 mm below the plate
        del.set(Vec3D(0, 0, -1), 0.03);
        boundaryHandler.copyAndAddObject(del);

        SphericalParticle p;
        p.setSpecies(sp);
        const Mdouble dmax = d[2] * 1.05;
        unsigned n = 0;
        for (Mdouble z = 0.5 * dmax; n < N; z += dmax)
        {
            for (Mdouble r = Rs - 0.55 * dmax; r > 0.45 * dmax && n < N; r -= dmax)
            {
                unsigned nc = std::max(1u, (unsigned) std::floor(2.0 * constants::pi * r / dmax));
                Mdouble th0 = random.getRandomNumber(0.0, 2.0 * constants::pi);
                for (unsigned k = 0; k < nc && n < N; ++k)
                {
                    Mdouble u = random.getRandomNumber(0.0, 1.0);
                    int ty = (u < frac[0]) ? 0 : ((u < frac[0] + frac[1]) ? 1 : 2);
                    p.setRadius(0.5 * d[ty]);
                    Mdouble th = th0 + 2.0 * constants::pi * k / nc;
                    p.setPosition(Vec3D(r * std::cos(th), r * std::sin(th), z));
                    p.setVelocity(Vec3D(random.getRandomNumber(-0.05, 0.05),
                                        random.getRandomNumber(-0.05, 0.05),
                                        random.getRandomNumber(-0.1, 0.0)));
                    particleHandler.copyAndAddObject(p);
                    ++n;
                }
            }
        }
        logger(INFO, "Inserted % particles, total mass % kg", particleHandler.getSize(), particleHandler.getMass());
        flow.open(getName() + ".flow");
        flow << "# time_s n_particles mass_above_plate_bottom_kg mass_deleted_kg\n";
    }

    void actionsAfterTimeStep() override
    {
        if (!isOpen && getTime() >= tOpen)
        {
            lid->set(Vec3D(0, 0, -1), Vec3D(0, 0, -1.0)); // move the closure 1 m down: orifice open
            isOpen = true;
            logger(INFO, "Orifice opened at t = % s", getTime());
        }
        if (getNumberOfTimeSteps() % 50 == 0)
        {
            Mdouble msilo = 0;
            for (BaseParticle* q : particleHandler)
                if (q->getPosition().Z > -t) msilo += q->getMass();
            auto del = dynamic_cast<DeletionBoundary*>(boundaryHandler.getObject(0));
            flow << getTime() << " " << particleHandler.getSize() << " " << msilo << " "
                 << del->getMassOfParticlesDeleted() << std::endl;
        }
    }
};

int main(int argc, char* argv[])
{
    SaltSilo silo;
    const char* sD = std::getenv("SILO_D_MM");
    const char* sN = std::getenv("SILO_N");
    const char* sR = std::getenv("SILO_RS_MM");      // silo radius (mm), default 12.5
    const char* sT = std::getenv("SILO_T_DISCHARGE"); // simulated time after opening (s), default 0.5
    const Mdouble Dmm = sD ? std::atof(sD) : 10.0;
    silo.Ro = 0.5e-3 * Dmm;
    if (sN) silo.N = (unsigned) std::atoi(sN);
    if (sR) silo.Rs = 1e-3 * std::atof(sR);
    const Mdouble tDis = sT ? std::atof(sT) : 0.5;
    silo.setName("SaltSilo_D" + std::to_string((int) std::lround(Dmm)));

    const Mdouble rho = 2165.0, e = 0.5, tc = 1.0e-3;
    const Mdouble dmean = 1.7e-3;
    const Mdouble mMean = rho * constants::pi / 6.0 * dmean * dmean * dmean;
    const Mdouble mMin = rho * constants::pi / 6.0 * std::pow(1.444e-3, 3);

    LinearViscoelasticFrictionSpecies s;   // particle-particle
    s.setDensity(rho);
    s.setCollisionTimeAndRestitutionCoefficient(tc, e, mMean);
    s.setSlidingFrictionCoefficient(0.5);
    s.setSlidingStiffness(2.0 / 7.0 * s.getStiffness());
    s.setSlidingDissipation(2.0 / 7.0 * s.getDissipation());
    s.setRollingFrictionCoefficient(0.3);
    s.setRollingStiffness(2.0 / 5.0 * s.getStiffness());
    s.setRollingDissipation(2.0 / 5.0 * s.getDissipation());
    auto ps = silo.speciesHandler.copyAndAddObject(s);
    auto ws = silo.speciesHandler.copyAndAddObject(s); // wall species (same contact law)
    auto mix = silo.speciesHandler.getMixedObject(ps, ws);
    mix->setSlidingFrictionCoefficient(0.4);           // particle-wall sliding friction

    const Mdouble tcMin = ps->getCollisionTime(mMin);
    logger(INFO, "k = % N/m, tc(mean) = % s, tc(min) = % s", ps->getStiffness(), tc, tcMin);
    silo.setTimeStep(tcMin / 25.0); // tc/25 (MercuryDPM suggests tc/50) to fit the shared runner's time budget
    silo.setTimeMax(silo.tOpen + tDis);
    silo.setGravity(Vec3D(0, 0, -9.81));
    silo.setXMin(-silo.Rs); silo.setXMax(silo.Rs);
    silo.setYMin(-silo.Rs); silo.setYMax(silo.Rs);
    silo.setZMin(-0.03);    silo.setZMax(0.05);
    silo.setSaveCount((unsigned) std::lround(0.02 / silo.getTimeStep()));
    silo.fStatFile.setFileType(FileType::NO_FILE);
    silo.restartFile.setFileType(FileType::NO_FILE);
    silo.solve(argc, argv);
    return 0;
}
