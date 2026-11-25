# Powder doser

**An open-source powder doser for autonomous alloy discovery, designed by engineers and modelled by AI agents.**

<p align="center">
  <a href="https://vertical-cloud-lab.github.io/powder-doser/"><b>Project page</b></a> ·
  <a href="https://github.com/vertical-cloud-lab/powder-doser/pull/209">Paper (in prep.)</a> ·
  <a href="https://vertical-cloud-lab.github.io/powder-doser/#build">CAD</a> ·
  <a href="https://www.youtube.com/watch?v=YmvaeqOQAU4&amp;t=514s">Talk</a> ·
  <a href="https://vertical-cloud-lab.github.io/powder-doser/#videos">Videos</a> ·
  <a href="https://vertical-cloud-lab.github.io/powder-doser/static/powder-doser-poster.pdf">Poster</a> ·
  <a href="https://vertical-cloud-lab.github.io/powder-doser/#talks">TMS 2027</a>
</p>

We built this doser at BYU's [Vertical Cloud Lab](https://github.com/vertical-cloud-lab) from 3D-printed parts and off-the-shelf electronics, for under $200 plus an analytical balance. One printed tube is both the powder reservoir and the dosing screw: the doser turns, tilts and taps it over a cup on the balance, which closes the loop, and an AI agent runs a dose when someone asks for one in a GitHub comment. Every 1 g dose on seven of the 13 powders we tested landed within ±5% of the target. **The [project page](https://vertical-cloud-lab.github.io/powder-doser/) has the rest:** the paper's figures, the CAD and firmware, the talk and videos, the poster and the TMS 2027 abstracts. The design discussion, the AI agents' work and the run data are in this repository's issues and pull requests.

<p align="center"><a href="https://vertical-cloud-lab.github.io/powder-doser/"><img src="docs/readme/gifs/al4047_claude_dose.gif" alt="Animation: left, a phone's screen recording of a GitHub pull-request thread, where Claude's checklist ticks off, a follow-up to Claude is typed and Claude posts its plan and a report; right, the doser over a balance whose reading climbs" width="720"></a></p>

<sub><b>Claude doses 8 g of Al 4047 for an atomizer charge</b> (30 Sep 2026, [#166](https://github.com/vertical-cloud-lab/powder-doser/pull/166)). Left, a phone's screen recording of the pull-request thread: Claude's checklist while the first pass runs, the follow-up to <code>@claude</code> typed on the phone after a clog, Claude's plan for a top-up, and its report. Right, the fixed camera over the balance at the same moment. 59 minutes in 22 s, sped up as marked. The full teaser on the [project page](https://vertical-cloud-lab.github.io/powder-doser/) starts with the auger being fitted.</sub>

<p align="center"><a href="https://vertical-cloud-lab.github.io/powder-doser/#dosing"><img src="docs/readme/gifs/three_phase_dose.gif" alt="Animation: the CAD doser over a cup on a balance runs a bulk, trickle and tap phase while a plot of the powder in the cup rises to 0.5 g" width="720"></a></p>

<sub><b>A dose in three phases, replayed on the CAD</b> with the mass logged in the cup: bulk at 40° and 100 rpm with taps until 300 mg is left, trickle at 10° with no taps, then single taps at 15° until within 3 mg. The values in blue are the ones the optimizer sets, here the settings it recommended for 0.5 g of salt in the optimization campaign ([#166](https://github.com/vertical-cloud-lab/powder-doser/pull/166)), not those of the tests in the paper. Sped up as marked; from the campaign's slides ([#175](https://github.com/vertical-cloud-lab/powder-doser/pull/175)).</sub>

## Citation

Until the paper is out, please cite the repository:

```bibtex
@misc{charles2026powderdoser,
  title        = {An open-source powder doser for autonomous alloy discovery,
                  designed by engineers and modelled by AI agents},
  author       = {Charles, Sam and Mulberry, Will and Winters, Luke and
                  Robison, Carl and Erickson, Gage and Baird, Sterling G.},
  year         = {2026},
  note         = {Manuscript in preparation},
  howpublished = {\url{https://github.com/vertical-cloud-lab/powder-doser}}
}
```
