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
   roaming laptop cannot reach the printer directly.** On
   `byu-devices` specifically, devices are typically not allowed to
   talk to each other at all, so the Step 2 smoke test may fail from
   *any* second device on that network — not just roaming laptops.
   Two workarounds:
   - **Interim: phone hotspot.** Put both the printer and the test
     laptop on the same phone hotspot so they share an isolated
     private network. The A1 mini is **2.4 GHz only** — on an iPhone
     you must enable *Maximise Compatibility*, and in `ac-dev-lab`
     testing ([#147](https://github.com/AccelerationConsortium/ac-dev-lab/issues/147))
     the printer *still* failed to see an iPhone hotspot even with
     that enabled, so have an Android hotspot or a cheap travel
     router as plan B.
   - **Longer term:** a network exemption / dedicated lab AP so the
     relay Pi and the printer share a VLAN without isolation (campus
     IT conversation — per @sgbaird, Shawn is the contact for this).
   Plan for the Step 2 smoke test to run from a machine that shares
   the printer's network — in practice the Pi (or lab NUC) that will
   eventually host the relay. This makes the Pi relay *more*
   important for the A1 mini, not less: it may be the only box that
   can talk to the printer at all.
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

Use the checked-in, A1-mini-specific
[`scripts/a1_mini_send_print.py`](../scripts/a1_mini_send_print.py).
It is the same verified FTPS-upload + `print.project_file` +
`gcode_state`-watch flow as the H2D Step 3 script, packaged for the
lab: open the file, fill in the **FILL THESE IN** block at the top
(the `PUT_..._HERE` placeholders for the printer IP, 8-digit access
code, 15-character serial, and the path to the `.gcode.3mf` you want
to print), then run it with no arguments:

```bash
pip install paho-mqtt
python scripts/a1_mini_send_print.py
# add --upload-only first if you want to verify the FTPS leg alone
```

If you prefer not to edit the file, everything can instead be passed
on the command line (`--ip/--access-code/--serial` plus the file path
as an argument) or via `A1_MINI_IP` / `A1_MINI_ACCESS_CODE` /
`A1_MINI_SERIAL` env vars — command line beats env vars beats the
constants in the file. (The generic
[`scripts/h2d_step3_send_print.py`](../scripts/h2d_step3_send_print.py)
also still works here; the A1-mini script just adds the checks below.)

Two A1-mini-specific rules for the payload file — both of which the
script now enforces or exposes:

1. **Do not reuse the H2D `cube_h2d.gcode.3mf` test payload.** A job
   sliced for the wrong printer is triage item #2 in the H2D Step 3
   failure list, and that file's IDEX header
   (`filament_map = 1,2`, `master_extruder_id = 2`, …) is exactly
   what a single-extruder A1 mini will choke on. Slice a small test
   cube with an **A1 mini profile** instead — export from desktop
   Bambu Studio is fine, or use the CLI recipe below.
   `a1_mini_send_print.py` inspects the file's G-code header before
   uploading and refuses anything that looks H2D/IDEX-sliced (or that
   is a project 3MF with no `Metadata/plate_1.gcode`); `--force`
   overrides.
2. **AMS lite:** the default payload sends `"use_ams": false` /
   `"ams_mapping": ""`, which prints from the external spool holder.
   If Thumbelina feeds from an AMS lite, set `USE_AMS = True` (and an
   `AMS_MAPPING`) in the FILL THESE IN block, or pass
   `--use-ams`/`--ams-mapping`. The `ac-dev-lab` A1-mini issues
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

## Field notes from `ac-dev-lab` (hard-won A1-mini lessons)

The AC team ran a full A1-mini automation campaign (remote Python
control, a Pi 4B relay, a Hugging Face/Colab front-end, and a
self-driving-lab practical) and left a detailed paper trail. These are
the operational lessons from
[#147](https://github.com/AccelerationConsortium/ac-dev-lab/issues/147),
[#149](https://github.com/AccelerationConsortium/ac-dev-lab/issues/149),
[#160](https://github.com/AccelerationConsortium/ac-dev-lab/issues/160), and
[#168](https://github.com/AccelerationConsortium/ac-dev-lab/issues/168)
that are worth knowing *before* they bite:

1. **The `0500-4003` "unable to parse file" saga — don't change the
   printer-side storage path.** For weeks, `upload_file` +
   `start_print` via `bambulabs_api` produced *"Printing stopped
   because the printer was unable to parse the file"*
   (`0500-4003 115012` / `108000`) even though the same file printed
   fine when started from the touchscreen, and factory reset / SD-card
   swaps / reformatting didn't help. The root cause (found with the
   `bambulabs_api` maintainer in
   [mchrisgm/bambulabs_api#99](https://github.com/mchrisgm/bambulabs_api/issues/99))
   was that the upload path on the printer had been changed from the
   location `start_print` expects. Leave the printer's file layout
   alone and upload to the default location the library (or our
   scripts' `/cache`) uses. If you ever hit `0500-4003`, check the
   path *first*, before the SD-card/firmware rabbit holes.
2. **`set_bed_temperature()` is a silent no-op — send G-code
   instead.** Confirmed on the real A1 mini: the API call neither
   changes the UI setpoint nor the actual bed temperature. What works
   is sending raw G-code via
   [`printer.gcode()`](https://mchrisgm.github.io/bambulabs_api/api/printer.html#bambulabs_api.Printer.gcode)
   — e.g. `M190 S65` (bed) / `M109 S220` (nozzle) — or pre-baking the
   setpoints into the `.gcode` file, which is exactly what
   `ac-dev-lab`'s `device.py` does with its `M104`/`M109`/`M140`/`M190`
   rewriting. `set_print_speed` and the light/pause/resume/status
   calls worked as advertised.
3. **The access code may display as an IP address on a fresh
   printer.** Until the printer has been linked once via the Bambu
   Handy app + Bambu Studio login, Settings → WLAN can show an IP
   where the 8-digit access code should be
   ([forum thread](https://forum.bambulab.com/t/a1-mini-where-do-i-find-the-access-code/56991/5)).
   One-time account linking fixes it; after that Step 1 proceeds
   normally.
4. **The printer's MQTT broker is LAN-local only.** It cannot be
   reached from outside its own network
   ([mchrisgm/bambulabs_api#110](https://github.com/mchrisgm/bambulabs_api/issues/110))
   — which is precisely why `ac-dev-lab` converged on the same
   architecture as our Steps 5–6: a Pi 4B beside the printer speaking
   LAN-MQTT/FTPS locally, bridged to the outside world via an
   external broker (HiveMQ/HF Spaces there, the FastAPI relay +
   Tailscale here).
5. **Status can read `UNKNOWN` immediately after `connect()`.** The
   working `ac-dev-lab` script sleeps ~2 s after `printer.connect()`
   and tolerates an `UNKNOWN` first read; don't gate your upload on a
   perfect first status poll.
6. **One G-code file per iteration beats live parameter twiddling.**
   For parameter-sweep/BO work (relevant to the tensegrity loop),
   `ac-dev-lab` settled on generating a separate small G-code file
   per iteration (or a grid of squares with per-square presets in one
   file) with setpoints baked in, plus purge/reset moves between
   iterations — rather than mutating temperatures mid-print through
   the API.

Reusable artifacts beyond the already-linked
[`bambu_a1_mini`](https://github.com/AccelerationConsortium/ac-dev-lab/tree/main/src/ac_training_lab/bambu_a1_mini)
directory: the Pi-relay control repo
[SissiFeng/bambu-printer-control](https://github.com/SissiFeng/bambu-printer-control)
(Pi 4B: printer control, MQTT bridge to HF, G-code generation), the
[A1-mini Hugging Face Space](https://huggingface.co/spaces/AccelerationConsortium/Bambu_A1mini),
and [PR #529](https://github.com/AccelerationConsortium/ac-dev-lab/pull/529)
(A1-mini toolhead-camera → AWS S3 + MQTT setup, useful when we add
print monitoring).

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

### One command from STL to print: `a1_mini_slice_and_send.py`

The checked-in
[`scripts/a1_mini_slice_and_send.py`](../scripts/a1_mini_slice_and_send.py)
packages this recipe as the slice-and-send alternative to
`a1_mini_send_print.py`: it takes a raw `.stl` (or an *unsliced* Bambu
Studio project `.3mf`), runs the CLI command above headlessly, prints
a G-code-header summary (printer profile, estimated time, filament
grams, temperatures), then feeds the result through the same verified
FTPS-upload + `print.project_file` + `gcode_state`-watch pipeline.
Same fill-in-the-placeholders pattern as the send script, plus fields
for the slicer binary and the three flattened profile JSONs:

```bash
pip install paho-mqtt
python scripts/a1_mini_slice_and_send.py                  # slice + upload + print
python scripts/a1_mini_slice_and_send.py --slice-only --keep-output   # dry-run the slicer alone
python scripts/a1_mini_slice_and_send.py --upload-only    # stop before starting the print
```

Notes: for `.stl` input the three profile JSONs are required; for a
project `.3mf` they are optional but **override** the settings
embedded in the file if given (CLI precedence). `--no-arrange` keeps a
project 3MF's existing plate layout. Already-sliced `.gcode.3mf` files
are refused — send those with `a1_mini_send_print.py`.

### Risks of headless slicing (read before unattended use)

Slicing without a human in front of the preview removes the last
visual checkpoint before plastic moves. Concretely:

1. **No preview means no sanity check on geometry.** Wrong STL
   units/scale, an orientation that needs supports but gets none,
   overhangs the auto-`--orient` heuristic handles badly, or a part
   auto-`--arrange`d differently than you expected all slice
   *successfully* — and waste filament, fail mid-air, or (worst case)
   drag a hot nozzle through detached spaghetti for hours. The
   script's header summary + confirmation prompt is a deliberately
   thin substitute: it shows time/filament/temperatures, not geometry.
   Don't pass `--yes` until the model + profile combination has
   printed successfully at least once.
2. **A "successful" slice can still carry wrong settings.** The CLI
   does not resolve profile `inherits` chains, so a half-flattened
   profile can slice cleanly with missing/default temperatures,
   speeds, or cooling. The script hard-rejects jobs exceeding A1-mini
   hardware maxima (bed > 80 °C, nozzle > 300 °C — a wrong-printer
   profile symptom) and refuses H2D/IDEX-flavoured output, but it
   cannot detect a *subtly* wrong profile (e.g. PETG temps applied to
   PLA).
3. **Settings-precedence surprises with project 3MFs.** CLI-loaded
   profiles silently override whatever the project file embeds
   (flags > `--load-*` > 3MF). Loading a stale profile bundle against
   a carefully-tuned project 3MF re-slices it with the stale settings
   and no warning beyond the script's NOTE line.
4. **Slicer-version drift.** Profile keys get renamed and slicing
   behaviour changes between BambuStudio releases. Pin the AppImage/
   binary version (the recipe here was developed against
   v02.06.00.51) and re-validate after any upgrade — same advice as
   pinning printer firmware.
5. **This exact A1-mini invocation is still not empirically
   verified** (see the NOTE above) — the P2S and H2D flows were run
   for real in PR #23; the A1-mini variant is the same AppImage on a
   simpler codepath, but treat the first failure as a profile
   flattening/patching problem, not a script bug.
6. **Compute cost lands wherever the script runs.** A slice is
   CPU-heavy and can take minutes on a Pi; the script bounds it with
   `--slice-timeout` (default 900 s) and cleans its temp dir, but
   don't point a tight automation loop at it without queueing —
   that's what the relay's `/print_stl` route (Steps 5–6) is for.
7. **One command now goes from file to moving hardware.** Combining
   slice + upload + start collapses the natural pause where someone
   used to look at the G-code. Keep the confirmation prompt for
   interactive use, and for automation route through the relay's
   safety envelope (`LIMITS`, allow-listed filaments) rather than
   `--yes` on this script — the script's checks are a subset of the
   relay's, and there is no hardware interlock in either.

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
3. **Step 3**: slice a small cube with an **A1 mini** profile, fill
   in the placeholders at the top of
   `scripts/a1_mini_send_print.py`, run it with `--upload-only`
   first, then the full run with the bed clear. Do **not** reuse the
   H2D cube file — the script refuses it anyway. (~15 min)
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
  isolated-client Wi-Fi VLAN** (or between two devices on
  `byu-devices`, which blocks client-to-client traffic) — run the
  smoke test from the Pi, or put printer + laptop on a shared phone
  hotspot, before concluding anything is wrong with the printer.
- **Don't change the printer-side file/storage layout** — uploading
  to a non-default path is the confirmed root cause of the
  `0500-4003` "unable to parse file" failure that cost `ac-dev-lab`
  weeks (see field notes above).
- **Don't rely on `set_bed_temperature()`** — it is a confirmed no-op
  on the A1 mini; bake setpoints into the G-code or send
  `M190`/`M109` via `printer.gcode()`.
