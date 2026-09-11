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

    def bar(self, *args, **kwargs):
        pass

    def axhline(self, *args, **kwargs):
        pass

    def annotate(self, text, xy=None, xytext=(0, 0), **kwargs):
        self.annotations.append((text, xy, xytext))

    def set_xticks(self, *args, **kwargs):
        pass

    def set_xticklabels(self, *args, **kwargs):
        pass

    def set_ylabel(self, *args, **kwargs):
        pass

    def set_ylim(self, *args, **kwargs):
        pass

    def set_title(self, *args, **kwargs):
        pass


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


def main():
    test_adjacent_dose_labels_differ()
    test_stagger_holds_across_powders()
    test_offset_cycle_alternates()
    if FAILURES:
        print("\n{} check(s) failed: {}".format(len(FAILURES),
                                                ", ".join(FAILURES)))
        return 1
    print("\nall checks passed")
    return 0


if __name__ == "__main__":
    sys.exit(main())
