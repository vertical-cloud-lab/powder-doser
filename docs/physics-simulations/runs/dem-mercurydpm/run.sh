#!/bin/bash
# Clone and build MercuryDPM with the SaltSilo driver, run both orifices, then the analysis.
set -e
HERE=$(cd "$(dirname "$0")" && pwd)
W=${W:-/tmp/sims-scratch/dem-mercurydpm}
mkdir -p "$W"; cd "$W"
[ -d src ] || git clone --depth 1 https://bitbucket.org/mercurydpm/mercurydpm.git src
cp "$HERE/SaltSilo.cpp" src/Drivers/MercurySimpleDemos/
mkdir -p build && cd build
cmake ../src -DCMAKE_BUILD_TYPE=Release > cmake.log
make -j2 SaltSilo > build_saltsilo.log
BIN="$W/build/Drivers/MercurySimpleDemos/SaltSilo"
export OMP_NUM_THREADS=1
mkdir -p "$W/run2" "$W/run3"
(cd "$W/run2" && SILO_D_MM=10 SILO_N=2500 "$BIN" > silo_D10.log 2>&1)
(cd "$W/run3" && SILO_D_MM=14 SILO_N=3000 SILO_RS_MM=15 SILO_T_DISCHARGE=0.35 "$BIN" > silo_D14.log 2>&1)
python3 "$HERE/analyze.py" "$W" "$HERE"
