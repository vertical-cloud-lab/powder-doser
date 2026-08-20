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


def main():
    test_adjacent_dose_labels_differ()
    test_stagger_holds_across_powders()
    test_offset_cycle_alternates()
    test_feed_factor_labels_are_rotated()
    test_legend_headroom_grows_with_the_powder_count()
    if FAILURES:
        print("\n{} check(s) failed: {}".format(len(FAILURES),
                                                ", ".join(FAILURES)))
        return 1
    print("\nall checks passed")
    return 0


if __name__ == "__main__":
    sys.exit(main())
