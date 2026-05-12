#!/usr/bin/env bash
# ============================================================================
# Powder Excavator — Archimedes auger v4 print-prep pipeline (integrated).
#
# v4 reverts to the original ONE-PIECE rotor (auger + tube fused) per PR
# review — see archimedes-auger.scad header for the architectural rationale.
# The single SCAD source is rendered, manifold-checked, exported to STEP,
# and sliced for the Bambu Lab H2D (project's reference FDM rig per the
# review note "assume an H2D printer in terms of FDM printer build volumes").
#
# Outputs (next to this script):
#   archimedes-auger.stl              Binary STL, single closed-manifold part
#   archimedes-auger.stp              STEP B-rep (faceted) via FreeCAD/OCCT
#   archimedes-auger-iso.png          Isometric preview
#   archimedes-auger-cutaway.png      Half-cutaway showing internal helix
#   slices/archimedes-auger.H2D.gcode PrusaSlicer slice for Bambu Lab H2D
#   slices/AUGER.gcode                8.3-name USB-friendly copy
# Plus optional CuraEngine slices via slice_cura.sh.
#
# Pre-reqs: openscad, admesh, prusa-slicer, freecadcmd, xvfb-run.
#   sudo apt-get install -y openscad admesh prusa-slicer freecad xvfb
# ============================================================================
set -euo pipefail

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SCAD="${HERE}/archimedes-auger.scad"
STL="${HERE}/archimedes-auger.stl"
STP="${HERE}/archimedes-auger.stp"
ISO_PNG="${HERE}/archimedes-auger-iso.png"
CUT_PNG="${HERE}/archimedes-auger-cutaway.png"
SLICES_REPO_DIR="${HERE}/slices"
SLICE_DIR="${SLICE_DIR:-/tmp/auger}"

NOZZLE_DIAMETER="${NOZZLE_DIAMETER:-0.4}"
LAYER_HEIGHT="${LAYER_HEIGHT:-0.2}"
FILAMENT_TYPE="${FILAMENT_TYPE:-PLA}"

mkdir -p "${SLICE_DIR}" "${SLICES_REPO_DIR}"

# ----------------------------------------------------------------------------
# SCAD -> STL -> admesh -> STEP
# ----------------------------------------------------------------------------
echo "==> OpenSCAD render -> ${STL}"
xvfb-run -a openscad -o "${STL}" --export-format=binstl "${SCAD}"

echo "==> admesh manifold check"
admesh -fundecvb "${SLICE_DIR}/archimedes-auger-clean.stl" "${STL}" \
    | grep -E '(Number of parts|disconnected|Degenerate|Volume)' | head -6

echo "==> STL -> STEP via FreeCAD (faceted B-rep)"
# OpenSCAD's kernel is mesh-based and has no native STEP exporter; convert
# via FreeCAD's OCCT bindings. Soft-fail if FreeCAD missing — STL is
# primary; STEP is the consumer-friendly companion.
if command -v freecadcmd >/dev/null 2>&1; then
    freecadcmd "${HERE}/stl_to_step.py" "${STL}" "${STP}" 2>&1 | tail -3 || true
    ls -la "${STP}" 2>/dev/null || echo "  (STEP not produced — continuing)"
else
    echo "  (freecadcmd missing — skipping STEP)"
fi

# ----------------------------------------------------------------------------
# Preview PNGs (iso + half-cutaway).
# ----------------------------------------------------------------------------
echo "==> Preview PNGs (iso + half-cutaway)"
xvfb-run -a openscad -o "${ISO_PNG}" --imgsize=600,800 \
    --autocenter --viewall --colorscheme=Tomorrow "${SCAD}"

