#!/usr/bin/env python3
"""Checks that the cross-powder dose panel stays readable.

Panel B prints the delivered mass above every bar.  Three doses of the
same powder land within a few mg of each other, so at the 2026-08-06 salt
run the labels collided into an unreadable run of digits --
``0.9950.9971.009`` for salt, ``0.9850.9650.971`` for calcium lactate.
The fix alternates the vertical offset within each powder's group; these
tests pin that so the panel cannot silently become illegible again as
more powders are added.

No plotting: ``panel_dose`` is driven against a recording stub.

Usage::

    python scripts/tests/test_plot_battery_compare.py
"""

import json
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                os.pardir))

import plot_battery_compare as cmp  # noqa: E402

FAILURES = []


def check(name, condition, detail=""):
    if condition:
        print("PASS {} {}".format(name, detail))
    else:
        FAILURES.append(name)
        print("FAIL {} {}".format(name, detail))


class FakeAxis(object):
    """Records only what the label-collision checks need."""

    def __init__(self):
        self.annotations = []
        self.annotation_kwargs = []
        self.ylim = (1.0, 1000.0)

    def bar(self, *args, **kwargs):
        pass

    def axhline(self, *args, **kwargs):
        pass

    def annotate(self, text, xy=None, xytext=(0, 0), **kwargs):
        self.annotations.append((text, xy, xytext))
        self.annotation_kwargs.append(kwargs)

    def set_xticks(self, *args, **kwargs):
        pass

    def set_xticklabels(self, *args, **kwargs):
        pass

    def set_xlabel(self, *args, **kwargs):
        pass

    def set_ylabel(self, *args, **kwargs):
        pass

    def set_yscale(self, *args, **kwargs):
        pass

    def get_ylim(self):
        return self.ylim

    def set_ylim(self, *args, **kwargs):
        if len(args) == 2:
            self.ylim = (args[0], args[1])

    def legend(self, *args, **kwargs):
        return FakeLegend()

    def set_title(self, *args, **kwargs):
        pass


class FakeLegend:
    def get_texts(self):
        return []


def doc(powder_id, dispensed, status="ok"):
    return {
        "powder_id": powder_id,
        "powder": powder_id,
        "started_utc": "2026-08-06T14:51:20Z",
        "doses": [{"n": i, "target_g": 1.0, "dispensed_g": g,
                   "status": status}
                  for i, g in enumerate(dispensed)],
    }


def value_labels(ax):
    """Bar value annotations: (x, value-as-drawn, vertical offset)."""
    out = []
    for text, xy, xytext in ax.annotations:
        # Value labels are the ones anchored at a bar's height; the target
        # line and the group captions are anchored at the axis extremes.
        if text.startswith("0.") or text.startswith("1."):
            out.append((xy[0], text, xytext[1]))
    return out


def test_adjacent_dose_labels_differ():
    """Two neighbouring bars must never share a label baseline."""
    ax = FakeAxis()
    # The real salt run: three doses inside 14 mg of each other.
    cmp.panel_dose(ax, [doc("salt", [0.9953, 0.9965, 1.0088])])
    labels = sorted(value_labels(ax))
    check("salt: three labels drawn", len(labels) == 3,
          "got {}".format(len(labels)))
    offsets = [dy for _, _, dy in labels]
    check("salt: adjacent offsets differ",
          all(a != b for a, b in zip(offsets, offsets[1:])),
          "offsets {}".format(offsets))


def test_stagger_holds_across_powders():
    """Every powder in the real dataset, not just the one that broke."""
    docs = [
        doc("white-rice-flour", [0.8597, 0.8399, 0.8868], "cycle-budget"),
        doc("calcium-lactate", [0.9846, 0.9654, 0.9705], "stalled"),
        doc("xanthan-gum", [0.9564, 0.9699, 0.9750], "stalled"),
        doc("salt", [0.9953, 0.9965, 1.0088]),
    ]
    ax = FakeAxis()
    cmp.panel_dose(ax, docs)
    labels = sorted(value_labels(ax))
    check("all doses labelled", len(labels) == 12,
          "got {}".format(len(labels)))
    bad = [(a, b) for a, b in zip(labels, labels[1:])
           if abs(a[0] - b[0]) < 1.01 and a[2] == b[2]]
    check("no adjacent pair shares a baseline", not bad, "{}".format(bad))


