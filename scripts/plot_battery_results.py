#!/usr/bin/env python3
"""Results figure for a uniform powder-battery run that actually fed.

Companion to ``plot_battery_run.py``, which is the *did it feed at all?*
diagnostic.  This one is the four-panel per-powder result used in the
manuscript (PR #97):

  A  block C -- mass per 360 deg auger revolution vs tilt, with SEM
  B  block D -- mass-vs-time traces at each auger speed (pulsation)
  C  block E -- mg per tap vs the measured re-feed rotation, per tilt
  D  block G -- closed-loop 1 g doses against the target

Usage::

    python scripts/plot_battery_results.py \
        data/battery/<stamp>_<powder-id>/run_<powder-id>.json \
        data/battery/<stamp>_<powder-id>/<powder-id>_results.png
"""

import json
import sys

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

# Reference palette (dataviz skill), light surface.
SURFACE = "#fcfcfb"
TEXT_PRIMARY = "#0b0b0b"
TEXT_SECONDARY = "#52514e"
GRID = "#dcdbd6"
# Categorical slots 1-3: the trio validated all-pairs for CVD.
SERIES = ["#2a78d6", "#eb6834", "#1baf7a"]
NOISE = "#9d9c95"
TARGET = "#e34948"


def summary_rows(doc, block, phase=None):
    rows = [r for r in doc["host_summary"] if r["block"] == block
            and (phase is None or r["phase"] == phase)]
    rows.sort(key=lambda r: r["tilt_deg"])
    return rows


def baseline_noise(doc):
    """Largest |delta| seen in block A -- the no-actuation noise floor."""
    deltas = [abs(t["delta_g"]) for t in doc["trials"] if t["block"] == "A"]
    return max(deltas) if deltas else 0.0


def style(ax):
    ax.set_facecolor(SURFACE)
    for side in ("top", "right"):
        ax.spines[side].set_visible(False)
    for side in ("left", "bottom"):
        ax.spines[side].set_color(GRID)
    ax.tick_params(colors=TEXT_SECONDARY, labelsize=9, length=3)
    ax.yaxis.grid(True, color=GRID, linewidth=0.8)
    ax.set_axisbelow(True)


# The balance displays to 0.1 mg, so a per-revolution mean at or under
# half a display count is "not detected", not a small measurement.
RESOLUTION_MG = 0.1
DETECTION_MG = RESOLUTION_MG / 2.0


def tilt_headline(rows, doc=None):
    """Describe the block C trend, which is not always a rise.

    White rice flour climbs ~10x from tilt 0 to 90 deg, sodium alginate
    saturates above 45 deg, brown rice flour is flat within its own
    scatter, and carboxymethyl cellulose peaks at 45 deg and falls again
    -- so state which of those this run is.

    A trend also needs two numbers to trend *between*.  Silicon -325
    returned exactly 0.0000 g on all twelve revolutions at 0 and 45 deg
    and a single isolated 7.2 mg event at 90 deg; the ratio test happily
    called that "feed factor rises with tilt", which asserts a tilt
    dependence out of two non-detections.  Tilts at or below the balance's
    detection limit are therefore reported as such instead of being
    treated as small measurements -- the same rule panel A's bars already
    follow, and the third repair to this function's habit of claiming
    more than the data carries.

    ``DETECTION_MG`` alone is not that rule, though: it is the balance's
    *display* resolution, and on a disturbed bench a tilt mean can clear
    it by two orders of magnitude and still be indistinguishable from
    zero.  Fumed silica read 2.5 / 2.7 / 5.6 mg per revolution with
    standard errors of 5.7 / 5.8 / 4.1 mg -- every mean inside one
    standard error of zero, several individual revolutions negative --
    and this function called it "feed factor rises with tilt".  A tilt
    now counts as detected only when its mean also clears twice its own
    standard error and the block A no-actuation spread, which is the same
    evidence ``tap_headline`` already demands.
    """
    values = [r["mean_g"] * 1000.0 for r in rows]
    if len(values) < 2 or max(values) <= 0:
        return "feed factor vs tilt"
    baseline = baseline_spread_mg(doc) if doc else 0.0

    def resolved(row, value):
        sem = abs(row.get("sem_g") or 0.0) * 1000.0
        return (value > DETECTION_MG
                and value >= 2 * sem
                and (baseline < 1.0 or value >= baseline))

    undetected = [r for r, v in zip(rows, values) if not resolved(r, v)]
    if len(undetected) == len(values):
        return "feed factor not resolved above the noise floor at any tilt"
    if undetected:
        detected = [(r, v) for r, v in zip(rows, values) if resolved(r, v)]
        where = ", ".join("{:.0f}°".format(r["tilt_deg"]) for r in undetected)
        shown = ", ".join("{:.0f}° {:.1f}".format(r["tilt_deg"], v)
                          for r, v in detected)
        return ("feed factor not resolved at {} ({} mg/rev)".format(
            where, shown))
    ratio = max(values) / max(min(values), 1e-9)
    if ratio < 2.0:
        return "feed factor is flat across tilt"
    peak = values.index(max(values))
    if 0 < peak < len(values) - 1:
        # Non-monotonic: an interior tilt beats both ends.  Saying
        # "rises with tilt" here would invert the result.
        return "feed factor peaks at {:.0f}° and falls above it".format(
            rows[peak]["tilt_deg"])
    if peak == 0:
        return "feed factor falls with tilt"
    # Rising.  Saturation means the last two are within ~33 % of each
    # other; a one-sided test calls a *drop* saturation.
    if len(values) >= 3 and values[-1] > 0 and 0.75 <= values[-2] / values[-1]:
        return "feed factor rises with tilt, saturating above 45°"
    return "feed factor rises with tilt"


