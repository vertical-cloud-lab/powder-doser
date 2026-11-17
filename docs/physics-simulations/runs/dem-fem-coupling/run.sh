#!/bin/bash
# 4C (open-source successor of BACI) particle-structure interaction, from the official Docker image
# (ghcr.io/4c-multiphysics/4c:main, 3.4 GB compressed / 9.7 GB unpacked).
HERE=$(cd "$(dirname "$0")" && pwd)
S=${SCRATCH:-/tmp/sims-scratch/dem-fem-coupling}
IMG=ghcr.io/4c-multiphysics/4c:main
TEST=pasi_twoway_disprelax_particle_dem_1d_normalcontact_linspring_walldiscretcond.4C.yaml
docker pull $IMG
mkdir -p "$S/tests" "$S/run"
docker run --rm -v "$S/tests":/out $IMG bash -c "cp /home/user/4C/tests/input_files/$TEST /out/"
# 1) the unmodified regression test (prints 'OK (9)' when 4C reproduces its reference values)
(cd "$S/tests" && docker run --rm --cpus=1 -u $(id -u):$(id -g) -v "$PWD":/work -w /work $IMG /home/user/4C/build/4C $TEST test > log_test.txt 2>&1; grep -A12 "Checking results" log_test.txt)
# 2) the dose-on-membrane case
python3 "$HERE/make_input.py" "$S/tests/$TEST" "$S/run/dose_membrane.4C.yaml" 14000
(cd "$S/run" && docker run --rm --cpus=1 -e OMP_NUM_THREADS=1 -u $(id -u):$(id -g) -v "$PWD":/work -w /work $IMG /home/user/4C/build/4C dose_membrane.4C.yaml out > log.txt 2>&1)
python3 -m venv /tmp/venv-cfd && /tmp/venv-cfd/bin/pip install -q numpy matplotlib imageio imageio-ffmpeg
/tmp/venv-cfd/bin/python "$HERE/post_4c.py" "$S/run" "$HERE"
