# Battery power options for conference demos (12V / 5A barrel-jack system)

This note responds to the request for practical battery options for running the powder doser away from wall power. The doser input target is **12V at up to 5A** (up to **60W**) through a barrel jack.

## Assumptions and compatibility checks

- **Power target:** 12V, peak 5A (design for 60W continuous headroom).
- **Connector:** verify barrel size on the doser before purchase (commonly **5.5 mm OD x 2.1 mm ID**, sometimes 2.5 mm ID).
- **Polarity:** assume **center-positive** unless explicitly marked otherwise.
- **Runtime estimate formula:**  
  `runtime (hours) ≈ usable_Wh / load_W`  
  where `usable_Wh ≈ battery_Wh × 0.85` (DC conversion + wiring losses).

## Option comparison

| Option | Typical price (USD) | Practical compatibility with 12V/5A barrel jack | Typical runtime at 60W load | Notes |
|---|---:|---|---:|---|
| Portable power station with regulated 12V DC output (10A car port or 5.5x2.1 output) | $150–$500 (240–700Wh class) | High (with quality cable/adapter, can supply >5A) | ~3.4–9.9 h | Easiest/safest conference option; includes charging, BMS, display. |
| 12.8V LiFePO4 pack (with BMS) + 12V buck-boost regulator + fuse + barrel cable | $120–$300 (20–40Ah pack + converter/accessories) | Medium-High (good if converter is rated >=8A continuous) | ~3.6–7.3 h (20–40Ah class) | Lighter than SLA, good cycle life, but requires integration work. |
| Sealed lead-acid (SLA) 12V battery + fuse + barrel adapter | $60–$180 (12–35Ah class) | Medium (voltage sags under load; may dip below ideal) | ~1.7–5.0 h | Lowest upfront cost; heavy; shorter cycle life. |
| USB-C PD power bank + PD trigger board set to 12V + boost converter to 12V/5A | $90–$250 | Low-Medium (many power banks cannot sustain true 60W at 12V rail) | ~1.4–4.2 h | Compact but easy to under-spec; higher integration risk. |
| Power-tool battery adapter ecosystem (e.g., 18V tool battery + 12V converter) | $80–$220 (assuming battery + adapter + converter) | Medium (works if converter is well-filtered and >=8A) | ~1.4–4.0 h (typical 90–280Wh packs) | Good if team already owns batteries/chargers. |

## Recommended path

1. **Primary recommendation (conference-ready):**  
   Use a **portable power station** with a regulated 12V output rated above 5A (prefer 8–10A capable), plus a short, thick-gauge DC cable and correct barrel adapter. This is the quickest, lowest-risk setup.

2. **Engineering recommendation (if integrating into hardware kit):**  
   Use a **LiFePO4 pack + buck-boost converter** module, fused at the battery output, with reverse-polarity protection at the doser input. This gives strong runtime per weight and better long-term cycle life.

## Implementation checklist (to avoid demo failures)

- Verify barrel jack **OD/ID size** and **center polarity** on the doser.
- Bench-test at worst-case load for at least 30 minutes (watch voltage drop and converter temperature).
- Add inline fuse near battery positive terminal.
- Bring one spare pre-wired barrel cable and one polarity-reversing adapter to conference.
- If using power station car-port output, use a locking or strain-relieved adapter cable.

## Quick runtime reference

At a 60W load with 85% usable energy factor:

- 240Wh battery -> ~3.4 hours
- 360Wh battery -> ~5.1 hours
- 512Wh battery -> ~7.3 hours
- 700Wh battery -> ~9.9 hours

For typical booth demos with intermittent motor activity, observed runtime is often longer than constant 60W calculations.
