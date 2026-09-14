#!/bin/bash
# Launch-gate hold for the dose blocks (G/H): repeated 180 s balance surveys
# until one meets the launch condition the four accepted 2026-09-10 launches
# used, or the window budget runs out.
#
# Runs on the RUNNER (like balance_zero.py / balance_environment_survey.py,
# which bridge to the Pico over SSH themselves via RPI_POWDER_DOSER_*).
#
# Usage: scripts/gate_hold.sh START_IDX END_IDX [CSV_PREFIX]
#   CSV files land at ${CSV_PREFIX}_wN.csv (default /tmp/gatehold_wN.csv);
#   copy the keepers into docs/rig-checks/data/ with the survey-series
#   naming when recording a hold.
#
# Launch condition per 180 s window:
#   end-to-end (median of last 5 samples minus median of first 5) inside
#   +/-6 mg, peak-to-peak <= 6 mg, zero single-poll jumps >= 10 mg.
#   A marginal window (peak-to-peak <= 9 mg) launches only if the next
#   window confirms it (state carried in ${CSV_PREFIX}_state).
#
# Exit codes: 0 = launch (criteria met), 2 = budget exhausted (stand down),
#   3 = survey error, 4 = end of this invocation's range without a decision.
#
# Validated live 2026-09-14 (30 windows, third silicon -110/+200 stand-down).
cd "$(dirname "$0")/.." || exit 3
START=${1:-1}; ENDW=${2:-13}; PREFIX=${3:-/tmp/gatehold}
for ((i=START; i<=ENDW; i++)); do
  CSV=${PREFIX}_w${i}.csv
  python3 scripts/balance_environment_survey.py --settle 180 --csv "$CSV" --port /dev/ttyACM0 > "${PREFIX}_w${i}.log" 2>&1 || true
  if [ ! -s "$CSV" ]; then echo "GATE,ERROR,window=$i,no-csv"; tail -5 "${PREFIX}_w${i}.log"; exit 3; fi
  RES=$(python3 - "$CSV" <<'PYEOF'
import csv, sys
rows = [(float(r["t_s"]), float(r["mg"])) for r in csv.DictReader(open(sys.argv[1]))]
mg = [m for _, m in rows]
def med(x):
    s = sorted(x); return s[len(s)//2]
e2e = med(mg[-5:]) - med(mg[:5])
p2p = max(mg) - min(mg)
jumps = sum(1 for a, b in zip(mg, mg[1:]) if abs(b-a) >= 10.0)
if abs(e2e) <= 6.0 and p2p <= 6.0 and jumps == 0:
    v = "PASS"
elif abs(e2e) <= 6.0 and p2p <= 9.0 and jumps == 0:
    v = "MARGINAL"
else:
    v = "FAIL"
print("%+.1f,%.1f,%d,%s,n=%d" % (e2e, p2p, jumps, v, len(mg)))
PYEOF
)
  echo "WINDOW,$i,$(date -u +%H:%M:%S)Z,$RES"
  V=$(echo "$RES" | cut -d, -f4)
  PREV=$(cat "${PREFIX}_state" 2>/dev/null)
  if [ "$V" = "PASS" ]; then echo "GATE,LAUNCH,window=$i,clean"; rm -f "${PREFIX}_state"; exit 0; fi
  if [ "$V" = "MARGINAL" ]; then
    if [ "$PREV" = "MARGINAL" ]; then echo "GATE,LAUNCH,window=$i,marginal-confirmed"; rm -f "${PREFIX}_state"; exit 0; fi
    echo MARGINAL > "${PREFIX}_state"
  else
    rm -f "${PREFIX}_state"
  fi
done
echo "GATE,STANDDOWN,max-windows"
exit 2