# include<> re-runs top-level code, so build an inline copy that omits the
# final archimedes_auger(); call and wraps the geometry in a difference()
# with a slab that bites away the front half of the rotor.
CUT_SCAD="$(mktemp --suffix=.scad)"
{
    sed -n '/^\/\* \[Main Dimensions\] \*\//,/^archimedes_auger();$/p' "${SCAD}" | sed '$d'
    echo 'difference() { archimedes_auger();'
    echo '  translate([-outer_r - 1, -(outer_r + 1), -1])'
    echo '    cube([outer_diameter + 2, outer_r + 1, total_height + 2]); }'
} > "${CUT_SCAD}"
xvfb-run -a openscad --render -o "${CUT_PNG}" --imgsize=600,800 \
    --autocenter --viewall --colorscheme=Tomorrow "${CUT_SCAD}"
rm -f "${CUT_SCAD}"

# ----------------------------------------------------------------------------
# Slice with PrusaSlicer CLI for the Bambu Lab H2D (build volume
# 350 × 320 × 325 mm — the 250 mm-tall auger leaves ~75 mm Z headroom and
# fits the 350 × 320 bed with room for brim + skirt). PrusaSlicer's Marlin
# (legacy) g-code flavour is compatible with Bambu's RepRap-derived
# firmware once the start/end blocks are spelled out explicitly.
# ----------------------------------------------------------------------------
slice_one () {
    local stl="$1" out="$2" temp="$3" first_temp="$4" bed="$5" extra_start="$6"
    prusa-slicer --export-gcode --output "${out}" \
        --filament-diameter 1.75 \
        --nozzle-diameter   "${NOZZLE_DIAMETER}" \
        --filament-type     "${FILAMENT_TYPE}" \
        --temperature ${temp} --bed-temperature 60 \
        --first-layer-temperature ${first_temp} --first-layer-bed-temperature 60 \
        --bed-shape "${bed}" \
        --max-print-height 325 \
        --layer-height "${LAYER_HEIGHT}" --first-layer-height "${LAYER_HEIGHT}" \
        --perimeters 3 --top-solid-layers 5 --bottom-solid-layers 4 \
        --fill-density 40% --fill-pattern gyroid \
        --skirts 1 --skirt-distance 5 --brim-width 4 \
        --support-material --support-material-auto \
        --support-material-threshold 50 \
        --start-gcode "${extra_start}" \
        --end-gcode $'M104 S0\nM140 S0\nG28 X\nM84\n' \
        "${stl}" 2>&1 | tail -3
    grep -E '^; (estimated printing time|filament used \[(mm|cm3)\])' "${out}" \
        | sed 's/^/      /'
}

# Bed shape (PrusaSlicer expects polygon vertices) and start block.
# NOTE: $'...' ANSI-C quoting expands \n to real newlines BEFORE the string
# is handed to PrusaSlicer; plain "..." would write a literal "\n" into the
# start-gcode block, producing one mangled line that firmware would reject.
H2D_BED='0x0,350x0,350x320,0x320'
H2D_START=$'G28\nG1 Z5 F5000\n'

H2D_OUT="${SLICES_REPO_DIR}/archimedes-auger.H2D.gcode"
SHORT_OUT="${SLICES_REPO_DIR}/AUGER.gcode"

echo "==> PrusaSlicer -> Bambu Lab H2D"
slice_one "${STL}" "${H2D_OUT}" 215 215 "${H2D_BED}" "${H2D_START}"

# 8.3-name USB-friendly copy for printer LCDs that truncate long filenames.
cp "${H2D_OUT}" "${SHORT_OUT}"

# ----------------------------------------------------------------------------
# Optional CuraEngine slice for parity with desktop Cura users.
# ----------------------------------------------------------------------------
echo
echo "==> [bonus] CuraEngine slice (Ultimaker Cura toolchain)"
if bash "${HERE}/slice_cura.sh"; then
    echo "    (CuraEngine slice written under ${SLICES_REPO_DIR}/)"
else
    echo "    (CuraEngine slice skipped — install with 'sudo snap install cura-slicer')" >&2
fi

echo
echo "==> Done."
echo "    STL:      ${STL}"
echo "    STEP:     ${STP}"
echo "    Iso:      ${ISO_PNG}"
echo "    Cutaway:  ${CUT_PNG}"
echo "    G-code:   ${H2D_OUT}"
echo "    USB:      ${SHORT_OUT}"
