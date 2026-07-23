# Programmatic printing on the Bambu Lab A1 mini ("Thumbelina")

This is the A1-mini companion to
[Programmatic and remote printing on the Bambu Lab H2D](h2d-programmatic-access.md).
The H2D doc is the full reference — transports, protocol payloads,
troubleshooting, relay design, and citations all live there and are
**not** duplicated here. This page is the *instruction list*: it walks
the same bringup Steps 0–6 in order, states exactly what changes for
the A1 mini, and gives the A1-mini-specific parameter values to plug
in. The A1 mini is the **easier** printer: it is single-extruder (no
IDEX filament-mapping dance), `bambulabs_api` is actually tested on
it, and the AC `ac-dev-lab` prior art referenced throughout the H2D
doc was written *against this exact model*.

> [!IMPORTANT]
> Bambu Lab's "printer control authorization" system is being extended
> to the A-series (see the IMPORTANT callout at the top of the H2D
> doc). The same rule applies: plan around Developer Mode / LAN mode,
> confirm the firmware version at bringup, and treat the Step 2 smoke
> test — not the settings menu's wording — as ground truth for whether
> the LAN ports are open. On older A1-mini firmware the toggle naming
> differs slightly (a single **"LAN Only Mode"** switch without a
> separate **"Developer Mode"** entry); newer firmware splits them as
> described in the H2D doc's terminology note.

## Parameter cheat sheet — A1 mini vs H2D

Every transport-level value is identical to the H2D. Only the
printer-physical and slicing parameters change:

| Parameter | A1 mini value | H2D value (for comparison) |
|---|---|---|
| MQTT endpoint | `mqtts://<IP>:8883`, user `bblp`, password = 8-digit access code | same |
| FTPS endpoint | `ftps://<IP>:990`, **implicit** TLS, TLS 1.2 session reuse **required** | same |
| MQTT topics | `device/<SERIAL>/report` / `device/<SERIAL>/request` | same |
| Credentials | `(IP, ACCESS_CODE, SERIAL)` triple | same |
| Network | **Wi-Fi only (2.4 GHz)** — no Ethernet port | RJ45 + Wi-Fi |
| Extruders | **1** (single extruder; optional AMS lite) | 2 (IDEX) |
| Build volume | **180 × 180 × 180 mm** | 350 × 320 × 325 mm |
| Max bed temp | **80 °C** | 120 °C |
| Max nozzle temp | **300 °C** | 350 °C |
| Slicer machine profile | `Bambu Lab A1 mini 0.4 nozzle` | `Bambu Lab H2D 0.4 nozzle` |
| Slicer process profile | `0.20mm Standard @BBL A1M` | `0.20mm Standard @BBL H2D` |
| Slicer filament profile | `Bambu PLA Basic @BBL A1M` | `Bambu PLA Basic @BBL H2D` |
| CLI filament-map flags | **none needed** | `--filament-map-mode "Manual" --filament-map "1,2"` |
| CLI plate selection | `--slice 0` (all plates) is fine | must use `--slice 1` (explicit plate) |
| `bambulabs_api` status | **tested** (A1 mini is a supported model) | README flags H2D as untested |
| Prior art | [`ac-dev-lab` `bambu_a1_mini`](https://github.com/AccelerationConsortium/ac-dev-lab/tree/main/src/ac_training_lab/bambu_a1_mini) — written for this printer | ported from it |

The two FTPS quirks debugged in PR #23 (implicit-vs-explicit FTPS on
`:990`, and the `522 SSL connection failed: session reuse required`
TLS-1.2 data-channel resumption) are **fleet-wide Bambu firmware
behaviour, not H2D-specific** — the `ImplicitFTP_TLS` class baked into
the checked-in scripts handles both and works unchanged on the A1
mini.

## Step 0 — Network (the biggest practical difference)

The A1 mini is **Wi-Fi-only (2.4 GHz)** — there is no RJ45 port, so
the H2D doc's "wired bringup side-steps campus IoT client isolation"
advice does not apply.

