# 2026-09-09 sodium alginate Block H -- detached run, needs collection

A Block H battery (3x50 mg + 3x200 mg, frozen three-phase controller,
dose_read_path=bracket) launched detached: sodium alginate was the worst
Block-G conveyor and its Block H doses grind toward the ~900 s per-dose
timeout, exceeding the launching job's 60-min GitHub token.

- tmux session: alginate  (on this Pi)
- run dir:      ~/powder-doser/data/battery/20260909T185352Z_sodium-alginate
- console log:  ~/handoff/2026-09-09_sodium-alginate_capture_console.log
- launched:     ~18:54 UTC 2026-09-09 (12:54 MDT)
- pre-flight:   feed confirmed, 4.53 mg/rev; survey clean (100pct stable, 0.4 mg over 180 s)
- NOT uploaded (Pi has no MONGODB_URI). NOT committed to git yet.

## To collect (next @claude session, run from the RUNNER):
1. Check it finished:
     ssh Pi "tmux capture-pane -t alginate -p | tail -20"
     ssh Pi "tail -30 ~/powder-doser/data/battery/20260909T185352Z_sodium-alginate/raw_serial_sodium-alginate.log"
   Look for RUN,END,ok (and CAPTURE_EXIT=0 in the console log).
2. Pull the run dir from the Pi into the repo under data/battery/, commit and push.
3. If run.json is missing or partial (killed mid-run), rebuild on the Pi:
     ~/powder-doser-venv/bin/python scripts/powder_battery_capture.py --from-raw \
       data/battery/20260909T185352Z_sodium-alginate/raw_serial_sodium-alginate.log --powder-id sodium-alginate \
       --powder "sodium alginate" --batch food-safe-2026-08 --operator claude \
       --preflight-json /tmp/preflight_na.json
4. Upload runner-side (runner has MONGODB_URI but needs pymongo):
     pip install pymongo && python scripts/powder_battery_capture.py --upload-file <run.json>
   (Pi has pymongo but no URI; do NOT copy the secret onto the Pi.)
5. Review QC; default upload is valid=false/unreviewed. Promote with
   scripts/amend_battery_run.py if clean. Then: python scripts/build_run_log.py
