# Per-powder summary of the stepped-tilt trials on the final settings.
# Usage: gawk -f summary.awk trials.csv > summary.csv
function med(s,   n, v, i) { n = split(substr(s, 2), v, " "); if (n == 0) return ""
  for (i = 1; i <= n; i++) v[i] += 0; asort(v)
  return (n % 2) ? v[(n + 1) / 2] : (v[n / 2] + v[n / 2 + 1]) / 2 }
function mn(s,   n, v, i) { n = split(substr(s, 2), v, " "); if (!n) return ""; for (i = 1; i <= n; i++) v[i] += 0; asort(v); return v[1] }
function mx(s,   n, v, i) { n = split(substr(s, 2), v, " "); if (!n) return ""; for (i = 1; i <= n; i++) v[i] += 0; asort(v); return v[n] }
BEGIN { FS = OFS = ","
  order[1] = "alsi10mg"; order[2] = "sodium-sulfate"; order[3] = "calcium-lactate"
  order[4] = "barium-chloride"; order[5] = "xanthan-gum"; order[6] = "salt" }
NR == 1 { next }
$6 == "final" {
  p = $1; nm[p] = $2; tg[p] = $11; tr[p]++
  if ($19 == 1) { d[p]++; e = $13 + 0; err[p] = err[p] " " e; tim[p] = tim[p] " " $15
    s[p] += e; ss[p] += e * e; w1[p] += $20; w5p[p] += $21; if (e >= -5 && e <= 5) w5[p]++
    if (e > 1) ov[p]++; st[p, $16]++
    if ($18 != "") fa[p] = fa[p] " " $18; if ($17 != "") br[p] = br[p] " " $17 }
}
END {
  print "powder_id,powder,target_g,trials,doses,within_1mg,within_5mg,within_5pct,over_1mg,median_error_mg," \
        "mean_error_mg,sd_error_mg,min_error_mg,max_error_mg,median_time_s,min_time_s,max_time_s," \
        "ended_in_bulk,ended_in_fine,ended_in_tap,median_fine_afterflow_mg,median_bulk_rate_g_per_s"
  for (i = 1; i <= 6; i++) { p = order[i]; k = d[p] + 0
    if (k == 0) { print p, nm[p], tg[p], tr[p], 0, 0, 0, 0, 0, "", "", "", "", "", "", "", "", 0, 0, 0, "", ""; continue }
    m = s[p] / k; sd = (k > 1) ? sqrt((ss[p] - k * m * m) / (k - 1)) : 0
    printf "%s,%s,%s,%d,%d,%d,%d,%d,%d,%.1f,%.1f,%.1f,%.1f,%.1f,%.1f,%.1f,%.1f,%d,%d,%d,%s,%s\n", p, nm[p], tg[p], tr[p], k,
      w1[p], w5[p], w5p[p], ov[p], med(err[p]), m, sd, mn(err[p]), mx(err[p]), med(tim[p]), mn(tim[p]), mx(tim[p]),
      st[p, "bulk"], st[p, "fine"], st[p, "tap"], (fa[p] != "" ? sprintf("%.1f", med(fa[p])) : ""), (br[p] != "" ? sprintf("%.3f", med(br[p])) : "") }
}