def test_offset_cycle_alternates():
    check("cycle has at least two distinct offsets",
          len(set(cmp.DOSE_LABEL_DY)) > 1,
          "{}".format(cmp.DOSE_LABEL_DY))
    check("cycle alternates",
          all(a != b for a, b in zip(cmp.DOSE_LABEL_DY,
                                     cmp.DOSE_LABEL_DY[1:])),
          "{}".format(cmp.DOSE_LABEL_DY))
    check("offsets clear the bar top", min(cmp.DOSE_LABEL_DY) > 0,
          "{}".format(cmp.DOSE_LABEL_DY))


def rotation_doc(powder_id, per_tilt):
    """A run document with just enough block C rows for panel A."""
    return {
        "powder_id": powder_id,
        "powder": powder_id,
        "started_utc": "2026-08-20T21:48:23Z",
        "host_summary": [
            {"block": "C", "phase": "rotation", "tilt_deg": tilt,
             "mean_g": mg / 1000.0, "sem_g": 0.0, "rsd_pct": 5.0}
            for tilt, mg in per_tilt.items()
        ],
    }


def test_feed_factor_labels_are_rotated():
    """Ten powders per tilt group: a horizontal label is wider than its bar.

    Before this, neighbouring labels merged into digit soup
    ("34.351.257.2" at tilt 0 deg).  Staggering the offset was not enough
    -- it is measured from each bar's own top, so two similarly tall bars
    stagger onto each other anyway.  Rotation is what actually bounds a
    label's width, so it is the thing worth pinning.
    """
    # The real 2026-08-20 dataset, whose tilt-90 group is the tight one.
    real = [("white-rice-flour", 37.2), ("sodium-alginate", 10.9),
            ("brown-rice-flour", 0.2), ("calcium-lactate", 232.2),
            ("carboxymethyl-cellulose", 9.3), ("xanthan-gum", 186.8),
            ("salt-0806", 24.9), ("salt-0812", 230.4),
            ("sodium-sulfate", 243.6), ("silicon-110-200", 302.4)]
    docs = [rotation_doc(name, {0.0: mg / 5.0, 45.0: mg * 0.7, 90.0: mg})
            for name, mg in real]
    ax = FakeAxis()
    cmp.panel_feed_factor(ax, docs)
    bar_labels = [(t, kw) for (t, _, _), kw
                  in zip(ax.annotations, ax.annotation_kwargs)
                  if not t.startswith("balance resolution")]
    check("every bar is labelled", len(bar_labels) == 30,
          "got {}".format(len(bar_labels)))
    unrotated = [t for t, kw in bar_labels if kw.get("rotation") != 90]
    check("every value label is rotated", not unrotated,
          "{}".format(unrotated[:4]))
    check("rotated labels sit on their bar top",
          all(kw.get("va") == "bottom" for _, kw in bar_labels))


def test_legend_headroom_grows_with_the_powder_count():
    """The legend must not land on a rotated label, which is ~5x taller."""
    few = FakeAxis()
    cmp.panel_feed_factor(few, [rotation_doc("salt", {0.0: 5.0, 90.0: 25.0})])
    many = FakeAxis()
    cmp.panel_feed_factor(many, [
        rotation_doc("p{}".format(i), {0.0: 5.0, 90.0: 25.0})
        for i in range(10)])
    check("more powders means more headroom", many.ylim[1] > few.ylim[1],
          "{} vs {}".format(many.ylim[1], few.ylim[1]))
    check("headroom clears the tallest bar", many.ylim[1] > 1000.0,
          "{}".format(many.ylim[1]))



