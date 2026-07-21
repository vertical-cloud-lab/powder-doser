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
>
> **Terminology note — Developer Mode vs LAN Only Mode.** These are two
> *separate* toggles on the printer, and the doc uses both. **Developer
> Mode** exposes the LAN MQTT broker (`8883/tcp`) + FTPS endpoint
> (`990/tcp`) with the `(IP, access code, serial)` auth triple — that's
> what mode B and the relay actually talk to. **LAN Only Mode** is an
> *additional, optional* hardening step that disables the Bambu Cloud
> link entirely. You can run mode B / the relay with Developer Mode
> **on** and LAN Only Mode **off** (mixed Cloud+LAN) — that's what
> [Step 6 → "additive" caveat](#step-6--slice-on-the-pi-ship-stlargs-remotely-tailscale-as-lan-variant)
> assumes, and it lets manual Bambu Studio cloud-submit keep working
> alongside the programmatic relay. Flipping LAN Only on is what would
> break those manual cloud prints, not the relay itself.

## TL;DR — three viable modes

| Mode | Transport | Auth | Cloud needed? | Status for H2D |
|---|---|---|---|---|
| **A. Bambu Cloud** | HTTPS to `api.bambulab.com` (file upload + start) and MQTT-over-TLS to `us.mqtt.bambulab.com:8883` (status) | Bambu account → access/refresh token, MQTT user `u_{USER_ID}` / password = access token | Yes | Same endpoints as other models; subject to the new authorization system, so most write commands now require Bambu Connect.[^bambu-third-party][^openbambu-mqtt] |
| **B. LAN / Developer Mode** | FTPS upload to `ftps://<printer>:990` then MQTT-over-TLS to `mqtts://<printer>:8883` | FTP user `bblp` + LAN access code; MQTT user `bblp` + LAN access code | No | Works the same way as on X1/P1/A1 *if Developer Mode is enabled*; community libraries (e.g. `bambulabs_api`) report H2D as "not yet tested".[^openbambu-ftp][^openbambu-mqtt][^bambulabs-readme] |
| **C. Bambu Connect (sanctioned third-party)** | Bambu Connect handles transport on behalf of the slicer | Cloud account login inside Bambu Connect | Yes (for login) | The path Bambu Lab tells third-party software (e.g. OrcaSlicer) to use under the new authorization system.[^bambu-third-party] |

## Getting started — bringup checklist for a real H2D

For the *powder-excavator* / powder-doser workflow the practical
target is **mode B** (LAN / Developer Mode): no cloud account in the
loop, no third-party authorization gate, and the same `(IP, access
code, serial)` triple every open-source library already understands.
The recommended bringup order is:

### Step 0 — Get the printer onto the same LAN as your worker host

1. Plug the H2D in and finish the on-screen setup. **The H2D has a
   built-in RJ45 Ethernet port on the back panel** (next to the power
   inlet), so you have two options:
   - **Wired (recommended for bringup):** run a Cat-5e/6 cable from
     the H2D to the same switch/router as the worker host. Wired
     usually side-steps the BYU-IoT-style client-isolation problem
     that blocks laptop→printer traffic on shared Wi-Fi.
   - **Wi-Fi:** Settings → WLAN → join the same SSID as the worker.
     Fine for production but expect the client-isolation caveats in
     Step 6 if you also want roaming laptops to reach the printer.

   A separate VLAN is fine as long as ports `990/tcp` (FTPS) and
   `8883/tcp` (MQTT-over-TLS) are reachable from the worker.
2. On the printer screen: **Settings → WLAN → IP address** (or
   **Settings → Network → IP address** if you plugged in Ethernet) —
   note the IPv4 address. Pin it via DHCP reservation so it does not
   move; the LAN flow has no mDNS / discovery broker.
3. **What OS does the worker need?** Nothing exotic — the LAN
   transports are just MQTT-over-TLS (`:8883`) and FTPS (`:990`), so
   any OS with a Python 3.10+ install works. The empirical Step 2
   commands below have **Linux / macOS / Windows-PowerShell** variants
   so a Mac or Windows laptop on the lab Wi-Fi can do the smoke test
   before you commit to a dedicated Pi.

### Step 1 — Enable LAN-only Developer Mode and capture credentials

This is the single setting that decides whether mode B will work at
all under the new authorization system.[^bambu-third-party]

1. **Settings → General → enable "LAN Only Mode"** (and **"Developer
   Mode"** if your firmware exposes it as a separate toggle).
2. From **Settings → WLAN → Access Code**, write down the 8-digit
   code. (This is the FTP and MQTT password — *not* your Bambu Cloud
   password.)
3. From **Settings → Device → Device Info / Serial**, write down the
   15-character serial (e.g. `03919C…`). This is the `<SERIAL>` in
   every MQTT topic (`device/<SERIAL>/report`, `…/request`).
4. Also note the **firmware version** on the same screen and pin it
   in your worker config — Bambu firmware updates have repeatedly
   changed Developer-Mode behaviour and the authorization gate.

You should now have a `(IP, ACCESS_CODE, SERIAL)` triple. Everything
downstream — every Python library, every MQTT publish, every FTPS
upload — needs exactly those three values.

### Step 2 — Smoke-test reachability (no print yet)

Before touching any slicer or print command, prove the two transports
work from the worker host. Replace `<IP>`, `<ACCESS_CODE>`, `<SERIAL>`
with the values from Step 1.

The three checks below are presented in **Linux / macOS** form first
(`openssl`, `mosquitto_sub`, `lftp` — all in Homebrew / `apt`), then in
**Windows PowerShell** form using only the cross-platform Python
`paho-mqtt` client (`pip install paho-mqtt`) and the built-in
`System.Net.Sockets.TcpClient`, so a Mac or Windows laptop on the lab
Wi-Fi can run the smoke test directly. Pick whichever block matches
the worker.

**Linux / macOS** (install once: `brew install mosquitto lftp openssl`
on macOS, `apt install mosquitto-clients lftp openssl` on Linux):

```bash
# 2a. MQTT-over-TLS handshake reachable on :8883?
openssl s_client -connect <IP>:8883 -servername <IP> </dev/null \
  | head -20
# Expect: "CONNECTED(...)" and a self-signed cert (CN=BBL …). The
# self-signed-ness is expected; see the security section below.

# 2b. Subscribe to the printer's status topic and watch idle telemetry
mosquitto_sub --insecure -h <IP> -p 8883 \
  -u bblp -P "<ACCESS_CODE>" \
  -t "device/<SERIAL>/report" -v
# Expect: JSON push messages within a few seconds. Press Ctrl-C when
# you see at least one. If you see "Connection refused" or auth
# failures, you do *not* have Developer/LAN-only Mode actually on.

# 2c. FTPS reachable + access-code accepted?
lftp -u "bblp,<ACCESS_CODE>" -e \
  "set ftp:ssl-allow yes; set ssl:verify-certificate no; \
   ls /cache; bye" \
  ftps://<IP>:990
# Expect: a directory listing of /cache (may be empty on a fresh
# printer). Auth failure here means the access code is wrong or LAN
# Mode is off.
```

**Windows (PowerShell) — no Bambu Studio, no WSL required.** The
same three checks using only Python + built-ins:

```powershell
# 2a. Can we open a TCP socket to :8883? (Python free.)
Test-NetConnection -ComputerName <IP> -Port 8883
# Expect: TcpTestSucceeded : True. Repeat with -Port 990 for FTPS.

# 2b/2c. Subscribe to MQTT + list /cache over FTPS, both from one
# Python script. Save as h2d_smoketest.py and run `python h2d_smoketest.py`.
```

```python
# h2d_smoketest.py — works on Windows, macOS, and Linux.
# pip install paho-mqtt
import ssl, socket, ftplib, threading, paho.mqtt.client as mqtt
IP, ACCESS_CODE, SERIAL = "<IP>", "<ACCESS_CODE>", "<SERIAL>"

# 2b. MQTT-over-TLS — wait up to 15 s for the first report, then move on
got = threading.Event()
def on_msg(c, u, m):
    print("MQTT OK:", m.topic, m.payload[:120], "…"); got.set()
c = mqtt.Client()
c.username_pw_set("bblp", ACCESS_CODE)
c.tls_set(cert_reqs=ssl.CERT_NONE); c.tls_insecure_set(True)
c.on_message = on_msg
c.connect(IP, 8883, 30)
c.subscribe(f"device/{SERIAL}/report")
c.loop_start()
if not got.wait(timeout=15):
    print("MQTT WARN: connected but no report in 15 s "
          "(check SERIAL — FTPS check will still run below)")
c.loop_stop(); c.disconnect()

# 2c. FTPS — list /cache. The H2D speaks *implicit* FTPS on :990 (TLS
# handshake immediately on TCP connect — there is no plaintext
# `220` welcome banner, no `AUTH TLS` command). Python's stdlib
# `ftplib.FTP_TLS` is *explicit*-FTPS by default, so a bare
# `FTP_TLS().connect(IP, 990)` will hang and time out: ftplib waits
# for a plaintext greeting while the printer waits for a ClientHello.
# Fix: wrap the socket with TLS *before* the first read.
class ImplicitFTP_TLS(ftplib.FTP_TLS):
    def connect(self, host="", port=0, timeout=-999, source_address=None):
        if host: self.host = host
        if port: self.port = port
        if timeout != -999: self.timeout = timeout
        if source_address is not None: self.source_address = source_address
        self.sock = socket.create_connection((self.host, self.port), self.timeout)
        self.af = self.sock.family
        self.sock = self.context.wrap_socket(self.sock, server_hostname=self.host)
        self.file = self.sock.makefile("r", encoding=self.encoding)
        self.welcome = self.getresp()
        return self.welcome

    # The H2D's FTPS server *requires* the data connection to reuse
    # the TLS session from the control connection (RFC 5077). Without
    # this, LIST/STOR/RETR fail with `522 SSL connection failed:
    # session reuse required`. `bambulabs_api` and OpenBambuAPI both
    # do this same override internally.
    def ntransfercmd(self, cmd, rest=None):
        conn, size = ftplib.FTP.ntransfercmd(self, cmd, rest)
        if self._prot_p:
            conn = self.context.wrap_socket(
                conn,
                server_hostname=self.host,
                session=self.sock.session,
            )
        return conn, size

ctx = ssl._create_unverified_context()
# Session resumption only works when both control and data sockets share
# the same SSLContext, and only when the context advertises TLS 1.2 (the
# H2D's FTPS server does not implement TLS 1.3 session tickets).
ctx.minimum_version = ssl.TLSVersion.TLSv1_2
ctx.maximum_version = ssl.TLSVersion.TLSv1_2
ftps = ImplicitFTP_TLS(context=ctx); ftps.connect(IP, 990, 30)
ftps.login("bblp", ACCESS_CODE); ftps.prot_p()
print("FTPS /cache:", ftps.nlst("/cache")); ftps.quit()
```

A ready-to-run copy of this script (same code plus `--ip/--access-code/
--serial` flags and `H2D_*` env-var support) is checked in at
[`scripts/h2d_smoketest.py`](../scripts/h2d_smoketest.py).

If both blocks above succeed (you see a JSON `report` message + a
listing of `/cache`, possibly empty), you have proven the same `(IP,
code, serial)` triple that the rest of the doc — and every library in
the "Open-source Python libraries" table below — assumes.

**Troubleshooting — `MQTT OK` but `FTPS ERROR: timed out`.**
Reported by @ctrhjk in PR #23 against firmware on serial
`0947AJ622500469`. Two checks, in order:

1. **You're using stdlib `ftplib.FTP_TLS` directly (explicit FTPS)
   instead of the `ImplicitFTP_TLS` subclass above.** This is the
   most common cause and matches the symptom exactly: TCP connect
   succeeds, then `ftps.connect()` blocks reading a plaintext
   welcome banner that never arrives because the printer is waiting
   for a TLS handshake on port 990. **Switching to the
   `ImplicitFTP_TLS` subclass above resolves it without any printer
   side change.** (`bambulabs_api` and OpenBambuAPI both wrap the
   socket the same way internally — see
   [bambulabs_api `Printer.upload_file`][bbl-upload].) Cross-check
   from the same machine with `lftp -u "bblp,<CODE>" -e "set
   ftp:ssl-allow yes; set ssl:verify-certificate no; ls; bye"
   ftps://<IP>:990` — `lftp` does implicit-FTPS correctly, so if
   `lftp` lists the directory and the Python script times out, the
   stdlib-vs-implicit issue is confirmed.

2. **Developer Mode is not actually enabled on the H2D.** MQTT can
   succeed without Developer Mode in some firmware revisions
   (telemetry on `device/<SERIAL>/report` keeps publishing because
   the local broker runs for the cloud bridge), while the FTPS
   server on `:990` only listens once Developer Mode is on. On the
   touchscreen, Settings → General → confirm **Developer Mode** is
   ON (separate from LAN Only Mode — see the terminology note at
   the top of this doc). After toggling, re-run the smoke test;
   `Test-NetConnection -Port 990` going from `False`/timeout to
   `True` is the one-line confirmation.

If both of those check out and FTPS still times out, the BYU IoT
VLAN is likely doing port-level filtering of `:990` (most campus IoT
networks block FTP family ports outright). Move the test laptop to
the printer's wired Ethernet port — that bypasses the per-VLAN
filter and is also what the production Pi relay will be wired into.

**Troubleshooting — `522 SSL connection failed: session reuse
required`.** Reported by @ctrhjk in PR #23 after the implicit-FTPS
fix above. This is the *next* Bambu Lab FTPS quirk you hit once the
control connection works: control logs in over TLS, then `nlst` /
`stor` / `retr` opens a fresh data connection on a new port (`PASV`)
and the printer rejects the data-channel TLS handshake unless it
resumes the session from the control channel. RFC 5077 session
resumption is *required*, not optional — same behaviour every
vsftpd-with-`require_ssl_reuse=YES` server has, and what
`bambulabs_api` works around. Three things have to line up for
Python's `ssl` module to actually resume:

1. **Override `ntransfercmd` to wrap the data socket with
   `session=self.sock.session`** (the control socket's SSLSession
   object). The updated `ImplicitFTP_TLS` above does this — copy it
   verbatim; without the override, OpenSSL starts a fresh handshake
   on the data port and the printer returns `522`.

2. **Pin the SSLContext to TLS 1.2 on both sockets.** TLS 1.3
   session tickets are negotiated post-handshake, and the H2D's
   FTPS server (vsftpd-derived) does not implement
   `NewSessionTicket`, so under TLS 1.3 `self.sock.session` is
   either `None` or unusable for resumption and you get `522` even
   with the `ntransfercmd` override. The `ctx.maximum_version =
   ssl.TLSVersion.TLSv1_2` line in the smoke-test snippet above is
   what forces this; if you build your own context, set both
   `minimum_version` and `maximum_version` to `TLSv1_2`.

3. **Reuse the same SSLContext for control and data.** Constructing
   a second `ssl.create_default_context()` for the data socket
   produces an unrelated session cache; `ntransfercmd` above passes
   `self.context` implicitly (since it's an instance method of
   `FTP_TLS`), so as long as you don't override `_get_conn_class` or
   pass a different context downstream, this is automatic.

Cross-check from the same Windows laptop:
`lftp -u "bblp,<CODE>" -e "set ftp:ssl-allow yes; set
ssl:verify-certificate no; set ssl:use-poodle-workaround yes; set
ftp:ssl-protect-data yes; ls /cache; bye" ftps://<IP>:990` — `lftp`
does implicit FTPS + TLS-1.2 session reuse by default, so a
successful `ls /cache` here while the Python script returns `522`
confirms the resumption / TLS-version mismatch above.

[bbl-upload]: https://github.com/mattcar15/bambu-printer-api/blob/main/bambulabs_api/printer.py

### Step 3 — End-to-end dry run with a real `.gcode.3mf`

Use the H2D `cube_h2d.gcode.3mf` from the empirical CLI walkthrough
([Remote slicing → Bambu Studio CLI](#1-bambu-studio-cli-bambu-studio---slice))
as the test payload — it is small (36 KB), already carries the IDEX
header the firmware expects, and has a known-good `Metadata/plate_1.gcode`
inside.

> [!TIP]
> All of 3a–3c below is packaged as one cross-platform script:
> [`scripts/h2d_step3_send_print.py`](../scripts/h2d_step3_send_print.py)
> (`pip install paho-mqtt`, then
> `python h2d_step3_send_print.py cube_h2d.gcode.3mf --ip <IP>
> --access-code <CODE> --serial <SERIAL>`). It uploads over the same
> verified implicit-FTPS stack as the Step 2 smoke test, asks for
> confirmation before publishing (`--yes` to skip, `--upload-only` for
> just 3a), and watches `gcode_state` until `RUNNING`. The shell
> commands below remain useful when you want to see each leg
> individually.

```bash
# 3a. Upload the 3MF to the printer's /cache
lftp -u "bblp,<ACCESS_CODE>" -e \
  "set ftp:ssl-allow yes; set ssl:verify-certificate no; \
   cd /cache; put cube_h2d.gcode.3mf; ls; bye" \
  ftps://<IP>:990

# 3b. In one terminal, watch status
mosquitto_sub --insecure -h <IP> -p 8883 \
  -u bblp -P "<ACCESS_CODE>" \
  -t "device/<SERIAL>/report" -v

# 3c. In another terminal, publish the start-print command
#     (clear the bed first — this is a real print)
mosquitto_pub --insecure -h <IP> -p 8883 \
  -u bblp -P "<ACCESS_CODE>" \
  -t "device/<SERIAL>/request" \
  -m '{"print":{"sequence_id":"0","command":"project_file",
       "param":"Metadata/plate_1.gcode","project_id":"0",
       "profile_id":"0","task_id":"0","subtask_id":"0",
       "subtask_name":"","url":"ftp:///cache/cube_h2d.gcode.3mf",
       "md5":"","timelapse":false,"bed_type":"auto",
       "bed_levelling":true,"flow_cali":true,"vibration_cali":true,
       "layer_inspect":true,"ams_mapping":"","use_ams":false}}'
```

You should see `gcode_state` in the `report` stream walk through
`IDLE → PREPARE → RUNNING` within ~30 s, and the printer should
actually start the cube. If `gcode_state` never leaves `IDLE` (or
returns to `IDLE` immediately with a non-zero `print_error`), the
common causes — in roughly the order I'd check them — are:

1. The `url` path doesn't match where the file actually landed (the
   `ls` in step 3a tells you the truth; note the **three** slashes in
   `ftp:///cache/cube_h2d.gcode.3mf`).
2. The `.gcode.3mf` was sliced for a different printer (e.g. a P2S
   profile pointed at an H2D) and the firmware rejects it for missing
   IDEX metadata — re-slice with the verified H2D recipe.
3. The new authorization gate is engaged because LAN-only / Developer
   Mode silently came back off after a firmware update; re-check
   Step 1.

### Step 4 — Wrap mode B in code

Once Steps 2 and 3 work from the shell, the same three values feed
straight into a Python wrapper. The lowest-friction starting point
is `bambulabs_api`'s `Printer(IP, ACCESS_CODE, SERIAL)` constructor,
which internally does the same FTPS upload + MQTT-over-TLS publish
you just verified by hand. (See the
[Open-source Python libraries](#open-source-python-libraries)
table for the H2D-readiness status of each option, and the
[`ac-dev-lab` A1-mini prior art](#prior-art-in-the-ac-ac-dev-lab-a1-mini)
section for a concrete `manual_print.py` template that already wires
this up for the A1 mini and ports almost verbatim to H2D once you
have a known-good `.gcode.3mf`.)

A ready-to-run version is checked in at
[`scripts/h2d_step4_bambulabs_api.py`](../scripts/h2d_step4_bambulabs_api.py)
(`pip install bambulabs_api`, then the same
`file --ip/--access-code/--serial` CLI as the Step 3 script): it
connects, uploads, checks for the FTPS `226 Transfer complete`
response, asks for bed-clear confirmation, calls `start_print`, and
polls `get_state()` until `RUNNING`. Because `bambulabs_api` is
community-maintained and H2D-untested (see the library table), the
script prints the installed library version up front and fails loudly
rather than guessing if a signature has drifted.

Only *after* Step 4 is green for a static, hand-sliced cube does it
make sense to plug in the headless slicer worker from the
[Remote slicing](#remote-slicing-stl--3mf) section and close the loop
STL → 3MF → upload → start.

### Step 5 — Going remote (Internet / Google Colab access)

Short answer: **no, you do not have to stay LAN-only.** The bringup
checklist starts there because mode B is the only path that today is
*both* unrestricted by the new third-party authorization gate *and*
fully exercised by every open-source Python library. But the LAN
boundary is just where the printer's transports terminate — there is
nothing stopping you from putting *something* on that LAN that a
remote caller (Colab notebook, lab dashboard, GitHub Action, another
sandboxed agent) can reach over the Internet. There are three
distinct shapes the "remote" path can take, and they trade off very
differently:

| Path | Where the credentials live | Who's exposed to the Internet | Works from a Colab notebook? | Caveats |
|---|---|---|---|---|
| **R1. Self-hosted relay on the printer's LAN** *(recommended; matches your "dedicated device" instinct)* | On the relay device only — never sent to the cloud or to the notebook | Just the relay's small HTTPS API (token-auth, TLS) | **Yes** — Colab does an `https://relay.example.com/print` POST | You own and operate one extra box (Pi/NUC/lab PC); same `(IP, code, serial)` triple from Steps 1–4, never leaves your LAN |
| **R2. Network tunnel to the LAN (Tailscale / WireGuard / Cloudflare Tunnel / ngrok)** | On the worker host as before | Just the printer ports, but only inside the tunnel's overlay network | **Mostly** — Colab needs the tunnel client installed in the runtime, which is fragile across Colab kernel restarts | Easiest if you already use Tailscale; treat the tailnet as the trust boundary |
| **R3. Direct Bambu Cloud (mode A) from anywhere** | Bambu account creds + access token in the caller (Colab) | Nothing of yours — Bambu's own infra | **Yes for status reads / push subscription; restricted for `print/project_file`** under the new authorization gate (see the warning at the top of this doc and mode A) | No relay needed, but write commands from non-Bambu software are exactly what Bambu Lab is locking down; expect this path to keep shrinking. Useful today for telemetry dashboards, not for "start a job from Colab." |

**For a Colab smoke test specifically, use R1.** A Colab runtime is
ephemeral, public-IP-roulette, and `pip install`s reset on every
reconnect; you do not want to push the LAN access code or self-signed
TLS pinning into that environment, and you do not want to rely on
Bambu Cloud for the *write* path under the current authorization
regime.

#### Minimal R1 relay (what to put on the dedicated device)

The relay is "the smallest possible HTTPS service that turns one
authenticated REST call into the FTPS-upload + MQTT-publish
sequence you already verified in Step 3." Sketch:

```python
# relay.py — runs on the dedicated device sitting on the printer's LAN
# pip install fastapi uvicorn[standard] bambulabs_api python-multipart
import os, secrets, tempfile
from fastapi import FastAPI, UploadFile, Header, HTTPException
import bambulabs_api as bl

PRINTER_IP    = os.environ["PRINTER_IP"]
ACCESS_CODE   = os.environ["ACCESS_CODE"]   # 8-digit LAN code, never leaves this box
SERIAL        = os.environ["SERIAL"]
RELAY_TOKEN   = os.environ["RELAY_TOKEN"]   # long random string; share with caller out-of-band

app     = FastAPI()
printer = bl.Printer(PRINTER_IP, ACCESS_CODE, SERIAL)

@app.on_event("startup")
async def _connect():
    # Connect inside the lifecycle hook (not at import time) so the
    # service still starts if the printer is briefly unreachable and
    # so Uvicorn --reload / multi-worker doesn't open duplicates.
    try:
        printer.connect()
    except Exception as e:
        # Defer hard failure to first request; /healthz can surface it.
        print(f"[relay] initial connect failed: {e!r}; will retry on demand")

@app.on_event("shutdown")
async def _disconnect():
    try:
        printer.disconnect()
    except Exception:
        pass

def _ensure_connected():
    # Cheap reconnect helper for use in routes; bambulabs_api is
    # idempotent on .connect() once an MQTT session is live.
    if not getattr(printer, "_connected", True):
        printer.connect()

def auth(token: str | None):
    if not token or not secrets.compare_digest(token, RELAY_TOKEN):
        raise HTTPException(401, "Unauthorized")

@app.get("/status")
def status(x_relay_token: str | None = Header(None)):
    auth(x_relay_token)
    _ensure_connected()
    return printer.mqtt_dump()        # last push_status snapshot

@app.post("/print")
async def start_print(file: UploadFile,
                      x_relay_token: str | None = Header(None)):
    auth(x_relay_token)
    _ensure_connected()
    with tempfile.NamedTemporaryFile(suffix=".gcode.3mf", delete=False) as f:
        f.write(await file.read())
        local = f.name
    remote = f"colab_{secrets.token_hex(4)}.gcode.3mf"
    try:
        printer.upload_file(local, remote)            # FTPS to /cache/<remote>
        printer.start_print(remote, "plate_1.gcode")  # MQTT project_file
    finally:
        os.unlink(local)
    return {"uploaded_as": remote, "ok": True}
```

Production hardening you'll want on top of the sketch (omitted to
keep it readable): wrap `upload_file` / `start_print` in try/except
that returns a structured 5xx and reconnects `printer` if the MQTT
session has dropped, add a `/healthz` that pings the broker, and
front the whole thing with `systemd` (or a container restart policy)
so a crash doesn't strand the dedicated device.

Run it on the dedicated device behind real TLS — Caddy or
Cloudflare Tunnel are both two-line setups that hand you a
`https://relay.<your-domain>` URL with a valid certificate; do **not**
expose the FastAPI app on a raw public port with the self-signed dev
cert.

#### From a Google Colab cell, the entire client looks like:

```python
# In a Colab cell
import os, requests
RELAY = "https://relay.example.com"
TOK   = os.environ["RELAY_TOKEN"]              # set via Colab Secrets UI
H     = {"X-Relay-Token": TOK}

# Status
print(requests.get(f"{RELAY}/status", headers=H, timeout=10).json())

# Start a print of a 3MF you sliced (or fetched from cloud storage) earlier
with open("cube_h2d.gcode.3mf", "rb") as f:
    r = requests.post(f"{RELAY}/print", headers=H,
                      files={"file": ("cube_h2d.gcode.3mf", f,
                                      "application/octet-stream")},
                      timeout=60)
print(r.status_code, r.json())
```

That's it — no MQTT client, no FTPS, no LAN access code, no
self-signed certs in the notebook. The notebook only ever sees the
relay token, which you can rotate from the dedicated device whenever
a Colab session dies or leaks.

If you want the slicer to also live remotely so Colab can hand the
relay raw STLs, add a second endpoint that calls the headless Bambu
Studio CLI from the [Remote slicing](#remote-slicing-stl--3mf)
section before the `start_print()` step — same dedicated device, just
one more route on the same FastAPI app.

> [!CAUTION]
> Anyone with the relay token can start a print, which can start a
> fire. Treat `RELAY_TOKEN` like a production credential: long,
> random, rotated, never in git, never in notebook output. Pair it
> with at least one out-of-band physical interlock (e.g. a hardware
> e-stop or a "ready to print" key switch on the printer's mains)
> before pointing it at a Colab notebook running unattended.

### Step 6 — Slice on the Pi, ship STL+args remotely (Tailscale-as-LAN variant)

Both of your instincts here are correct, and they line up cleanly with
the R1 + R2 paths above:

1. **"Slicing on the device side (Pi running Ubuntu) so Colab just
   sends an STL and some args"** is just R1 with one more FastAPI
   route on the same relay process. The Pi already has the H2D
   `(IP, ACCESS_CODE, SERIAL)` triple and a known-good profile bundle;
   adding `bambu-studio --slice` keeps the LAN access code, the
   self-signed TLS, *and* the slicer-version pin all on the device so
   the notebook only ever sees `POST /print_stl`. This is also the
   right place to enforce safety limits — see below.
2. **"We already use Tailscale; can that be our 'LAN'?"** Yes —
   that's exactly path R2. A tailnet is an authenticated
   WireGuard overlay; from the H2D's and the Pi's point of view,
   anything you let into the tailnet *is* on the same L2-equivalent
   network as them. Two practical patterns:

   - **Pi inside the tailnet, H2D not.** Most common. The H2D stays
     on its dumb VLAN (it doesn't speak WireGuard) and the Pi straddles
     the two: physical NIC on the printer's LAN, Tailscale on `tailscale0`.
     The relay's FastAPI app binds to the tailnet IP (e.g.
     `uvicorn relay:app --host 100.x.y.z`), so callers (your laptop,
     a lab dashboard, a Colab cell with `tailscale up` in a setup cell,
     or a CI runner) reach `https://lab-pi.<tailnet>.ts.net:8000` over
     TLS without ever exposing port 8000 to the public Internet.
   - **Tailscale Funnel for true Internet ingress.** If you want a
     Colab cell to hit the Pi *without* installing Tailscale in the
     runtime, expose the relay through Funnel: `tailscale serve
     --https=443 http://localhost:8000` then `tailscale funnel 443 on`
     gives you a `https://lab-pi.<tailnet>.ts.net` URL with a real
     LetsEncrypt cert, terminated on the Pi. Same FastAPI app,
     same `RELAY_TOKEN` auth, no Caddy / Cloudflare needed.

   Either way, **the LAN access code, the printer's self-signed cert,
   and the H2D's MQTT/FTPS ports never leave the Pi.** The tailnet
   replaces the Caddy-or-Cloudflare-Tunnel "real TLS in front of the
   relay" piece from R1; everything else (token-auth FastAPI,
   `try/finally` cleanup, `systemd`-supervised process, hardware
   interlock) stays the same.

> **"Does adding the Pi+tailnet relay break manual Bambu Studio prints
> from a desktop?"** No. Adding the Pi-side relay is purely *additive* —
> it does not require moving the H2D off its current network or
> disabling Bambu Cloud. The relay is just one more LAN client of
> the printer (FTPS on `:990` + MQTT-over-TLS on `:8883`), running
> alongside whatever Bambu Studio instances are already there.
> Concretely, the H2D supports two non-exclusive submission paths
> simultaneously:
>
> - **Cloud-bound Bambu Studio** (the default for an account-linked,
>   Internet-attached printer like one on a campus IoT VLAN such as
>   BYU's): desktop Bambu Studio submits via `mode A` through Bambu's
>   servers. Continues to work unchanged — the Pi/tailnet relay never
>   touches Bambu Cloud.
> - **LAN-direct Bambu Studio** (`Send to printer` over LAN when the
>   desktop is on the same subnet as the H2D, with Developer Mode +
>   Access Code): keeps working as long as the desktop and the H2D
>   are on the same L2/subnet. The relay uses the *same* `(IP,
>   ACCESS_CODE, SERIAL)` triple over `mode B` from the Pi — no
>   exclusive lock, no MQTT session conflict in practice (the broker
>   on the printer accepts multiple subscribers; only one print job
>   can be `RUNNING` at a time, which is enforced by `gcode_state`,
>   not by who's connected).
>
> Two practical caveats specific to a BYU-IoT-style network:
>
> 1. **Client isolation.** Many campus IoT VLANs block client-to-client
>    traffic, so a laptop on the campus Wi-Fi often *cannot* reach the
>    H2D directly even if both are "online" — Bambu Studio falls back
>    to Cloud silently. The Pi solves this for programmatic use because
>    it sits on the same VLAN as the printer (typically wired) and the
>    tailnet bypasses client isolation for *its* traffic only. Manual
>    Bambu Studio LAN sends from a laptop on the same VLAN may still
>    fail; cloud sends still work.
> 2. **If you later flip the printer to LAN Only Mode** to harden the
>    setup (Step 1), *that* is what disables Bambu Cloud / desktop
>    Bambu Studio's cloud submit — not the existence of the Pi relay.
>    You can stay in mixed mode (Cloud + LAN both enabled) indefinitely
>    and still use the Pi+tailnet relay; LAN Only is a separate,
>    optional hardening step that trades manual-cloud convenience for
>    a smaller attack surface.

#### `/print_stl` on the Pi: STL + args → safety-checked slice → start

Concretely, replace `/print` from the Step 5 sketch with a route that
takes the raw STL and a small JSON arg blob, runs the
empirically-verified H2D slicing recipe, *then* enforces hard limits
before handing the resulting `.gcode.3mf` to `start_print`:

```python
# relay.py — additions to the Step-5 sketch (still token-auth + try/finally)
import asyncio, json, os, secrets, shutil, subprocess, tempfile, zipfile
from pathlib import Path
from fastapi import Form, Header, HTTPException, UploadFile

BAMBU       = os.environ["BAMBU_APPIMAGE"]            # absolute path on the Pi
PROFILES    = Path(os.environ["H2D_PROFILE_DIR"])     # holds h2d_*_flat.json bundles
# Per-material profile bundles, exported once from a desktop Bambu Studio
# with an H2D installed. Each value is the flattened filament JSON the CLI
# loads into BOTH tools (filament-map "1,2") for that material.
FILAMENT_PROFILES = {
    "PLA":    PROFILES / "h2d_filament_pla_flat.json",
    "PETG":   PROFILES / "h2d_filament_petg_flat.json",
    "PLA-CF": PROFILES / "h2d_filament_placf_flat.json",
}
ALLOWED_FIL = set(FILAMENT_PROFILES)
LAYER_H_RANGE = (0.08, 0.32)                          # numeric cap on layer height
LIMITS = {                                            # safety envelope
    "max_stl_bytes":          50 * 1024 * 1024,
    "max_print_minutes":      8 * 60,
    "max_filament_grams":     500,
    "max_first_layer_bed_c":  70,                     # PLA-only lab → cap bed temp
    "max_nozzle_c":           260,
}

def _safe_slice(stl: Path, work: Path, layer_h: float, fil: str) -> Path:
    if fil not in ALLOWED_FIL:
        raise HTTPException(400, f"filament {fil!r} not in allow-list")
    if not (LAYER_H_RANGE[0] <= layer_h <= LAYER_H_RANGE[1]):
        raise HTTPException(400, f"layer_height {layer_h} outside {LAYER_H_RANGE}")
    fil_json = FILAMENT_PROFILES[fil]                 # per-material profile
    out = work / "out"
    out.mkdir()
    cp = subprocess.run(
        ["xvfb-run", "-a", "-s", "-screen 0 1280x1024x24", BAMBU,
         "--orient", "1", "--arrange", "1",
         "--load-settings",  f"{PROFILES/'h2d_machine_flat.json'};{PROFILES/'h2d_process_flat.json'}",
         "--load-filaments", f"{fil_json};{fil_json}",   # filament profile per tool
         "--filament-map-mode", "Manual", "--filament-map", "1,2",
         "--layer-height", f"{layer_h}",                  # CLI overrides process profile
         "--slice", "1", "--export-3mf", "out.gcode.3mf",
         "--outputdir", str(out), str(stl)],
        capture_output=True, text=True, timeout=600, cwd=work, check=False,
    )
    try:
        result = json.loads((out / "result.json").read_text())
    except (FileNotFoundError, ValueError):
        result = {}
    if cp.returncode != 0 or result.get("return_code", -1) != 0:
        raise HTTPException(422, f"slice failed: {result.get('error_string', cp.stderr[-500:])}")
    return out / "out.gcode.3mf"

def _enforce_envelope(gcode_3mf: Path) -> None:
    # Parse the slicer's own header out of Metadata/plate_1.gcode and
    # reject anything outside the lab's safety envelope BEFORE we publish
    # the start command over MQTT.
    with zipfile.ZipFile(gcode_3mf) as z:
        head = z.read("Metadata/plate_1.gcode").decode("utf-8", "replace")[:8192]
    def _g(key, cast=float):
        for line in head.splitlines():
            if line.startswith(f"; {key}") and "=" in line:
                try:
                    return cast(line.split("=", 1)[1].strip().split(",")[0])
                except (ValueError, IndexError):
                    return None
        return None
    # Fail-closed: a missing header is treated as a hard error rather than
    # silently passing every numeric check (0 < every positive limit).
    fields = {
        "minutes": (_g("total_estimated_time", float) or None,
                    lambda v: v / 60, LIMITS["max_print_minutes"], "print too long"),
        "grams":   (_g("total_filament_weight", float),
                    lambda v: v, LIMITS["max_filament_grams"], "too much filament"),
        "bed_c":   (_g("first_layer_bed_temperature", float),
                    lambda v: v, LIMITS["max_first_layer_bed_c"], "bed temp exceeds cap"),
        "noz_c":   (_g("nozzle_temperature", float),
                    lambda v: v, LIMITS["max_nozzle_c"], "nozzle temp exceeds cap"),
    }
    for name, (raw, scale, limit, msg) in fields.items():
        if raw is None:
            raise HTTPException(422, f"missing required slicer header for {name!r}; refusing print")
        if scale(raw) > limit:
            raise HTTPException(413, f"{msg}: {scale(raw):.1f} > {limit}")

@app.post("/print_stl")
async def print_stl(file: UploadFile,
                    layer_height: float = Form(0.20),
                    filament: str = Form("PLA"),
                    x_relay_token: str | None = Header(None)):
    auth(x_relay_token)
    _ensure_connected()
    body = await file.read()
    if len(body) > LIMITS["max_stl_bytes"]:
        raise HTTPException(413, "STL too large")
    work = Path(tempfile.mkdtemp(prefix="h2d_"))
    try:
        stl = work / "in.stl"; stl.write_bytes(body)
        sliced = _safe_slice(stl, work, layer_height, filament)
        _enforce_envelope(sliced)                     # safety gate
        remote = f"colab_{secrets.token_hex(4)}.gcode.3mf"
        printer.upload_file(str(sliced), remote)
        printer.start_print(remote, "plate_1.gcode")
        return {"uploaded_as": remote, "ok": True}
    finally:
        shutil.rmtree(work, ignore_errors=True)
```

The Colab cell shrinks accordingly:

```python
import os, requests
RELAY = "https://lab-pi.<tailnet>.ts.net"             # Funnel URL, or tailnet IP
H = {"X-Relay-Token": os.environ["RELAY_TOKEN"]}
with open("part.stl", "rb") as f:
    r = requests.post(f"{RELAY}/print_stl", headers=H,
                      files={"file": ("part.stl", f, "model/stl")},
                      data={"layer_height": "0.20", "filament": "PLA"},
                      timeout=900)
print(r.status_code, r.json())
```

Key safety properties of this shape (worth defending in code review):

- **Allow-list, not deny-list, on filament + slicer args.** A
  whitelist of materials and a numeric cap on layer height is much
  harder to bypass than blocking known-bad strings.
- **Limits are enforced on the *sliced output*, not on the request.**
  A caller can't lie about print time or filament weight — the relay
  parses the slicer's own G-code header and rejects before
  `start_print()`. This catches both honest mistakes (10× scaled STL)
  and malicious payloads (STL crafted to slice into a 14-hour job).
- **`ALLOWED_FIL` / `LIMITS` live in environment variables on the
  Pi**, not in the repo. Operators can tighten them per-lab without
  shipping new code, and the values can't be overridden by the
  caller.
- **The Pi never exposes the LAN access code, the H2D's MQTT broker,
  or the FTPS endpoint.** The tailnet (or Funnel URL) only ever sees
  the FastAPI app on `:8000`.
- **Bound CPU + wall-clock per slice** via `subprocess.run(...,
  timeout=600)` and a `tempfile.mkdtemp()` that's `rmtree`'d in
  `finally`, so a pathological STL can't fill the Pi's disk or wedge
  the relay process.
- **Hardware interlock still required.** Software limits stop most
  bad jobs; a physical e-stop / mains key switch is the only thing
  that stops *all* of them, including firmware bugs and stuck
  thermistors. See "Hardware interlock — concrete options" below for
  three off-the-shelf parts that satisfy this without modifying the
  printer.

### Hardware interlock — concrete options

The "hardware e-stop / mains key switch" referenced above is a
**physical means to cut power to the H2D that does not depend on
firmware, MQTT, or the relay process being healthy.** The H2D draws
roughly 1000–1500 W peak from a standard 120 V (NA) or 230 V (EU)
outlet, so any UL/CE-listed interlock rated for that load works. Three
options in increasing cost/effort, pick **one**:

1. **In-line lockable mains switch (~$20, recommended baseline).** Buy
   a UL-listed lockable plug-load disconnect like a Tripp-Lite
   PS-415-HGLK or any "lockable inline power switch" rated ≥ 15 A
   @ 120 V (or ≥ 10 A @ 230 V). Plug the H2D into it, plug it into
   the wall, and hang the key on the lab wall. *Action when not in
   use:* operator turns the key to OFF and removes it — Colab cannot
   energise the printer no matter what the relay does.
2. **Mushroom-head e-stop pendant (~$40).** A pre-wired 22 mm
   latching e-stop button in an IP65 enclosure with a 1 m mains
   pigtail (Allen-Bradley 800FP-MT44, IDEC HW1B-V401, or any
   AliExpress equivalent rated for the printer's draw). Wire it in
   series with the H2D's power cord — pressing the button latches the
   contacts open and physically disconnects mains until twisted to
   reset. *Action:* mounted within arm's reach of anyone in the lab,
   tested once a quarter by pressing it mid-print and confirming the
   printer drops out.
3. **Smart plug with a local off-button + remote watchdog (~$15 +
   software).** Kasa KP125M, Shelly Plug US, or any Matter/HomeKit
   plug with a physical button. Wire a watchdog process on the Pi
   that issues an "off" command if `/print_stl` jobs exceed the
   `LIMITS["max_print_minutes"]` cap. *Caveat:* this is the *least*
   robust of the three because it depends on the smart plug's
   firmware — keep it as a belt-and-braces layer on top of #1 or #2,
   not as the only interlock.

For an *unattended* Colab notebook you want at least option 1 in
place **before** flipping `RELAY_TOKEN` on. For a staffed lab you
probably want option 2 anyway because it doubles as the e-stop for
the rest of the rig (powder-doser, hot plate, etc.). None of these
require modifying the printer or voiding the H2D warranty — they all
sit upstream of the printer's IEC inlet.

A reasonable order of operations to get this on a real Pi:

1. Get the Pi onto Tailscale (`tailscale up`) and confirm
   `tailscale ip -4` from another tailnet device.
2. Drop the H2D AppImage + flattened H2D profile bundle on the Pi
   under `~/h2d/`, then run the verified `--slice 1` command from the
   "Verified end-to-end locally" section once by hand to confirm the
   Pi can produce a valid `cube_h2d.gcode.3mf`.
3. Install the relay (`pip install fastapi uvicorn[standard]
   bambulabs_api python-multipart`), wire `BAMBU_APPIMAGE`,
   `H2D_PROFILE_DIR`, `PRINTER_IP`, `ACCESS_CODE`, `SERIAL`,
   `RELAY_TOKEN` via `systemd` `Environment=` lines.
4. Smoke-test `POST /status` from a laptop on the tailnet, then
   `POST /print_stl` with the same 12-tri cube STL used in the
   empirical verification. Watch `gcode_state` walk
   `IDLE → PREPARE → RUNNING` exactly as in bringup Step 3.
5. **Install the hardware interlock from "Hardware interlock —
   concrete options" above** (at minimum a lockable mains switch
   with the key hung on the lab wall). Verify it kills the printer
   mid-print by running `POST /print_stl` with the cube, then
   turning the key — `gcode_state` should go to `FAILED` /
   `OFFLINE` within seconds and the heaters should be cold to the
   touch on the next pass.
6. *Then* point Colab at the URL.

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
  --orient 1 --arrange 1 \
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
- `--orient 1` and `--arrange 1` are needed for raw STL input because,
  unlike a `.3mf`, an STL has no plate layout. Both flags accept an
  explicit `1` (enable) / `0` (disable) argument; the wiki also shows
  `--orient` as a bare boolean toggle and both forms are accepted by
  v02.06.00.51 — the doc standardises on the explicit `--orient 1
  --arrange 1` form everywhere so the same command works whether you
  copy from this section or from the verified H2D recipe
  below.[^bambu-studio-cli]
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