1. Join Thumbelina to the lab Wi-Fi from the touchscreen
   (Settings → WLAN). Pin the IP with a DHCP reservation as usual —
   the LAN flow has no discovery/mDNS broker.
2. On a BYU-IoT-style network with client isolation, **assume a
   roaming laptop cannot reach the printer directly.** Plan for the
   Step 2 smoke test to run from a machine that shares the printer's
   VLAN — in practice the Pi (or lab NUC) that will eventually host
   the relay. This makes the Pi relay *more* important for the A1
   mini, not less: it may be the only box that can talk to the
   printer at all.
3. Ports are the same as the H2D: `8883/tcp` (MQTT-over-TLS) and
   `990/tcp` (implicit FTPS) must be reachable from the worker.

## Step 1 — Enable LAN/Developer mode and capture the triple

Identical procedure to [H2D Step 1](h2d-programmatic-access.md#step-1--enable-lan-only-developer-mode-and-capture-credentials),
with one naming caveat:

1. Settings → General → enable **Developer Mode** if your firmware
   shows it; on older A1-mini firmware the only toggle is **LAN Only
   Mode** and it plays both roles. If you want to keep manual Bambu
   Studio cloud prints working, prefer the Developer-Mode-only /
   mixed-mode configuration where the firmware offers it.
2. Capture the **8-digit Access Code** (Settings → WLAN), the
   **15-character Serial** (Settings → Device), and the **firmware
   version** (pin it in the worker config).
3. That `(IP, ACCESS_CODE, SERIAL)` triple is everything downstream
   code needs — exactly as for the H2D.

## Step 2 — Smoke test (reuse the H2D script verbatim)

Run the checked-in [`scripts/h2d_smoketest.py`](../scripts/h2d_smoketest.py)
**as-is** with Thumbelina's values — nothing in it is H2D-specific;
the `H2D_IP` / `H2D_ACCESS_CODE` / `H2D_SERIAL` env-var names are just
labels:

```bash
pip install paho-mqtt
python scripts/h2d_smoketest.py --ip <IP> --access-code <CODE> --serial <SERIAL>
```

Expected output is the same as on the H2D: an `MQTT OK:` line with a
JSON `report` payload, then an `FTPS /cache:` listing (possibly `[]`).
The whole troubleshooting ladder in
[H2D Step 2](h2d-programmatic-access.md#step-2--smoke-test-reachability-no-print-yet)
(explicit-FTPS timeout, `522` session reuse, Developer Mode not
actually on, VLAN port filtering) applies unchanged — with the
addition that on the Wi-Fi-only A1 mini a `timed out` on *both*
transports from a laptop most likely means client isolation, so retry
from the Pi before touching printer settings.

## Step 3 — First programmatic print

Use the checked-in
[`scripts/h2d_step3_send_print.py`](../scripts/h2d_step3_send_print.py)
unchanged — the FTPS upload, the `print.project_file` MQTT payload,
and the `gcode_state` watch are all model-agnostic:

```bash
python scripts/h2d_step3_send_print.py <file>.gcode.3mf \
    --ip <IP> --access-code <CODE> --serial <SERIAL>
# --upload-only first if you want to verify the FTPS leg alone
```

Two A1-mini-specific rules for the payload file:

1. **Do not reuse the H2D `cube_h2d.gcode.3mf` test payload.** A job
   sliced for the wrong printer is triage item #2 in the H2D Step 3
   failure list, and that file's IDEX header
   (`filament_map = 1,2`, `master_extruder_id = 2`, …) is exactly
   what a single-extruder A1 mini will choke on. Slice a small test
   cube with an **A1 mini profile** instead — export from desktop
   Bambu Studio is fine, or use the CLI recipe below.
2. **AMS lite:** the script's payload sends `"use_ams": false` /
   `"ams_mapping": ""`, which prints from the external spool holder.
   If Thumbelina feeds from an AMS lite, set `use_ams: true` and an
   `ams_mapping` (edit `project_file_payload()` in the script). The
   `ac-dev-lab` A1-mini issues
   ([#147](https://github.com/AccelerationConsortium/ac-dev-lab/issues/147),
   [#149](https://github.com/AccelerationConsortium/ac-dev-lab/issues/149))
   are the working reference for what mapped correctly there.

Success looks identical to the H2D: `gcode_state` walks
`IDLE → PREPARE → RUNNING` within ~30 s.

## Step 4 — Wrap it in Python

Use [`scripts/h2d_step4_bambulabs_api.py`](../scripts/h2d_step4_bambulabs_api.py)
unchanged. Better still than on the H2D: **`bambulabs_api` is tested
on the A1 mini** (it is the H2D that the library's README flags as
untested), so the defensive version-printing in the script is less
likely to matter. The most directly reusable prior art is
`ac-dev-lab`'s
[`_scripts/manual_print.py`](https://github.com/AccelerationConsortium/ac-dev-lab/blob/main/src/ac_training_lab/bambu_a1_mini/_scripts/manual_print.py),
which was written against an A1 mini and demonstrates the
wrap-a-raw-`.gcode`-as-`Metadata/plate_1.gcode`-in-a-zip trick — that
trick works on the A1 mini exactly as published. Even the
single-extruder G-code setpoint rewriting in
[`device.py`](https://github.com/AccelerationConsortium/ac-dev-lab/blob/main/src/ac_training_lab/bambu_a1_mini/device.py)
(`M104`/`M109`/`M140`/`M190` replacement), which the H2D doc flags as
**not** portable to IDEX, is fine here — Thumbelina is the printer it
was written for.

## Headless slicing (STL → 3MF) — the biggest simplification

The entire IDEX dance from the
[verified H2D recipe](h2d-programmatic-access.md#verified-end-to-end-locally)
— `--filament-map-mode "Manual"`, `--filament-map "1,2"`, duplicated
filament profiles, the `--slice 1`-not-`--slice 0` gotcha — exists
only because the H2D is dual-extruder. On the single-extruder A1 mini
the command collapses to the plain wiki form:

```bash
xvfb-run -a -s "-screen 0 1280x1024x24" ./bambu.AppImage \
  --orient 1 --arrange 1 \
  --load-settings  "a1mini_machine_flat.json;a1mini_process_flat.json" \
  --load-filaments "a1mini_filament_flat.json" \
  --slice 0 --export-3mf part.gcode.3mf --outputdir out part.stl
```

with the flattened profiles built from the AppImage's bundled
`resources/profiles/BBL/` presets:

- machine: `machine/Bambu Lab A1 mini 0.4 nozzle.json`
- process: `process/0.20mm Standard @BBL A1M.json`
- filament: `filament/Bambu PLA Basic @BBL A1M.json`

Two of the three H2D gotchas still apply because they are
CLI-general, not IDEX-specific:

1. **Flatten the `inherits` chain.** The bundled profiles are
   templates (`"inherits": "Bambu PLA Basic @base"`, …) that the CLI
   does not resolve — walk `inherits` upward and merge into one full
   config per role, exactly as the H2D doc describes.
2. **Patch the flattened machine config's identity fields** so the
   compatibility check accepts it: `from = "system"`,
   `inherits = ""`, and
   `printer_settings_id = "Bambu Lab A1 mini 0.4 nozzle"` (matching
   the `compatible_printers` list on the A1M process profile).

The third gotcha (manual filament mapping gated on
`plate_to_slice != 0`) does not apply — a single-extruder printer
never enters that codepath, so `--slice 0` works.

> [!NOTE]
> Unlike the P2S and H2D runs in the H2D doc, this exact A1-mini
> invocation has **not** been empirically executed as part of PR #23
> — but it exercises the *less* exotic (single-extruder) codepath of
> the same verified AppImage, so treat any failure as a profile
> flattening/patching problem first.

## Steps 5–6 — Relay, Tailscale, and the safety envelope

The whole remote-access design —
[R1/R2/R3 table, FastAPI relay, Tailscale-as-LAN, `/print_stl` with a
safety envelope, hardware interlock](h2d-programmatic-access.md#step-5--going-remote-internet--google-colab-access)
— is printer-agnostic and carries over verbatim. Adjustments for
Thumbelina:

1. **Relay placement matters more.** Because the A1 mini is
   Wi-Fi-only behind possible client isolation (Step 0), the Pi may
   be the *only* machine that can reach it — put the relay there from
   day one.
2. **`_safe_slice()` loses the IDEX flags.** Drop
   `--filament-map-mode` / `--filament-map`, pass a **single**
   filament profile (`--load-filaments f"{fil_json}"`), point
   `--load-settings` at the flattened A1-mini bundles, and `--slice
   0` is fine. `_enforce_envelope()` works unchanged — single-extruder
   G-code headers are the simple case of what it already parses.
3. **Scale `LIMITS` to the smaller machine.** Suggested envelope
   (same PLA-lab assumptions as the H2D sketch):

   ```python
   LIMITS = {
       "max_stl_bytes":          20 * 1024 * 1024,  # 180 mm cube ≪ H2D volume
       "max_print_minutes":      6 * 60,            # plausible A1-mini job cap
       "max_filament_grams":     250,
       "max_first_layer_bed_c":  70,                # ≤ printer max of 80 °C
       "max_nozzle_c":           260,               # PLA/PETG; printer max 300 °C
   }
   ```

   The existing PLA-oriented temperature caps are already valid for
   the A1 mini (its hardware maxima are 80 °C bed / 300 °C nozzle);
   the main tightening is on time/mass. Oversize STLs are also
   rejected naturally at the `--arrange` step since the bed is
   180 × 180 mm.
4. **Hardware interlock:** the same three
   [off-the-shelf options](h2d-programmatic-access.md#hardware-interlock--concrete-options)
   apply. The A1 mini draws far less than the H2D (~150 W typical,
   ~350 W peak), so any of the listed parts is comfortably rated;
   everything still sits upstream of the printer's power inlet.

## Bringup order (TL;DR)

1. **Step 0–1** at the printer: Wi-Fi + DHCP reservation, enable
   Developer/LAN mode, capture `(IP, ACCESS_CODE, SERIAL)` + firmware
   version. (~15 min)
2. **Step 2** from a machine on the printer's VLAN (likely the Pi):
   `scripts/h2d_smoketest.py` with Thumbelina's values. (~5 min)
3. **Step 3**: slice a small cube with an **A1 mini** profile, then
   `scripts/h2d_step3_send_print.py cube_a1m.gcode.3mf --upload-only`
   first, then the full run with the bed clear. Do **not** reuse the
   H2D cube file. (~15 min)
4. **Step 4**: same print via `scripts/h2d_step4_bambulabs_api.py`.
   (~15 min)
5. **Steps 5–6**, only after 1–4 are green: relay on the Pi with the
   A1-mini `_safe_slice` / `LIMITS` adjustments above, Tailscale (or
   Funnel) in front, hardware interlock installed and tested
   mid-print before any unattended/Colab use.

## What *not* to do

- **Don't send H2D-sliced files** (or any wrong-printer `.gcode.3mf`)
  — the IDEX header is rejected by single-extruder firmware, and the
  failure shows up as `gcode_state` never leaving `IDLE`.
- **Don't copy the H2D CLI flags wholesale** —
  `--filament-map-mode` / `--filament-map` on a single-extruder
  profile is at best a no-op and at worst an error.
- **Don't assume the settings-menu wording matches the H2D doc** —
  older A1-mini firmware has a single LAN Only toggle; the Step 2
  smoke test is the ground truth for whether `:8883`/`:990` are open.
- **Don't debug reachability from a roaming laptop on an
  isolated-client Wi-Fi VLAN** — run the smoke test from the Pi
  before concluding anything is wrong with the printer.
