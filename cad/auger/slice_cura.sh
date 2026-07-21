#!/usr/bin/env bash
# ============================================================================
# Powder Excavator — Archimedes auger v4: CuraEngine (Ultimaker Cura) slice.
#
# Companion to render_print.sh. Slices the integrated archimedes-auger.stl
# with Ultimaker's open-source slicing engine, for parity with what most
# desktop Cura users run.
#
# CuraEngine isn't packaged in the GitHub-hosted runner's apt repos. We
# install via `snap install cura-slicer`; falls back to a system PATH lookup
# if a user installed CuraEngine manually.
#
# Outputs (under cad/auger/slices/):
#   archimedes-auger.H2D.cura.gcode   Cura — Bambu Lab H2D
# ============================================================================
set -euo pipefail

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SLICES_DIR="${HERE}/slices"
mkdir -p "${SLICES_DIR}"

STL="${HERE}/archimedes-auger.stl"
OUT="${SLICES_DIR}/archimedes-auger.H2D.cura.gcode"

# ---------------------------------------------------------------------------
# Locate CuraEngine + bundled resources. Try snap first (CI runner), then
# system PATH (manual installs).
# ---------------------------------------------------------------------------
find_cura () {
    local snap_root
    if [[ -d /snap/cura-slicer/current ]]; then
        snap_root=/snap/cura-slicer/current
    elif compgen -G "/snap/cura-slicer/[0-9]*" > /dev/null; then
        snap_root="$(ls -d /snap/cura-slicer/[0-9]* | sort -n | tail -1)"
    fi
    if [[ -n "${snap_root:-}" && -x "${snap_root}/usr/bin/CuraEngine" ]]; then
        CURA="${snap_root}/usr/bin/CuraEngine"
        export LD_LIBRARY_PATH="${snap_root}/usr/lib/x86_64-linux-gnu:${snap_root}/usr/lib${LD_LIBRARY_PATH:+:$LD_LIBRARY_PATH}"
        RES="${snap_root}/usr/share/cura/resources"
        return 0
    fi
    if command -v CuraEngine >/dev/null 2>&1; then
        CURA="$(command -v CuraEngine)"
        RES="${CURA_RESOURCES:-/usr/share/cura/resources}"
        return 0
    fi
    echo "ERROR: CuraEngine not found. Install with:" >&2
    echo "  sudo snap install cura-slicer" >&2
    return 1
}

find_cura

if [[ ! -d "${RES}/definitions" ]]; then
    echo "ERROR: Cura resources directory not found at ${RES}" >&2
    exit 1
fi
export CURA_ENGINE_SEARCH_PATH="${RES}/definitions:${RES}/extruders"

# Resolved Marlin-flavour start/end blocks. CuraEngine's bare CLI doesn't
# resolve `{...}` placeholders the frontend normally substitutes, so the
# blocks are spelled out here for the H2D's 350 × 320 mm bed at PLA temps.
H2D_START=$'G21 ; mm\nG90 ; absolute pos\nM82 ; absolute extrusion\nM104 S210 ; set hotend\nM140 S60 ; set bed\nM190 S60 ; wait bed\nM109 S210 ; wait hotend\nG28 ; home\nG92 E0.0\nG1 Z5 F5000\n'
H2D_END=$'M104 S0\nM140 S0\nM107\nG28 X\nM84\n'

slice_h2d () {
    local stl="$1" out="$2" temp="$3" first_temp="$4" start="$5" end="$6"
    common_args=(
        slice -j "${RES}/definitions/fdmprinter.def.json"
        -s machine_width=350
        -s machine_depth=320
        -s machine_height=325
        -s machine_center_is_zero=false
        -s machine_nozzle_size=0.4
        -s machine_gcode_flavor=Marlin
        -s material_print_temperature="${temp}"
        -s material_print_temperature_layer_0="${first_temp}"
        -s material_bed_temperature=60
        -s material_bed_temperature_layer_0=60
        -s layer_height=0.2
        -s layer_height_0=0.2
        -s wall_line_count=3
        -s top_layers=5
        -s bottom_layers=4
        -s infill_sparse_density=40
        -s infill_pattern=gyroid
        -s adhesion_type=brim
        -s brim_width=4
        -s support_enable=true
        -s support_angle=50
        -s machine_start_gcode="${start}"
        -s machine_end_gcode="${end}"
    )
    # Assert no unresolved Cura placeholders survived into start/end blocks.
    for s in "${start}" "${end}"; do
        if [[ "${s}" == *"{"* ]]; then
            echo "ERROR: unresolved {placeholder} in start/end gcode" >&2
            return 1
        fi
    done
    "${CURA}" "${common_args[@]}" -l "${stl}" -o "${out}" 2>&1 | tail -5
}

echo "==> CuraEngine -> Bambu Lab H2D"
slice_h2d "${STL}" "${OUT}" 210 215 "${H2D_START}" "${H2D_END}"

for gcode in "${OUT}"; do
    [[ -f "${gcode}" ]] || continue
    bytes=$(wc -c <"${gcode}")
    lines=$(wc -l <"${gcode}")
    echo "      ${gcode##*/}: ${bytes} bytes, ${lines} lines"
done

echo
echo "==> Done."
echo "    Cura g-code: ${OUT}"
