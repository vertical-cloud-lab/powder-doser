# Programmatic and remote printing on the Bambu Lab H2D

This note collects what is currently known (as of mid-2026) about driving
a Bambu Lab H2D printer from code — both from the local network and over
the internet — so that the *powder-excavator* workflow can dispatch
sliced jobs without a human at the slicer. It is research notes, not a
finished integration: H2D-specific support in the open-source ecosystem
is still maturing and several of the protocol details below are
documented by the community rather than by Bambu Lab.

> [!IMPORTANT]
> Bambu Lab rolled out a "printer control authorization" system starting
> with X-series firmware and is extending it to the P-series and
> A-series; once enabled, *starting a print job from third-party
> software requires routing the job through Bambu Connect*, unless the
> printer is in **Developer Mode** (LAN-only, no Bambu Cloud). The same
> framework is expected to apply to the H2D. Plan integrations around
> one of the three modes below.[^bambu-third-party]

## TL;DR — three viable modes

| Mode | Transport | Auth | Cloud needed? | Status for H2D |
|---|---|---|---|---|
| **A. Bambu Cloud** | HTTPS to `api.bambulab.com` (file upload + start) and MQTT-over-TLS to `us.mqtt.bambulab.com:8883` (status) | Bambu account → access/refresh token, MQTT user `u_{USER_ID}` / password = access token | Yes | Same endpoints as other models; subject to the new authorization system, so most write commands now require Bambu Connect.[^bambu-third-party][^openbambu-mqtt] |
| **B. LAN / Developer Mode** | FTPS upload to `ftps://<printer>:990` then MQTT-over-TLS to `mqtts://<printer>:8883` | FTP user `bblp` + LAN access code; MQTT user `bblp` + LAN access code | No | Works the same way as on X1/P1/A1 *if Developer Mode is enabled*; community libraries (e.g. `bambulabs_api`) report H2D as "not yet tested".[^openbambu-ftp][^openbambu-mqtt][^bambulabs-readme] |
| **C. Bambu Connect (sanctioned third-party)** | Bambu Connect handles transport on behalf of the slicer | Cloud account login inside Bambu Connect | Yes (for login) | The path Bambu Lab tells third-party software (e.g. OrcaSlicer) to use under the new authorization system.[^bambu-third-party] |

## A. Cloud submission

The undocumented-but-community-reverse-engineered cloud surface used by
Bambu Studio and the Handy app exposes:

- **HTTPS base URL:** `https://api.bambulab.com` (China region:
  `https://api.bambulab.cn`). Endpoints follow the pattern
  `/v1/{service}/...`, e.g. `/v1/iot-service/api/user/...` for device
  and project operations.[^openbambu-cloudhttp]
- **Authentication:** log in with the Bambu account (email/password,
  with an emailed verification code on first use), receive an
  access token + refresh token, and send `Authorization: Bearer
  <ACCESS_TOKEN>` on every request.[^openbambu-cloudhttp]
- **MQTT for status / commands:** connect to
  `mqtts://us.mqtt.bambulab.com:8883` with TLS;
  username `u_{USER_ID}` (the user id is returned by
  `GET /v1/design-user-service/my/preference`); password is the access
  token.[^openbambu-mqtt]
- **Sending a print** in cloud mode is a two-step flow: upload the
  sliced `.3mf` to project storage, then publish a `print/project_file`
  command on `device/{DEVICE_ID}/request` referencing the uploaded file;
  status comes back on `device/{DEVICE_ID}/report`.[^openbambu-mqtt]

Note that under the new authorization system (see warning above) "start
a print job" is one of the *restricted* commands when invoked from
non-Bambu software, while pure status reads (push notifications used by
e.g. Home Assistant) are not.[^bambu-third-party]

## B. LAN / Developer Mode submission

This is the path most relevant to an autonomous powder-handling rig
sitting next to the printer. Enable **Developer Mode** on the printer
(Settings → General → Developer Mode) so that the new authorization
system does not block third-party prints.[^bambu-third-party]

