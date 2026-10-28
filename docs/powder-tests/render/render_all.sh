#!/usr/bin/env bash
# Render every scene to ../animations/<name>.{mp4,gif} and <name>_poster.png.
# Needs an X display for VTK: uses Xvfb when DISPLAY is unset. Usage: ./render_all.sh [scene ...]
set -euo pipefail
cd "$(dirname "$0")"
PY=${PYTHON:-python3}
scenes=("$@")
if [ ${#scenes[@]} -eq 0 ]; then
  scenes=(hall_flow density angle_of_repose sieve laser_diffraction moisture_lod ft4_shear ring_shear)
fi
if [ -z "${DISPLAY:-}" ]; then
  Xvfb :97 -screen 0 1920x1080x24 -nolisten tcp >/dev/null 2>&1 &
  XPID=$!
  trap 'kill $XPID' EXIT
  export DISPLAY=:97
  sleep 1
fi
printf '%s\n' "${scenes[@]}" | xargs -P "${JOBS:-3}" -I{} "$PY" {}.py