# --- palette -------------------------------------------------------------
#
# The palette grew one slot at a time as powders were added, and it has
# already failed silently once: at five powders the fifth wore the same
# blue as the first, so two powders were one series on the page and
# nobody noticed until the figure was read closely.  A comment saying
# "validated" does not stop that recurring, so the separation is asserted
# here instead -- every pair, in normal vision and under simulated
# deuteranopia and protanopia, plus contrast against the plotting
# surface and against the reserved TARGET red.


def _srgb_to_linear(channel):
    if channel <= 0.04045:
        return channel / 12.92
    return ((channel + 0.055) / 1.055) ** 2.4


def _rgb(hex_colour):
    raw = hex_colour.lstrip("#")
    return tuple(int(raw[i:i + 2], 16) / 255.0 for i in (0, 2, 4))


def _relative_luminance(hex_colour):
    r, g, b = [_srgb_to_linear(c) for c in _rgb(hex_colour)]
    return 0.2126 * r + 0.7152 * g + 0.0722 * b


def _contrast(a, b):
    high, low = sorted([_relative_luminance(a), _relative_luminance(b)],
                       reverse=True)
    return (high + 0.05) / (low + 0.05)


def _lab(hex_colour):
    r, g, b = [_srgb_to_linear(c) * 100.0 for c in _rgb(hex_colour)]
    x = (r * 0.4124 + g * 0.3576 + b * 0.1805) / 95.047
    y = (r * 0.2126 + g * 0.7152 + b * 0.0722) / 100.0
    z = (r * 0.0193 + g * 0.1192 + b * 0.9505) / 108.883

    def f(t):
        return t ** (1.0 / 3.0) if t > 0.008856 else (7.787 * t + 16.0 / 116)

    fx, fy, fz = f(x), f(y), f(z)
    return (116 * fy - 16, 500 * (fx - fy), 200 * (fy - fz))


def _delta_e(a, b):
    return sum((x - y) ** 2 for x, y in zip(_lab(a), _lab(b))) ** 0.5


def _simulate_cvd(hex_colour, kind):
    """Brettel/Vienot-style dichromat approximation (LMS projection)."""
    r, g, b = [_srgb_to_linear(c) for c in _rgb(hex_colour)]
    long_ = 17.8824 * r + 43.5161 * g + 4.11935 * b
    med = 3.45565 * r + 27.1554 * g + 3.86714 * b
    short = 0.0299566 * r + 0.184309 * g + 1.46709 * b
    if kind == "deuteranopia":
        med = 0.494207 * long_ + 1.24827 * short
    elif kind == "protanopia":
        long_ = 2.02344 * med - 2.52581 * short
    else:
        raise ValueError(kind)
    out = (0.080944 * long_ - 0.130504 * med + 0.116721 * short,
           -0.0102485 * long_ + 0.0540194 * med - 0.113615 * short,
           -0.000365294 * long_ - 0.00412163 * med + 0.693513 * short)

    def encode(channel):
        channel = max(0.0, min(1.0, channel))
        if channel <= 0.0031308:
            channel *= 12.92
        else:
            channel = 1.055 * channel ** (1 / 2.4) - 0.055
        return int(round(255 * max(0.0, min(1.0, channel))))

    return "#%02x%02x%02x" % tuple(encode(c) for c in out)


# What the palette actually promises, and what it does not.
#
# Separation is asserted for *adjacent* slots, because that is the
# design: in a grouped bar chart the bars that touch are consecutive
# powders, and every bar additionally carries a direct value label.
# Non-adjacent pairs are deliberately not held to the same bar -- the
# orange/olive and blue/purple pairs sit closer than this under
# simulated dichromacy and always have.
#
# The absolute numbers depend on the dichromat model, so these floors
# are set from the model in this file with headroom, not copied from the
# module docstring (which was measured with a different simulation).
# Measured here at eleven slots: worst adjacent dE 22.0 normal, 12.6
# deuteranopia, 13.1 protanopia -- all at the newest pair, slate against
# teal.
MIN_ADJACENT_DELTA_E_NORMAL = 18.0
MIN_ADJACENT_DELTA_E_CVD = 9.0

