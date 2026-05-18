#!/usr/bin/env bash
# Render every .kcl source in kcl/ to STEP + STL + iso PNG via the zoo.dev
# `zoo` CLI.  Requires ZOO_API_TOKEN in the environment and a funded zoo.dev
# account.  See README.md for the payment-blocker we hit while authoring this
# package.
#
# Usage:
#   ZOO_API_TOKEN=... ./render_with_zoo.sh
set -euo pipefail

HERE="$(cd "$(dirname "$0")" && pwd)"
ZOO=${ZOO_CLI:-zoo}

mkdir -p "$HERE/step" "$HERE/stl" "$HERE/views"

# Re-export the main parts (params.kcl is shared, not rendered).
parts=(
  mounting_plate baseplate hinge_pin linear_actuator_placeholder
  cup_placeholder scale_placeholder auger_placeholder
  bracket_placeholder tap_collar_mount_placeholder nema17_placeholder
)

for name in "${parts[@]}"; do
  src="$HERE/kcl/${name}.kcl"
  echo ">>> $name"
  "$ZOO" kcl export --output-format=step "$src" "$HERE/step"
  mv "$HERE/step/output.step" "$HERE/step/${name}.step"
  "$ZOO" kcl export --output-format=stl "$src" "$HERE/stl"
  mv "$HERE/stl/output.stl" "$HERE/stl/${name}.stl"
  "$ZOO" kcl snapshot "$src" "$HERE/views/${name}.png"
done