### Step 1 — Upload the sliced file via FTPS

The printer runs an implicit-FTPS server on port 990:[^openbambu-ftp]

```
ftps://<PRINTER_IP>:990
TLS:      implicit
Username: bblp
Password: <LAN access code shown on the printer's screen>
```

Place the sliced job (typically a `gcode.3mf` produced by Bambu Studio /
OrcaSlicer) under `/` (printer SD card root) or `/cache/` — the path
matters because the start-print command references it by URL.

### Step 2 — Trigger the print over MQTT-over-TLS

Connect to the printer's broker:[^openbambu-mqtt]

```
mqtts://<PRINTER_IP>:8883
TLS:      yes (self-signed; pin or trust the printer cert; see OpenBambuAPI tls.md)
Username: bblp
Password: <LAN access code>
```

Subscribe to `device/<SERIAL>/report` and publish the start command on
`device/<SERIAL>/request`. The minimum payload to start a print of a
file already on the SD card is:[^openbambu-mqtt]

```json
{
  "print": {
    "sequence_id": "0",
    "command": "project_file",
    "param": "Metadata/plate_1.gcode",
    "project_id": "0",
    "profile_id": "0",
    "task_id": "0",
    "subtask_id": "0",
    "subtask_name": "",
    "url": "ftp:///cache/myfile.gcode.3mf",
    "md5": "",
    "timelapse": true,
    "bed_type": "auto",
    "bed_levelling": true,
    "flow_cali": true,
    "vibration_cali": true,
    "layer_inspect": true,
    "ams_mapping": "",
    "use_ams": false
  }
}
```

The `param` field selects which plate inside the `.3mf` is printed;
`url` is the path the printer should fetch the file from (the FTP path
where step 1 deposited it). Status, progress and errors come back as
JSON messages with `command: "push_status"` (and a periodic full
snapshot with `command: "push_all"`) on the `…/report` topic.[^openbambu-mqtt]

## C. Bambu Connect

If we cannot keep the printer in Developer Mode (for example, because
we still want the cloud features that Developer Mode disables), the
sanctioned route is to install **Bambu Connect** alongside the
third-party tool. Bambu Connect logs in with the Bambu Lab account and
forwards sliced G-code / 3MF to the printer through the secured
channel; the third-party tool only has to hand the file off to Bambu
Connect.[^bambu-third-party] OrcaSlicer is the integration demo Bambu
Lab themselves point at.

## Open-source Python libraries

The following are community-maintained and unofficial. Pin the version,
expect occasional breakage when Bambu changes the protocol, and verify
against your specific firmware.

- **`bambulabs_api`** (BambuTools/bambulabs_api). MIT-licensed Python
  wrapper around the LAN MQTT+FTPS protocol. Install: `pip install
  bambulabs_api`. The README's "Known Limitations" explicitly states
  *"H2D printers have not been tested yet"*, so treat H2D support as
  experimental and verify each call.[^bambulabs-readme]

  ```python
  import bambulabs_api as bl

  printer = bl.Printer(ip="192.168.1.200",
                       access_code="12345678",
                       serial="AC12309BH109")
  printer.connect()
  print(printer.get_state())
  printer.disconnect()
  ```

- **`bambu-connect`** / **`pybambu`** — similar LAN-mode wrappers
  popular in Home Assistant–style integrations.

- **`ha-bambulab`** — Home Assistant custom integration; useful as a
  reference for the read-only `push_status` / `push_all` MQTT message
  shapes (these are the messages that remain unrestricted under the new
  authorization system).[^bambu-third-party]

- **OpenBambuAPI** (Doridian/OpenBambuAPI) — not a library, but the
  most complete community protocol reference; the cloud HTTP, LAN MQTT,
  FTPS and TLS pages cited throughout this note live there.[^openbambu-mqtt][^openbambu-ftp][^openbambu-cloudhttp]