# Two slots sit under the 3:1 surface-contrast guideline and always
# have; the direct bar labels carry them.  Pinned by value so a *new*
# slot cannot quietly join them.
KNOWN_LOW_CONTRAST = {"#1baf7a", "#e87ba4"}


def _adjacent_pairs():
    return [(i, i + 1) for i in range(len(cmp.SERIES) - 1)]


def test_no_two_series_colours_are_identical():
    """The failure this palette actually had: a fifth powder repainted
    the same blue as the first, so two powders were one series."""
    check("no two series colours are the same",
          len(set(cmp.SERIES)) == len(cmp.SERIES),
          "{} slots, {} distinct".format(len(cmp.SERIES),
                                         len(set(cmp.SERIES))))


def test_adjacent_series_colours_are_distinguishable():
    worst = min((_delta_e(cmp.SERIES[i], cmp.SERIES[j]), i, j)
                for i, j in _adjacent_pairs())
    check("adjacent slots separated in normal vision",
          worst[0] >= MIN_ADJACENT_DELTA_E_NORMAL,
          "worst dE {:.1f} between slots {} and {}".format(*worst))
    for kind in ("deuteranopia", "protanopia"):
        worst = min((_delta_e(_simulate_cvd(cmp.SERIES[i], kind),
                              _simulate_cvd(cmp.SERIES[j], kind)), i, j)
                    for i, j in _adjacent_pairs())
        check("adjacent slots separated under {}".format(kind),
              worst[0] >= MIN_ADJACENT_DELTA_E_CVD,
              "worst dE {:.1f} between slots {} and {}".format(*worst))


def test_no_new_slot_joins_the_low_contrast_exceptions():
    low = {colour for colour in cmp.SERIES
           if _contrast(colour, cmp.SURFACE) < 3.0}
    check("only the documented slots sit under 3:1",
          low == KNOWN_LOW_CONTRAST,
          "under 3:1: {}".format(sorted(low) or "none"))


def test_no_series_colour_wears_the_reserved_target_red():
    nearest = min((_delta_e(colour, cmp.TARGET), colour)
                  for colour in cmp.SERIES)
    check("no series colour is confusable with the TARGET red",
          nearest[0] >= MIN_ADJACENT_DELTA_E_NORMAL,
          "nearest dE {:.1f} ({})".format(*nearest))


def test_palette_covers_every_valid_run_in_the_repo():
    """The cycle warning exists, but it should not be firing in practice."""
    here = os.path.dirname(os.path.abspath(__file__))
    battery = os.path.join(here, os.pardir, os.pardir, "data", "battery")
    if not os.path.isdir(battery):
        print("SKIP palette covers every valid run (no data/battery)")
        return
    valid = 0
    for entry in sorted(os.listdir(battery)):
        path = os.path.join(battery, entry)
        if not os.path.isdir(path):
            continue
        for name in os.listdir(path):
            if not (name.startswith("run_") and name.endswith(".json")):
                continue
            with open(os.path.join(path, name)) as handle:
                run_doc = json.load(handle)
            qc = run_doc.get("qc") or {}
            if qc.get("valid_for_cross_powder_comparison"):
                valid += 1
    check("palette has a slot for every valid run",
          valid <= len(cmp.SERIES),
          "{} valid run(s), {} slots".format(valid, len(cmp.SERIES)))


def main():
    test_adjacent_dose_labels_differ()
    test_stagger_holds_across_powders()
    test_offset_cycle_alternates()
    test_feed_factor_labels_are_rotated()
    test_legend_headroom_grows_with_the_powder_count()
    test_no_two_series_colours_are_identical()
    test_adjacent_series_colours_are_distinguishable()
    test_no_new_slot_joins_the_low_contrast_exceptions()
    test_no_series_colour_wears_the_reserved_target_red()
    test_palette_covers_every_valid_run_in_the_repo()
    if FAILURES:
        print("\n{} check(s) failed: {}".format(len(FAILURES),
                                                ", ".join(FAILURES)))
        return 1
    print("\nall checks passed")
    return 0


if __name__ == "__main__":
    sys.exit(main())