def panel_rotation(ax, doc):
    """Block C: mg per revolution vs tilt."""
    rows = summary_rows(doc, "C")
    xs = range(len(rows))
    values = [r["mean_g"] * 1000.0 for r in rows]
    errors = [(r["sem_g"] or 0.0) * 1000.0 for r in rows]
    noise_mg = baseline_noise(doc) * 1000.0

    ax.bar(xs, values, width=0.55, color=SERIES[0], yerr=errors,
           ecolor=TEXT_SECONDARY, capsize=4, error_kw={"linewidth": 1.2})
    if noise_mg > 0:
        ax.axhline(noise_mg, color=NOISE, linewidth=2, linestyle=(0, (4, 3)))
    for x, value, error, row in zip(xs, values, errors, rows):
        ax.annotate("{:.1f}\nRSD {:.0f}%".format(value, row["rsd_pct"] or 0),
                    xy=(x, value + error), xytext=(0, 8),
                    textcoords="offset points", ha="center", fontsize=8.5,
                    color=TEXT_PRIMARY)
    ax.set_xticks(list(xs))
    ax.set_xticklabels(["{:.0f}°".format(r["tilt_deg"]) for r in rows])
    ax.set_xlabel("tube tilt (0° horizontal, 90° vertical)",
                  fontsize=9.5, color=TEXT_SECONDARY)
    ax.set_ylabel("mass per 360° revolution (mg)", fontsize=9.5,
                  color=TEXT_SECONDARY)
    ax.set_ylim(0, max(values) * 1.45 if values else 1)
    ax.set_title("A  Block C — {} (n=6 each, 30 RPM)".format(
                     tilt_headline(rows, doc)),
                 fontsize=10.5, color=TEXT_PRIMARY, loc="left", pad=10)


def panel_speed(ax, doc):
    """Block D: mass-vs-time trace at each auger speed."""
    polls = [p for p in doc["polls"] if p["block"] == "D"]
    rpms = sorted({p["rpm"] for p in polls})
    for i, rpm in enumerate(rpms):
        trace = [p for p in polls if p["rpm"] == rpm]
        if not trace:
            continue
        t0 = trace[0]["t_ms"]
        g0 = trace[0]["grams"]
        ax.plot([(p["t_ms"] - t0) / 1000.0 for p in trace],
                [(p["grams"] - g0) * 1000.0 for p in trace],
                color=SERIES[i % len(SERIES)], linewidth=2,
                marker="o", markersize=4.5, markeredgecolor=SURFACE,
                markeredgewidth=1.2,
                label="{:.0f} RPM".format(rpm))
        ax.annotate("{:.0f} RPM".format(rpm),
                    xy=((trace[-1]["t_ms"] - t0) / 1000.0,
                        (trace[-1]["grams"] - g0) * 1000.0),
                    xytext=(5, -2), textcoords="offset points",
                    fontsize=8.5, color=TEXT_SECONDARY)
    ax.set_xlabel("time within the 3-revolution burst (s)", fontsize=9.5,
                  color=TEXT_SECONDARY)
    ax.set_ylabel("delivered mass (mg)", fontsize=9.5,
                  color=TEXT_SECONDARY)
    ax.set_title("B  Block D — mass vs time at each auger speed "
                 "(tilt 45°)", fontsize=10.5, color=TEXT_PRIMARY,
                 loc="left", pad=10)
    legend = ax.legend(frameon=False, fontsize=9, loc="lower right")
    for text in legend.get_texts():
        text.set_color(TEXT_SECONDARY)


