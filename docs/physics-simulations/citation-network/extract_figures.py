#!/usr/bin/env python3
"""Crop key figures of El Kassem et al. (2021), KONA 38:235-250, and of the same group's Computational Particle
Mechanics 8:87-111 paper (both CC BY 4.0), from the PDFs read through the Pi.

Usage:  python extract_figures.py [pdf_dir]        (default /tmp/kona/pdf)
Writes figures/<paper>_<fig>.png at 200 dpi. Boxes are PDF points (x0, y0, x1, y1) on the printed page.
The PDFs are not committed; manifest.json has their URLs, sizes and sha256.
"""
from __future__ import annotations

import sys
from pathlib import Path

import pymupdf

HERE = Path(__file__).resolve().parent
PDF_DIR = Path(sys.argv[1] if len(sys.argv) > 1 else "/tmp/kona/pdf")
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
CROPS_CPM = {
    "fig05-06_aor_free_flowing_vs_cohesive": (13, (51, 300, 292, 492),
                                              "Figs. 5-6 experimental AoR heaps of SpheroLac 100 and InhaLac 251"),
    "fig12_pareto_aor_cohesive": (16, (51, 352, 292, 528), "Fig. 12 Pareto of effects on the AoR, cohesive powder"),
    "fig27-28_aor_validation": (22, (51, 54, 547, 360),
                                "Figs. 27-28 and Table 10: DEM AoR from the prediction model against experiment"),
}


def main() -> None:
    out = HERE / "figures"
    out.mkdir(exist_ok=True)
    for paper, crops in (("elkassem2021_kona", CROPS), ("elkassem2021_cpm", CROPS_CPM)):
        doc = pymupdf.open(PDF_DIR / f"{paper}.pdf")
        for name, (page, box, cap) in crops.items():
            pix = doc[page - 1].get_pixmap(dpi=200, clip=pymupdf.Rect(*box))
            pix.save(out / f"{paper}_{name}.png")
            print(f"{paper} {name}: page {page}, {pix.width}x{pix.height} px  ({cap})")


if __name__ == "__main__":
    main()
