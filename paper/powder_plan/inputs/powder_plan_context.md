# Context: ten-powder validation plan (PR #97, July 2026)

The manuscript (`main.pdf`, with SI `si.pdf`) has just been revised to plan a
ten-powder validation campaign and to describe the three-phase dosing
procedure actually implemented in the repository firmware. The relevant new
content is:

- **Table 1 (main.pdf, Dispensing performance)** — the ten planned powders:
  sodium chloride (baseline), calcium lactate, sodium alginate, xanthan gum,
  white rice flour, brown rice flour (six food-grade surrogates); AlSi10Mg
  gas-atomized alloy powder; crystalline silicon in fine (~45 um) and coarse
  (100-200 mesh) grades; fumed-silica glidant (dosed neat and as a 0.5-1 wt%
  flow aid for the fine silicon). Qualitative flow observations come from
  manual bench tests documented in repository issues #88/#116; the fine-Si and
  glidant notes come from prior experience with a commercial powder trickler.
- **Three-phase dosing procedure (Experimental)** — bulk (continuous rotation,
  steep angle, exit at 0.5 g-to-target) -> fine (30-degree increments with
  stabilized readings, exit at 50 mg-to-target) -> tap-to-target (solenoid tap
  bursts with settle-and-read, +/-5 mg tolerance, auger nudge on stall). All
  phase parameters are per-powder configurable. Algorithmic/Bayesian
  optimization of these parameters is explicitly deferred to future work.
- **ISO 8655-inspired validation protocol** — modelled on the two attached
  Digital Discovery "digital pipette" papers (`digital_pipette_v1_*.pdf`,
  `digital_pipette_v2_*.pdf`), which followed ISO 8655-6: n>=10 replicate
  deliveries per condition at target masses spanning the envelope (5 g,
  500 mg, 50 mg, 20 mg), reporting systematic error, random error (CV),
  plus powder-specific overshoot rate and dose time, against pre-registered
  acceptance limits (+/-5% above 100 mg, +/-10% at 20 mg, <30 s per dose).

Dispensing data in Fig. 3 remain SYNTHETIC watermarked placeholders by
intention; the bench campaign will replace them. Do not flag the synthetic
data itself as a defect — that is a known, deliberate placeholder.