## Prior art in the AC `ac-dev-lab` (A1 mini)

The Acceleration Consortium's
[`AccelerationConsortium/ac-dev-lab`](https://github.com/AccelerationConsortium/ac-dev-lab)
training-lab repo has working code (against a **Bambu A1 mini**, not an
H2D) that exercises the same LAN MQTT + FTPS path described above. Useful
prior art when porting to the H2D:

- **`src/ac_training_lab/bambu_a1_mini/_scripts/manual_print.py`** — a
  minimal, end-to-end example that uses `bambulabs_api` to (1) read a
  `.gcode` template, (2) wrap it as `Metadata/plate_1.gcode` inside an
  in-memory zip, (3) `printer.upload_file(...)` over FTPS, and (4)
  `printer.start_print(upload_fname, 1)` over MQTT. The same shape
  should work for the H2D's plate 1 once the file is sliced with an H2D
  profile.[^acdevlab-manual-print]
- **`src/ac_training_lab/bambu_a1_mini/device.py`** — runs on a
  Raspberry Pi 4B next to the printer and bridges an external MQTT
  broker (subscribed to a `request` topic) to the printer: it loads a
  G-code template, rewrites the embedded nozzle/bed/speed/fan setpoints
  with `M104/M109/M140/M190` regex-style replacements, writes a temp
  G-code, and shells out to a `print.py` that pushes the file. This is a
  good template for an unattended powder-excavator dispatcher.[^acdevlab-device]
- **`src/ac_training_lab/bambu_a1_mini/README.md`** plus the
  [tracking issues](https://github.com/AccelerationConsortium/ac-dev-lab/issues)
  worth reading before reimplementing for H2D — in particular
  [#147 *Set up remote Python control on A1 mini*](https://github.com/AccelerationConsortium/ac-dev-lab/issues/147),
  [#149 *Set up A1 mini*](https://github.com/AccelerationConsortium/ac-dev-lab/issues/149),
  [#160 *Integration of Bambu 3D Printer with colab & hugging face*](https://github.com/AccelerationConsortium/ac-dev-lab/issues/160),
  [#168 *A1 Mini 3D printer — Self-driving Lab for MSE403H1*](https://github.com/AccelerationConsortium/ac-dev-lab/issues/168),
  and [PR #182 *MQTT client … for controlling a Bambu 3D printer*](https://github.com/AccelerationConsortium/ac-dev-lab/pull/182).

Things from that prior art that should carry over to the H2D unchanged:

- The `(IP, ACCESS_CODE, SERIAL)` triple as the only printer credentials
  the LAN path needs, sourced from a `my_secrets.py` that is **not**
  committed.
- Wrapping the print payload as `Metadata/plate_1.gcode` inside a zip
  and uploading it under any filename, then calling `start_print(fname,
  plate_index)`.
- Putting a small Pi (Pi 4B / Pi Zero 2 W) on the same LAN as the
  printer and using an *external* MQTT broker (HiveMQ Cloud, mosquitto)
  for orchestration, rather than driving the printer's own broker from
  the cloud.

Things that almost certainly will **not** carry over and need re-work
for the H2D:

- The G-code rewriting in `device.py` assumes single-extruder A1 mini
  setpoints (`M104 S220`, `M140 S65`, etc.). On the H2D the sliced job
  contains per-tool metadata for both extruders (and possibly the
  laser / cutter), so any setpoint rewriting has to be tool-aware or
  done at the slicer level instead.
- `bambulabs_api`'s README still flags H2D as untested,[^bambulabs-readme]
  so behaviours like `start_print(fname, plate)` and the status-field
  parsing in `get_state()` / `get_bed_temperature()` should be verified
  against an actual H2D before relying on them.

## Remote slicing (STL → 3MF)

**Short answer: yes, but not on Bambu Lab's servers.** Bambu Cloud only
accepts already-sliced project files; there is no public endpoint that
takes an STL and returns a `.gcode.3mf`.[^bambu-cloud-no-slice] Remote
slicing therefore means running a slicer headlessly on a machine *you*
control (a workstation, a CI runner, or a container) and then handing
the resulting `.gcode.3mf` to one of the three submission modes above.

Two practical paths, both based on the PrusaSlicer-derived CLI that
Bambu Studio and OrcaSlicer inherit:

### 1. Bambu Studio CLI (`bambu-studio --slice`)

`bambu-studio` ships an officially documented CLI mode (no GUI required
at runtime, but on Linux it still links wxWidgets, so containerised
runs typically wrap it in `xvfb-run`).[^bambu-studio-cli] The wiki's
own *"Slice stls"* example is exactly this STL → sliced-`.3mf` flow:

```bash
xvfb-run -a bambu-studio \
  --orient --arrange 1 \
  --load-settings  "machine.json;process.json" \
  --load-filaments "filament.json" \
  --slice 0 \
  --export-3mf out.gcode.3mf \
  part.stl
```

- `--load-settings` / `--load-filaments` take JSON profiles exported
  from a desktop Bambu Studio that has an **H2D** machine profile
  installed — this is what gives the resulting `.gcode.3mf` the
  per-tool / IDEX / laser metadata the H2D needs.[^bambu-studio-cli]
- `--orient` and `--arrange 1` are needed for raw STL input because,
  unlike a `.3mf`, an STL has no plate layout.[^bambu-studio-cli]
- `--slice 0` slices all plates; pass a 1-based index to slice one
  specific plate.[^bambu-studio-cli]
- The output `.gcode.3mf` is the file you upload via FTPS in mode B
  and reference from `print.project_file`.

#### Verified end-to-end locally

To remove all doubt that this is a real, working CLI rather than a
documented-but-broken side door, the flow above was exercised against
the official BambuStudio v02.06.00.51 Linux AppImage on Ubuntu 24.04
with a 12-triangle cube STL (684 bytes) generated on the fly:

```bash
# 1. Pull the official AppImage from the BambuStudio releases page.
curl -sLo bambu.AppImage \
  https://github.com/bambulab/BambuStudio/releases/download/v02.06.00.51/BambuStudio_ubuntu-24.04-v02.06.00.51-20260417160415.AppImage
chmod +x bambu.AppImage

# 2. Headless slice (software GL is enough for the thumbnail step).
LIBGL_ALWAYS_SOFTWARE=1 GALLIUM_DRIVER=llvmpipe \
xvfb-run -a -s "-screen 0 1280x1024x24" ./bambu.AppImage \
  --orient 1 --arrange 1 \
  --load-settings  "machine.json;process.json" \
  --load-filaments "filament.json" \
  --slice 0 --export-3mf cube.gcode.3mf --outputdir out cube.stl
```

Result with the *flattened P2S example profiles linked from the
BambuStudio CLI wiki* (`machine.json` / `process.json` /
`filament.json` from the wiki's own attachments):

- `out/cube.gcode.3mf` (≈41 KB, valid 3MF/OPC zip), containing the
  same internal layout that mode B's `print.project_file` references —
  including a `Metadata/plate_1.gcode` entry (271 KB), a
  `Metadata/plate_1.gcode.md5`, and a `Metadata/slice_info.config`.
- `out/result.json` reports `"return_code": 0`-equivalent slice
  statistics: 100 layers @ 0.20 mm, ~3.63 g of filament, 8 m 41 s
  print time, 12 triangles in, full per-feature time breakdown out.

Repeating the exact same invocation but pointing
`--load-settings`/`--load-filaments` at the **bundled H2D profiles**
that ship inside the AppImage
(`resources/profiles/BBL/machine/Bambu Lab H2D 0.4 nozzle.json`,
`resources/profiles/BBL/process/0.20mm Standard @BBL H2D.json`,
`resources/profiles/BBL/filament/Bambu PLA Basic @BBL H2D.json`)
fails on purpose, with:

```
[error] plate 1 : some filaments can not be mapped under auto mode for
        multi extruder printer
run found error, return -66, exit...
```

That is exactly the H2D / IDEX caveat called out further down: the
H2D needs an explicit per-extruder filament list and the bundled
profiles are *templates* (they declare `inherits: "Bambu PLA Basic
@base"` etc.) which the CLI does not resolve — the wiki itself notes
*"the config file should be a full config instead of the one used in
resources/profiles/BBL/filament"*.[^bambu-studio-cli]

**Reproducing one filament profile per tool on the H2D — what
actually works:** flatten the inheritance chain into a single full
config per role, fix three identity fields, and pass an explicit
manual filament-to-extruder map. With the same AppImage and cube STL
as above:

```bash
# Walk machine/process/filament profiles' "inherits" chain and merge
# parents into children → h2d_machine_flat.json, h2d_process_flat.json,
# h2d_filament_flat.json. Then patch the resulting machine config so
# the CLI's compatibility check accepts it:
#   machine.from         = "system"   (so new_printer_system_name == name)
#   machine.inherits     = ""         (do not look up a missing parent)
#   machine.printer_settings_id = "Bambu Lab H2D 0.4 nozzle"
# (mirror from=system / inherits="" on the process and filament configs).

xvfb-run -a -s "-screen 0 1280x1024x24" ./bambu.AppImage \
  --orient 1 --arrange 1 \
  --load-settings  "h2d_machine_flat.json;h2d_process_flat.json" \
  --load-filaments "h2d_filament_flat.json;h2d_filament_flat.json" \
  --filament-map-mode "Manual" \
  --filament-map "1,2" \
  --slice 1 --export-3mf cube_h2d.gcode.3mf --outputdir h2d_out cube.stl
```

This run completes with `result.json` reporting `"return_code": 0`,
`"error_string": "Success."`, and produces a valid 36 KB
`cube_h2d.gcode.3mf`. The `Metadata/plate_1.gcode` inside the archive
carries the IDEX header the printer actually expects:

```
; filament_map      = 1,2
; filament_map_2    = 0,1
; filament_map_mode = Manual
; printer_extruder_id = 1,2
; print_extruder_id   = 1,2
; master_extruder_id  = 2
```

i.e. filament 1 → left extruder, filament 2 → right extruder, with
explicit master-extruder selection — exactly the per-tool metadata
the IDEX-aware firmware needs and that mode B's `print.project_file`
references.[^cli-empirical] Two non-obvious gotchas surfaced by this
exercise:

- **`--slice 0` (all plates) silently skips the manual filament-map
  setup**: the CLI's manual-mode block guards on `plate_to_slice != 0`,
  so for STL → 3MF on a multi-extruder machine you must pass
  `--slice 1` (or another explicit plate index). With `--slice 0`,
  even correct flags still fail with `"some filaments can not be
  mapped under manual mode for multi extruder printer"`.
- **`--filament-map-mode` defaults to `Auto For Flush`** on the H2D,
  which then trips the auto-mapping check; passing `Manual` is what
  switches the message from `under auto mode` to `under manual mode`
  and makes the explicit `--filament-map` array load.

### 2. OrcaSlicer CLI

OrcaSlicer is a Bambu Studio fork and accepts the same general CLI
shape; it also retains the upstream PrusaSlicer flags (`--export-gcode`,
`--load <profile.ini>`, positional STL).[^orcaslicer-cli] In a
container it likewise wants `xvfb-run` because of wxWidgets. OrcaSlicer
is useful when you want a profile that is not (yet) shipped in Bambu
Studio, or when you want to pin a specific slicer version separately
from Bambu Lab's release cadence.

### Suggested pipeline for powder-excavator

1. Generate or fetch the STL.
2. Submit it to a self-hosted slicer worker (a container running
   `bambu-studio --slice` or `OrcaSlicer --export-gcode`) with the
   pinned H2D profile bundle. Capture the resulting `.gcode.3mf`.
3. Hand the `.gcode.3mf` to mode A (cloud), B (LAN MQTT + FTPS), or C
   (Bambu Connect) exactly as documented above.

### What *won't* work

- **No Bambu Cloud server-side slicer.** The cloud REST API only
  exposes file-management and print-control endpoints; STL → G-code
  conversion is not part of the surface.[^bambu-cloud-no-slice]
- **No "slice on the printer."** The printer firmware consumes
  `.gcode.3mf` (or raw `.gcode`) only.
- **Don't ship STL through `print.project_file`.** That command
  expects an already-sliced project file referenced by an FTP URL on
  the printer; pointing it at a raw STL will fail.[^openbambu-mqtt]

## H2D-specific caveats

The H2D's hardware features (true IDEX dual extruder, optional laser /
vinyl-cutter modules, larger build volume) are exposed in the slicer
and in the `.3mf` job as **per-tool metadata**: each region/object is
tagged with the tool that should print or cut it. A `.3mf` sliced for
the H2D therefore carries a multi-tool plate that older Bambu printers
do not understand; conversely, none of the open-source LAN libraries
above currently advertise tested H2D support.[^bambulabs-readme] When
integrating, plan to:

1. Slice on a machine that has an **H2D profile** in Bambu Studio or
   OrcaSlicer so the resulting `.gcode.3mf` contains the right tool /
   laser metadata. Pin the slicer version used by the pipeline.
2. Confirm the firmware version on the printer before relying on
   third-party prints — the authorization system, the set of
   restricted MQTT commands and the Developer-Mode toggle are all
   firmware-gated.[^bambu-third-party]
3. Keep cloud (mode A) and LAN (mode B) credentials *separate* and
   stored as secrets (not in the repo). LAN access codes rotate when
   the user changes them on the screen; cloud refresh tokens expire.

## Security considerations

- The LAN MQTT broker uses a self-signed certificate; pin it or trust
  it explicitly rather than disabling verification, and treat the LAN
  access code as a shared secret (anyone on the LAN with it can drive
  the printer).[^openbambu-mqtt]
- TLS on MQTT is mandatory on Bambu printers but is not free —
  experimental work in the IoT literature shows that MQTT-over-TLS can
  add substantial CPU and energy overhead versus plain MQTT, which is
  worth keeping in mind for very constrained gateway hardware.[^paris-mqtt-tls]
- Cloud submission relies on undocumented endpoints that Bambu can
  change at any time; under the new authorization system, expect
  third-party `start_print` calls to be rejected unless they go through
  Bambu Connect or the printer is in Developer Mode.[^bambu-third-party]

## References

[^bambu-third-party]: Bambu Lab Wiki, *Third-party Integration with
    Bambu Lab Products*. <https://wiki.bambulab.com/en/software/third-party-integration>
    (consulted 2026-05). Describes the new authorization control system,
    the list of restricted commands (binding/unbinding, firmware
    upgrade, remote video, **starting a print job**, controlling
    movement/temperature/fans/AMS/calibration), the unrestricted
    operations (status pushes, SD-card prints, MicroSD firmware
    updates), the Bambu Connect middleware, and Developer Mode
    semantics.

[^openbambu-mqtt]: Doridian, *OpenBambuAPI* — `mqtt.md`.
    <https://github.com/Doridian/OpenBambuAPI/blob/main/mqtt.md>.
    Documents both the cloud broker
    (`mqtts://us.mqtt.bambulab.com:8883`, user `u_{USER_ID}`, password
    = access token) and the local broker (`mqtts://<printer>:8883`, user
    `bblp`, password = LAN access code), the `device/{ID}/request` and
    `device/{ID}/report` topics, and the JSON shape of
    `print.project_file`, `print.gcode_file`, `push_status` and
    `push_all` messages quoted above.

[^openbambu-ftp]: Doridian, *OpenBambuAPI* — `ftp.md`.
    <https://github.com/Doridian/OpenBambuAPI/blob/main/ftp.md>.
    `ftps://<DEVICE_IP>:990`, implicit TLS, user `bblp`, password = LAN
    access code.

[^openbambu-cloudhttp]: Doridian, *OpenBambuAPI* — `cloud-http.md`.
    <https://github.com/Doridian/OpenBambuAPI/blob/main/cloud-http.md>.
    Documents the cloud REST surface used by Bambu Studio/Handy,
    including the user / device / project endpoints referenced from
    `mqtt.md`.

[^bambulabs-readme]: BambuTools, *bambulabs_api*. README.
    <https://github.com/BambuTools/bambulabs_api/blob/main/README.md>.
    Quoted statement under "Known Limitations": *"H2D printers have not
    been tested yet."* Source for the install command, basic `Printer`
    usage example, and the `(IP, access_code, serial)` constructor
    signature shown above.

[^acdevlab-manual-print]: AccelerationConsortium, *ac-dev-lab* —
    `src/ac_training_lab/bambu_a1_mini/_scripts/manual_print.py`.
    <https://github.com/AccelerationConsortium/ac-dev-lab/blob/main/src/ac_training_lab/bambu_a1_mini/_scripts/manual_print.py>.
    End-to-end A1-mini example: reads a `.gcode` file, wraps it as
    `Metadata/plate_1.gcode` inside an in-memory zip, calls
    `bambulabs_api.Printer(IP, ACCESS_CODE, SERIAL).upload_file(...)`
    over FTPS, then `printer.start_print(upload_fname, 1)` over MQTT.

[^acdevlab-device]: AccelerationConsortium, *ac-dev-lab* —
    `src/ac_training_lab/bambu_a1_mini/device.py`.
    <https://github.com/AccelerationConsortium/ac-dev-lab/blob/main/src/ac_training_lab/bambu_a1_mini/device.py>.
    Pi-side MQTT bridge: subscribes to a `REQUEST_TOPIC`, rewrites the
    embedded `nozzle_temperature` / `textured_plate_temp` /
    `M104`/`M109`/`M140`/`M190` setpoints in a G-code template based on
    the request's `parameters`, and shells out to a `print.py` that
    pushes the file to the printer.

[^bambu-cloud-no-slice]: Bambu Lab's documented cloud surface (file
    management, project upload, start/stop/status, AMS, etc.) does not
    include a server-side slicer; STLs must be sliced client-side
    before upload. Confirmed against the community-maintained Bambu
    Cloud API reference at
    <https://github.com/coelacant1/Bambu-Lab-Cloud-API> (consulted
    2026-05) and against `Doridian/OpenBambuAPI/cloud-http.md`, neither
    of which lists a `/slice` or equivalent endpoint.

[^bambu-studio-cli]: Bambu Lab, *BambuStudio* — official
    *Command Line Usage* wiki.
    <https://github.com/bambulab/BambuStudio/wiki/Command-Line-Usage>
    (consulted 2026-05). Documents the `bambu-studio` CLI, including
    `--slice plate_index` (`0` = all plates), `--export-3mf`,
    `--load-settings "machine.json;process.json"`,
    `--load-filaments "filament1.json;..."`, `--orient`, `--arrange`,
    `--outputdir`, `--export-slicedata`, `--info`, and the three-tier
    settings precedence (CLI flags > `--load-*` files > settings
    embedded in the `.3mf`). The wiki's third worked example —
    *"Slice stls"* — explicitly slices a `.stl` input
    (`./bambu-studio --orient --arrange 1 --load-settings ... --load-filaments ... --slice 0 --export-3mf output.3mf test_data/boat.stl`),
    confirming STL → sliced-`.3mf` is a first-class CLI use case. On
    Linux, headless runs in CI/containers typically wrap the binary in
    `xvfb-run` because of the wxWidgets dependency.

[^orcaslicer-cli]: SoftFever, *OrcaSlicer* — README and
    PrusaSlicer-derived CLI.
    <https://github.com/SoftFever/OrcaSlicer>. Accepts the upstream
    PrusaSlicer flags (`--export-gcode`, `--load <profile.ini>`,
    positional STL input); same `xvfb-run` caveat as Bambu Studio for
    headless Linux runs. See also the upstream PrusaSlicer
    *Command-Line Usage* wiki:
    <https://github.com/prusa3d/PrusaSlicer/wiki/Command-Line-Interface>.

[^cli-empirical]: Empirically verified for this PR on
    2026-05-07 against the official BambuStudio v02.06.00.51 Linux
    AppImage
    (`BambuStudio_ubuntu-24.04-v02.06.00.51-20260417160415.AppImage`)
    on Ubuntu 24.04, run under
    `xvfb-run -a -s "-screen 0 1280x1024x24"` with
    `LIBGL_ALWAYS_SOFTWARE=1 GALLIUM_DRIVER=llvmpipe` for the OpenGL
    thumbnail step. Input was a 12-triangle 20 mm cube binary STL.
    With the wiki's flattened example profiles
    (<https://github.com/user-attachments/files/26363641/machine.json>,
    <https://github.com/user-attachments/files/26363644/process.json>,
    <https://github.com/user-attachments/files/26363647/filament.json>,
    P2S 0.4 nozzle / 0.20 mm Standard / Bambu PLA Basic), the slice
    completed and produced a valid 41 KB `cube.gcode.3mf` archive
    containing `Metadata/plate_1.gcode` (271 KB),
    `Metadata/plate_1.gcode.md5`, `Metadata/slice_info.config`,
    `Metadata/project_settings.config`, plus a `result.json` with
    100-layer / 8 m 41 s / 3.63 g slice statistics. Re-running the
    same command against the bundled H2D 0.4 nozzle machine + 0.20 mm
    H2D process + Bambu PLA Basic H2D filament profiles fails with
    `"plate 1 : some filaments can not be mapped under auto mode for
    multi extruder printer"` (`return_code: -66`), demonstrating the
    H2D-specific IDEX caveat described in this section. Resolving the
    `inherits` chain of those bundled profiles into flat full configs
    (and patching `from = "system"`, `inherits = ""`, and
    `printer_settings_id = "Bambu Lab H2D 0.4 nozzle"` on the machine
    config so the CLI's compatibility check accepts it), then passing
    two filament profiles plus
    `--filament-map-mode "Manual" --filament-map "1,2" --slice 1`,
    *succeeds* on this same fresh AppImage: `result.json` reports
    `"return_code": 0` / `"error_string": "Success."`, and the
    resulting 36 KB `cube_h2d.gcode.3mf` contains a
    `Metadata/plate_1.gcode` (~249 KB) whose header carries the IDEX
    assignment (`filament_map = 1,2`, `filament_map_mode = Manual`,
    `printer_extruder_id = 1,2`, `master_extruder_id = 2`). The same
    invocation with `--slice 0` (all plates) instead of `--slice 1`
    silently re-trips the `"can not be mapped under manual mode"`
    error because the BambuStudio CLI's manual-filament-map setup is
    guarded by `plate_to_slice != 0` (see `src/BambuStudio.cpp`
    lines ~6491-6700 in tag `v02.06.00.51`).

[^paris-mqtt-tls]: Iqbal Luqman Bin Mohd Paris, Mohamed Hadi Habaebi,
    and Alhareth Mohammed Zyoud, *Implementation of SSL/TLS Security
    with MQTT Protocol in IoT Environment*, Wireless Personal
    Communications 132:163–182 (Jul 2023).
    <https://doi.org/10.1007/s11277-023-10605-y>. Quantifies the
    overhead and battery-life cost of enabling TLS on top of MQTT in a
    constrained-IoT setup; cited here only as motivation for treating
    MQTT-over-TLS as a non-trivial cost on small gateway hardware.
