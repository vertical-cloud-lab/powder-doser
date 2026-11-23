#!/usr/bin/env python3
"""Crop the key figures of El Kassem et al. (2021), KONA 38:235-250 (CC BY 4.0), from the PDF read through the Pi.

Usage:  python extract_figures.py [/tmp/kona/pdf/elkassem2021_kona.pdf]
Writes figures/elkassem2021_kona_<fig>.png at 200 dpi. Boxes are PDF points (x0, y0, x1, y1) on the printed page.
The PDF itself is not committed; manifest.json has its URL, size and sha256.
"""
from __future__ import annotations

import sys
from pathlib import Path

import pymupdf

HERE = Path(__file__).resolve().parent
PDF = Path(sys.argv[1] if len(sys.argv) > 1 else "/tmp/kona/pdf/elkassem2021_kona.pdf")
CROPS = {  # name: (page, box, caption as printed)
    "fig01-02_auger_and_setup": (4, (50, 378, 293, 776),
                                 "Fig. 1 auger geometry; Fig. 2 experimental setup (CAD and lab)"),
    "fig03_calibration_flowchart": (5, (50, 572, 548, 773), "Fig. 3 general flowchart of the calibration process"),
    "fig07_adjusted_responses": (9, (50, 54, 548, 333),
                                 "Fig. 7 adjusted response of AoR, BD, mass flow and kinetic energy to the four inputs"),
    "fig12_predicted_contours": (11, (50, 214, 293, 675),
                                 "Fig. 12 predicted contour plots of AoR, BD and mass flow over mu_s,pp and mu_r,pp"),
    "fig13_superimposed_contours": (11, (305, 190, 548, 380),
                                    "Fig. 13 superimposed contours: the admissible parameter region"),
    "fig14_aor_experiment_vs_dem": (11, (305, 384, 548, 553), "Fig. 14 AoR heaps, experiment and DEM"),
    "fig16_flow_rate_validation": (12, (50, 54, 293, 470), "Fig. 16 mass flow, DEM against experiment at 400-800 rpm"),
}


def main() -> None:
    doc = pymupdf.open(PDF)
    out = HERE / "figures"
    out.mkdir(exist_ok=True)
    for name, (page, box, cap) in CROPS.items():
        pix = doc[page - 1].get_pixmap(dpi=200, clip=pymupdf.Rect(*box))
        pix.save(out / f"elkassem2021_kona_{name}.png")
        print(f"{name}: page {page}, {pix.width}x{pix.height} px  ({cap})")


if __name__ == "__main__":
    main()
