# Tidy table of the stepped-tilt trials: one row per trial, from the per-launch
# trials_summary.csv files in raw/ (byte-identical copies from PR #131's branch).
# Usage: gawk -f tidy.awk raw/*.csv > trials.csv
# File names are <powder_id>__<run folder>__<launch folder>__trials_summary.csv.
BEGIN {
  FPAT = "([^,]*)|(\"[^\"]*\")"; OFS = ","
  name["salt"] = "NaCl"; name["alsi10mg"] = "AlSi10Mg"
  name["calcium-lactate"] = "Calcium lactate"; name["barium-chloride"] = "Barium chloride"
  name["sodium-sulfate"] = "Sodium sulfate"; name["xanthan-gum"] = "Xanthan gum"
  grp["salt"] = "surrogate"; grp["calcium-lactate"] = "surrogate"; grp["xanthan-gum"] = "surrogate"
  grp["alsi10mg"] = "research"; grp["barium-chloride"] = "research"; grp["sodium-sulfate"] = "research"
  # Plot rows, top to bottom by mass per auger revolution in protocol C (Fig. 6a).
  row["alsi10mg"] = 6; row["sodium-sulfate"] = 5; row["calcium-lactate"] = 4
  row["barium-chloride"] = 3; row["xanthan-gum"] = 2; row["salt"] = 1
  print "powder_id,powder,group,run,launch,protocol,trial,date_utc,start_utc,status,target_g,final_g," \
        "error_mg,error_pct,dose_s,end_stage,bulk_rate_g_per_s,fine_afterflow_mg,dose_completed," \
        "within_1mg,within_5pct,plot_row,plot_y,plot_x_symlog"
}
FNR == 1 { next }
{
  split(FILENAME, a, "/"); fn = a[length(a)]; split(fn, p, "__")
  pid = p[1]; run = p[2]; launch = p[3]
  # Runs on the final settings (script versions 19d, 19e and 20a-20e); the
  # earlier salt runs (18a-19c) were protocol development.
  final = (run ~ /old-auger-80rpm|alsi10mg|calcium-lactate|barium-chloride|sodium-sulfate|xanthan-gum/)
  status = $7; target = $8 + 0; e = $10 + 0
  done = (status == "ok" || status == "overshoot")
  stage = ($15 != "") ? "tap" : (($14 != "") ? "fine" : "bulk")
  lim = 0.05 * target * 1000
  w1 = (done && e >= -1 && e <= 1) ? 1 : 0
  w5 = (done && e >= -lim && e <= lim) ? 1 : 0
  # Deterministic jitter within the row from the trial number (golden-ratio sequence).
  tr = $2 + 0; if (launch ~ /^launch2/ && pid != "alsi10mg") tr += 40
  jit = (tr * 0.6180339887) - int(tr * 0.6180339887)
  y = row[pid] + 0.56 * (jit - 0.5)
  xs = (e >= 0 ? 1 : -1) * log(1 + (e < 0 ? -e : e)) / log(10)
  epct = (target > 0) ? 100 * e / (1000 * target) : ""
  print pid, name[pid], grp[pid], run, launch, (final ? "final" : "development"), $2, $3, $4, status, \
        $8, $9, $10, sprintf("%.2f", epct), $12, (done ? stage : ""), $19, $22, done, w1, w5, \
        row[pid], sprintf("%.3f", y), sprintf("%.4f", xs)
}