def baseline_spread_mg(doc):
    """Block A's no-actuation scatter, in mg -- what nothing at all looks like.

    On a quiet bench this is zero to the balance's display resolution.  In a
    disturbed room the same eight do-nothing trials can spread over tens of
    mg, and any per-action quantum smaller than that is a description of the
    room rather than of the powder.
    """
    for row in doc.get("host_summary") or []:
        if row["block"] == "A" and row.get("std_g") is not None:
            return abs(row["std_g"]) * 1000.0
    return 0.0


def tap_headline(taps, doc=None, refeeds=None):
    """Describe what tapping did, rather than assuming it did nothing.

    Every powder through sodium alginate moved <0.3 mg per tap, but calcium
    lactate moves ~20 mg, so the panel title has to follow the data.  The
    1 mg floor is a few times the balance's 0.1 mg display resolution.

    A mean alone is not enough, though.  Sodium sulfate's taps averaged 9 mg
    in a room whose *no-actuation* block A trials scattered over 23 mg, so
    "moves up to 9 mg per tap" would have been a statement about bench
    disturbance.  A quantum is only claimed when it clears both block A's
    spread and twice its own standard error.

    Block A's spread is checked *first*, because "contributes almost
    nothing" is itself a claim about the powder and needs the same
    evidence.  Silicon's taps averaged -3.5 mg against a 20 mg block A
    spread: the room moved the balance further than a tap did, so those
    trials bound the quantum at nothing at all -- a real 15 mg quantum
    would have looked the same.  On a quiet bench (block A at the display
    resolution) a sub-mg mean does bound the quantum, and "almost
    nothing" stands -- hence the 1 mg materiality guard, without which a
    quiet run whose taps average -0.04 mg would trip the same branch.

    Clearing the noise is necessary but not sufficient, because noise is
    not the only thing that is not powder.  A tap can only dislodge what
    rotation has already carried to the delivery lip, so a tap quantum
    larger than the re-feed rotation measured *in the same trials, at the
    same tilt* is mechanically impossible and is something else -- on
    2026-08-21 fumed silica's tilt 0 deg taps read 32.2 mg against a
    -8.9 mg re-feed rotation, every trial flagged as a shock, which was
    the tap solenoid's impulse coupling into the load cell.  That passed
    both noise tests comfortably.  So the largest claimable quantum is
    capped by its own tilt's re-feed rotation.
    """
    means = [r["mean_g"] * 1000.0 for r in taps] or [0.0]
    if refeeds:
        by_tilt = {r["tilt_deg"]: r["mean_g"] * 1000.0 for r in refeeds}
        credible = [m for r, m in zip(taps, means)
                    if m <= by_tilt.get(r["tilt_deg"], float("inf"))]
        if not credible:
            return "tap exceeds its own re-feed rotation (not powder)"
        means = credible
    peak = max(means)
    sems = [abs(r.get("sem_g") or 0.0) * 1000.0 for r in taps] or [0.0]
    baseline = baseline_spread_mg(doc) if doc else 0.0
    if baseline >= 1.0 and peak < baseline:
        return "tap quantum not resolved above the no-actuation baseline"
    if peak < 1.0:
        return "tapping contributes almost nothing"
    if peak < 2 * max(sems):
        return "tap quantum not resolved above the no-actuation baseline"
    return "tapping moves up to {:.0f} mg per tap".format(peak)


def dose_headline(doses):
    """Describe how the closed-loop doses ended, from the doses.

    A dose can converge, exhaust the fine-phase cycle budget, or stall;
    when it stalls, the phase it stalled *in* is the useful detail, so
    read it off the last entry of ``phase_cycles``.
    """
    if not doses:
        return "no closed-loop doses"
    statuses = {d["status"] for d in doses}
    if statuses == {"ok"}:
        return "three-phase doses converge within tolerance"
    if statuses == {"cycle-budget"}:
        return "three-phase doses run out of fine-phase budget"
    if statuses == {"stalled"}:
        phases = {d.get("phase_cycles", "").split(";")[-1].split(":")[0]
                  for d in doses}
        if len(phases) == 1:
            phase = phases.pop()
            if phase:
                return "three-phase doses stall in the {} phase".format(phase)
        return "three-phase doses stall short of the target"
    return "three-phase doses vs the target"


