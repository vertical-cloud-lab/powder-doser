# Alternative / commercial powder-dosing equipment

This folder collects research on commercially-available powder-dosing
instruments that are alternatives to (or potential reference points for)
the in-house *powder-excavator* concept. It is the working area for the
quote-gathering effort tracked in
[issue #1 — "Quotes and clarifications for powder dosing equipment (MTI,
Mettler, etc.)"](https://github.com/vertical-cloud-lab/powder-doser/issues/1).

The information below is compiled from each vendor's public product page
and is intended only as a starting point — confirm every number with the
vendor when requesting a quote, since options, accessories, and freight
all materially change the final price.

## Products under consideration

| # | Vendor                                  | Product / SKU                       | Class                                 | Throughput / capacity                                    | Resolution & accuracy                            | Public price (USD, indicative) |
|---|-----------------------------------------|-------------------------------------|---------------------------------------|----------------------------------------------------------|--------------------------------------------------|--------------------------------|
| 1 | MTI Corporation                         | [AM-PD6](https://mtixtl.com/products/am-pd6)     | Automated, 6-channel benchtop          | 6 samples / batch, 6 × 500 mL feeders, up to 100 g       | 0.1 mg readability, ±2 mg accuracy               | ~$70k list (varies)            |
| 2 | MTI Corporation                         | [AM-PD16](https://mtixtl.com/products/am-pd16)   | Automated, 16-channel benchtop         | 16 samples / batch, 16 × 500 mL feeders, 10 mg – 100 g   | 0.1 mg readability, ±1 mg accuracy               | Quote-only                     |
| 3 | MTI Corporation                         | [PF-A](https://mtixtl.com/products/pf-a)         | **Manual** glass screw dispenser, 250 mL | Single sample, manual hand-knob feed                   | Limited by user's external balance               | ~$300 list                     |
| 4 | Labman Automation                       | [MultiDose](https://www.labmanautomation.com/portfolio/products/multidose/) | Automated, collaborative-robot benchtop | Up to 6 SBS racks per run, 56 dosing heads on carousel  | Mettler XPR 6-decimal balance                    | Quote-only                     |
| 5 | METTLER TOLEDO + Axel Semrau (Trajan)  | [Chronect XPR](https://www.mt.com/us/en/home/products/Laboratory_Weighing_Solutions/mettler-product-collaboration/axel-semrau.html) | Automated, 6-axis-robot benchtop       | Up to 32 RFID powders, up to 288 vessels, 1 mg – grams  | XPR balance, 0.01 mg (0.005 mg fine), 0.7 mg min | Quote-only                     |

## 1. MTI AM-PD6 — Automated 6-channel powder dispenser

- Product page: <https://mtixtl.com/products/am-pd6>
- Format: compact benchtop, glovebox-friendly, LCD touchscreen + bundled
  laptop and software.
- Material feeding: six 500 mL containers with mechanical stirring and
  glass material feeders.
- Capacity: up to 100 g per dose.
- Particle size: 10–100 µm standard (smaller available on request).
- Resolution: 0.1 mg. Accuracy: ±2 mg (varies with powder).
- Sample holder: plastic tray with 6 × 30 mL plastic containers; X-Y
  stage moves containers under the feeders.
- Power: 120 VAC or 208–240 VAC, 50/60 Hz, 3 kVA.
- Footprint: 1000 × 600 × 800 mm (L × W × H).
- Compliance: CE; NRTL/CSA available at extra cost.
- Warranty: 1-year limited (consumables, glassware, etc. excluded).
- Optional: protective case / glovebox integration; can be coupled to
  MTI's automated mixing, pressing, and sintering modules.

## 2. MTI AM-PD16 (AM-PD16R) — Automated 16-channel powder dispenser

- Product page: <https://mtixtl.com/products/am-pd16>
- Format: compact benchtop with rotary 16-element glass feeder and a
  robot arm that picks containers and places them on a precision
  balance.
- Capacity: 10 mg – 100 g per dose.
- Resolution: 0.1 mg. Accuracy: ±1 mg.
- Sample holder: tray with 16 × 30 mL plastic containers.
- Power: 208–240 VAC, 50/60 Hz, 3 kW.
- Footprint: 1000 × 600 × 800 mm.
- Compliance: CE; NRTL/CSA at extra cost.
- Warranty: 1-year warranty + lifetime support.
- Related option to ask about: `Bal-APD6-S36` — 6-channel dispenser with
  bar-code scanner extending the run to 36 compositions
  (<https://mtixtl.com/products/bal-apd6-s36>).

## 3. MTI PF-A — Manual 250 mL glass dispenser

- Product page: <https://mtixtl.com/products/pf-a>
- Format: hand-operated screw dispenser for use beside an external
  balance (low-cost reference / baseline).
- Container material: glass; max working temperature 300 °C.
- Feeding screw: PTFE, 6.5 mm pitch (custom pitch on request).
- Container capacity: 250 mL; particle size < 170 µm.
- Warranty: 1-year limited.
- **Lead time** is explicitly called out in the issue and should be
  confirmed when requesting the quote — MTI's online listings do not
  publish a stocking commitment for this SKU.

## 4. Labman MultiDose

- Product page:
  <https://www.labmanautomation.com/portfolio/products/multidose/>
- Format: benchtop platform pairing a collaborative Universal Robots
  arm with a Mettler Toledo XPR 6-decimal balance.
- Throughput: up to 6 SBS-format racks per run; carousel holds up to 56
  different dosing heads (>10 specialised heads available, including
  anti-static).
- Powders: handles sticky, fluffy, and static-prone materials; anti-
  static kit available.
- Software: drag-and-drop UI with live feedback, user profiles, secure
  CSV export, real-time notifications.
- Reliability features: spare-vial fallback, autonomous interchangeable
  gripper fingertips, integrated de-clogging, mid-run rack updates.
- Customisation: off-the-shelf or custom-built (extra modules, glovebox
  integration, air-filtration enclosures, etc.).
- Support: 1-year full warranty as standard; designed and built in the
  UK.
- Vendor: Labman Automation Ltd (Stokesley, North Yorkshire, UK).
  General contact form: <https://www.labmanautomation.com/contact/>.

## 5. METTLER TOLEDO Chronect XPR (with Axel Semrau / Trajan)

- Mettler product page:
  <https://www.mt.com/us/en/home/products/Laboratory_Weighing_Solutions/mettler-product-collaboration/axel-semrau.html>
- Demo video: <https://www.youtube.com/watch?v=zm9fOt1J37c>
- Format: benchtop automated powder + (optional) liquid dispensing
  system built around a Mettler Toledo XPR balance and a Universal
  Robots UR3e 6-axis arm; CHRONOS control software with RFID-tagged
  dosing heads.
- Throughput: up to 32 RFID-tagged powder heads; up to 288 vessels
  across 3 SBS plates (also supports 2, 4, 8, 10, 20, 40 mL vials).
- Dispensing range: 1 mg up to several grams of powder; optional
  liquid module dispenses 100 mg – 10 g of solvents up to 20 cP.
- Balance: XPR with 0.01 mg readability (0.005 mg in fine range);
  minimum sample weight ~0.7 mg (1 % tolerance).
- Footprint: ~975 × 650 × 800 mm; ~100 kg main unit.
- Use cases: inert-atmosphere or fume-hood operation for toxic / air-
  sensitive substances; full ELN/LIMS integration.
- Vendor contact: METTLER TOLEDO local sales (US:
  <https://www.mt.com/us/en/home/site_content/contact_us.html>) or
  Axel Semrau (Trajan Group):
  <https://www.axel-semrau.de/en/contact/>.

## Quote-request checklist (use the same wording for every vendor)

When emailing each vendor, include the following so the quote is
directly comparable across the five products:

1. **Application context** — academic R&D lab, autonomous /
   self-driving lab workflow, ceramic and metal-oxide precursor powders
   in the 1 mg – 50 g range, target throughput of N samples/day.
2. **Powders to handle** — list a few representative materials
   (e.g. xanthan gum, alumina, lithium salts) so the vendor can pick
   appropriate dosing heads and flag anti-static / cohesive-powder
   concerns.
3. **Sample format** — vial / well-plate type and SBS rack format.
4. **Environment** — ambient bench, fume hood, or glovebox (specify
   inert-atmosphere requirement).
5. **Software / integration** — scriptable API, ELN/LIMS hooks, CSV
   export, ability to drive the system from a host PC over
   Ethernet/USB.
6. **Items to itemize on the quote**
   - Base instrument and standard accessories.
   - Dosing heads / feeders for the powders listed in (2).
   - Required PC, balance, and any consumables.
   - Glovebox / enclosure / anti-static add-ons.
   - Installation, training, and on-site commissioning.
   - 1st-year and extended-warranty / service-plan options.
   - Freight and applicable taxes/duties to the lab address.
7. **Lead time** — explicitly request stock vs. build-to-order lead
   time (called out in the issue for PF-A in particular).
8. **Validity** — ask for the quote to be valid for at least 60 days.