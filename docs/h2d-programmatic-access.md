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
| **B. LAN / Developer Mode** | FTPS upload to `ftps://<printer>:990` then MQTT-over-TLS to `mqtt://<printer>:8883` | FTP user `bblp` + LAN access code; MQTT user `bblp` + LAN access code | No | Works the same way as on X1/P1/A1 *if Developer Mode is enabled*; community libraries (e.g. `bambulabs_api`) report H2D as "not yet tested".[^openbambu-ftp][^openbambu-mqtt][^bambulabs-readme] |
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

[^paris-mqtt-tls]: Iqbal Luqman Bin Mohd Paris, Mohamed Hadi Habaebi,
    and Alhareth Mohammed Zyoud, *Implementation of SSL/TLS Security
    with MQTT Protocol in IoT Environment*, Wireless Personal
    Communications 132:163–182 (Jul 2023).
    <https://doi.org/10.1007/s11277-023-10605-y>. Quantifies the
    overhead and battery-life cost of enabling TLS on top of MQTT in a
    constrained-IoT setup; cited here only as motivation for treating
    MQTT-over-TLS as a non-trivial cost on small gateway hardware.