def panel_tap(ax, doc):
    """Block E: tap quantum against the re-feed rotation, per tilt."""
    taps = summary_rows(doc, "E", "tap")
    refeeds = summary_rows(doc, "E", "refeed")
    tilts = [r["tilt_deg"] for r in taps]
    xs = range(len(tilts))
    width = 0.36

    for offset, rows, label, color in (
            (-width / 2, refeeds, "360° re-feed rotation", SERIES[0]),
            (+width / 2, taps, "single tap", SERIES[1])):
        values = [r["mean_g"] * 1000.0 for r in rows]
        errors = [(r["sem_g"] or 0.0) * 1000.0 for r in rows]
        ax.bar([x + offset for x in xs], values, width=width - 0.02,
               color=color, yerr=errors, ecolor=TEXT_SECONDARY,
               capsize=4, error_kw={"linewidth": 1.2}, label=label)
        for x, value in zip(xs, values):
            ax.annotate("{:.2f}".format(value), xy=(x + offset, value),
                        xytext=(0, 5), textcoords="offset points",
                        ha="center", fontsize=8.5, color=TEXT_PRIMARY)
    ax.set_xticks(list(xs))
    ax.set_xticklabels(["{:.0f}°".format(t) for t in tilts])
    ax.set_xlabel("tube tilt", fontsize=9.5, color=TEXT_SECONDARY)
    ax.set_ylabel("mass per action (mg)", fontsize=9.5,
                  color=TEXT_SECONDARY)
    ax.set_title("C  Block E — {} (n=8 each)".format(
        tap_headline(taps, doc, refeeds)),
                 fontsize=10.5, color=TEXT_PRIMARY, loc="left", pad=10)
    legend = ax.legend(frameon=False, fontsize=9, loc="upper left")
    for text in legend.get_texts():
        text.set_color(TEXT_SECONDARY)


def panel_dose(ax, doc):
    """Block G: closed-loop doses against the target."""
    doses = doc["doses"]
    xs = range(len(doses))
    values = [d["dispensed_g"] for d in doses]
    target = doses[0]["target_g"] if doses else 1.0

    ax.bar(xs, values, width=0.5, color=SERIES[0])
    ax.axhline(target, color=TARGET, linewidth=2, linestyle=(0, (4, 3)))
    ax.annotate("target {:.3f} g".format(target), xy=(-0.45, target),
                xytext=(0, 6), textcoords="offset points", ha="left",
                fontsize=8.5, color=TEXT_SECONDARY)
    for x, dose in zip(xs, doses):
        ax.annotate("{:.4f} g\n({:+.3f} g)\n{}".format(
                        dose["dispensed_g"], dose["error_g"],
                        dose["status"]),
                    xy=(x, dose["dispensed_g"]), xytext=(0, -46),
                    textcoords="offset points", ha="center", fontsize=8.5,
                    color="#ffffff")
    ax.set_xticks(list(xs))
    ax.set_xticklabels(["dose {}\n{:.0f} s".format(d["n"] + 1, d["elapsed_s"])
                        for d in doses], fontsize=9)
    ax.set_ylabel("delivered mass (g)", fontsize=9.5,
                  color=TEXT_SECONDARY)
    ax.set_ylim(0, max(values + [target]) * 1.2)
    ax.set_title("D  Block G — {}".format(dose_headline(doses)),
                 fontsize=10.5, color=TEXT_PRIMARY, loc="left", pad=10)


def main(path, out_path):
    doc = json.load(open(path))
    powder = doc.get("powder") or doc["powder_id"]

    fig, axes = plt.subplots(2, 2, figsize=(12.6, 8.6), facecolor=SURFACE)
    for ax in axes.flat:
        style(ax)

    panel_rotation(axes[0][0], doc)
    panel_speed(axes[0][1], doc)
    panel_tap(axes[1][0], doc)
    panel_dose(axes[1][1], doc)

    fig.suptitle(
        "{} — uniform powder battery, {}Z".format(
            powder, doc["started_utc"][:19].replace("T", " ")),
        fontsize=13, color=TEXT_PRIMARY, x=0.008, ha="left", y=0.985)
    fig.tight_layout(rect=(0, 0, 1, 0.955))
    fig.savefig(out_path, dpi=170, facecolor=SURFACE)
    print("wrote", out_path)


if __name__ == "__main__":
    run_json = sys.argv[1]
    out = sys.argv[2] if len(sys.argv) > 2 else "battery_results.png"
    main(run_json, out)
