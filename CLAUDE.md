## Edison Scientific

When waiting on an Edison task in GitHub Actions, NEVER run the polling script in the background (run_in_background, nohup, &, or the Monitor tool) — the runner is destroyed the moment you post your final comment, killing background processes; Monitor counts as background and dies the same way. Also be aware that the agent harness BLOCKS the shell `sleep` builtin in foreground Bash calls (the error message suggests Monitor — do NOT follow that suggestion, it recreates the background-death failure; this killed several past sessions). The pattern that works: put the wait INSIDE a single blocking Python call — Python-side `time.sleep` is not blocked — and run it as ONE foreground Bash call with an explicit long timeout (max 3600000 ms). Run exactly this (adjust only the task-id path):

```bash
# ONE foreground Bash tool call with timeout: 3600000
python - <<'EOF'
import json, os, time
from edison_client import EdisonClient

client = EdisonClient(api_key=os.environ["EDISON_PLATFORM_API_KEY"])
task_id = json.load(open("outputs/<...>/_task_id.json"))["task_id"]
while True:
    task = client.get_task(task_id=task_id, verbose=True)
    status = str(task.status)
    print("status:", status, flush=True)
    if status in {"success", "fail", "failed", "cancelled", "error"}:
        break
    time.sleep(240)
EOF
```

Equivalently, run a repo script whose own `while ... time.sleep(...)` loop does the waiting (e.g. `python scripts/explore_case_studies.py stage8-wait`) as a single long-timeout Bash call. Do not post your final comment until results are fetched and committed, or ~45 minutes of wall-clock have elapsed — in which case commit the task-id file and state that a follow-up @claude comment is needed to fetch. If you need to upload files, use analysis query type. See the docs: https://edisonscientific.gitbook.io/edison-cookbook/edison-client. Here is the endpoint you should use: https://api.platform.edisonscientific.com. The API key is `EDISON_PLATFORM_API_KEY`. Don't expose this secret, e.g., by echoing or grepping it. Pass the API key in explicitly:

```
from edison_client import EdisonClient, JobNames
client = EdisonClient(api_key=EDISON_PLATFORM_API_KEY)
```

Whenever you retrieve results (either during the current agent session or during the next session), make sure to fetch and commit all artifacts associated with a trajectory.

If using Edison Analysis, refer to https://docs.edisonscientific.com/edison-client/file-management#upload for instructions on how to upload files. If able to use Context7, to better inform use of EdisonClient, see https://context7.com/future-house/edison-client-docs/llms.txt?tokens=10000

## CAD

If you make changes to CAD drawings, recompile/render them (images, GIFs, STLs, etc.).

## Onshape

Onshape is the team's GUI/cloud CAD — browser + REST API, so it is Linux/CI-friendly by
construction (API docs: https://onshape-public.github.io/docs/, interactive explorer:
https://cad.onshape.com/glassworks/explorer/). Auth is an HMAC-signed key pair in
`ONSHAPE_ACCESS_KEY` / `ONSHAPE_SECRET_KEY`; no OAuth app is needed for
read/translate/FeatureScript work, and never echo or commit the keys. Probe auth with
`GET /api/v6/users/sessioninfo` *and* a documents list — an unapproved personal
Education-plan key can 204 on sessioninfo yet 401 ("Unauthenticated API request") on
everything else; company/classroom-scoped keys (Company settings → Developer → API keys)
are what works. For enterprise-domain documents (e.g. `byudesign.onshape.com`), call that
domain, not `cad.onshape.com`. Always post clickable document/tab links in issues/PRs.

- **Import/export.** Push geometry via multipart
  `POST /api/v6/blobelements/d/{did}/w/{wid}?translate=true`, then poll
  `GET /api/v6/translations/{id}` to `DONE`. Upload **STEP, not STL** — STEP imports as an
  editable Part Studio solid, STL as a dumb mesh. Export with
  `POST .../partstudios/d/{did}/w/{wid}/e/{eid}/translations` (`formatName=STEP`/`STL`),
  poll, download. STEP carries geometry and part names only — plate layout, extruder
  routing, and filament profiles live exclusively in the `.3mf`.
- **Share links ≠ export.** An anonymous-read share serves `features`, `elements`,
  `shadedviews`, `thumbnails` (200) but 401/403s every geometry/export endpoint unless
  export was enabled on the share; there is no cookie workaround — ask the owner or use
  API keys with real access. The feature-tree JSON is still the full parametric source, so
  mirroring it + renders into git beats committing nothing (byu-vcl#169).
- **Verify, don't assert.** Render the live workspace via the `shadedviews` endpoint and
  read back bounding boxes / `featureStatus` after driving parameters through the API.
- **Commit the ids.** Any document a script or teammate creates should get its URL +
  did/wid/eids committed (e.g. an `ONSHAPE-DOCUMENT.md`) — stdout-only ids become a
  scavenger hunt. Make driver scripts idempotent: find the document and studios by name
  and replace only the stale feature, so element ids (and bookmarks) survive re-runs.
- **One source of truth.** If a git-tracked file (`.fs`/`.scad`/`.py`) regenerates the
  document, hand-edits in Onshape get silently overwritten — agree on the direction up
  front. Prefer one document containing all Part Studios + the assembly over one document
  per part (powder-doser#128).
- **FeatureScript.** Custom features can only be referenced from a **version**, never a
  workspace: push Feature Studio → compile server-side → cut a version → insert into a
  Part Studio. Traps that each cost real time (worked example + details:
  tensegrity-optimization#95): colliding with an `onshape/std` name (e.g. `BLEND_BOUNDS`)
  kills the compile *silently* — `featureSpecs: []`, no error, so prefix your constants;
  `fSphere` takes a `Query` centre, use `opSphere` for generated geometry; operation ids
  must be contiguous per parent; `POST .../features` needs the flattened `btType`
  serialization (`"BTMFeature-134"`); enum parameters need the feature's full
  `d::v::e::m` namespace (empty is accepted with 200, then regen `ERROR`); the REST layer
  returns `featureStatus` only, never regen message text. Lint/debug through
  `POST .../partstudios/.../featurescript` — it gives real line-numbered errors but only
  accepts a single anonymous function (no `FeatureScript NNNN;` header, no imports).
  Add `regenError` guards + sane bounds so bad dialog values error instead of building
  junk geometry.

## LaTeX

Install MiKTeX instead of TeXLive to reduce download size and time. In the first installation of MiKTeX, download known required packages based on the LaTeX file itself, and install anything else ad-hoc as needed.

## Coding Agent

- Include plots directly in your comment reply via `![image name](https://github.com/<user/org>/<repo>/blob/<shortened-commit-hash>/<filename>?raw=true)`. Truncate the commit hash to the first 7 characters only. For example, `https://github.com/AccelerationConsortium/evaluation-metrics/blob/52754e7/scripts/bo_benchmarks/demonstrations/branin_campaign_demonstration_results.png?raw=true`. For provenance, ensure you use the shortened (7-character) commit hash, not the branch name
- If you mention files in your comment reply, add direct hyperlinks based on the shortened (7-character) commit hash
- IMPORTANT: Never echo/grep/print environment secrets. These should never be exposed in your terminal history or other outputs

## Tailscale → Raspberry Pi connection

If you are doing remote work with the physical Pi device (be very careful!), this section is applicable. Regardless, **you are already on the tailnet for the powder doser test device.** As this can be connected to physical hardware, this is a high-risk activity. The workflow joins the runner via the official
[Tailscale GitHub Action](https://tailscale.com/kb/1276/tailscale-github-action) (OAuth
client + device tag) before you start. Run `tailscale status` to confirm — do **not**
install Tailscale, mint auth keys via the API, or run `tailscale up` unless status
genuinely shows you disconnected. Access to the Pi is
[Tailscale SSH](https://tailscale.com/kb/1193/tailscale-ssh), authorized by
[tailnet ACLs](https://tailscale.com/kb/1018/acls) rather than SSH keys — there is no key
to find or generate. The Pi's login username, hostname, and sudo password are injected as
environment variables (check `env` for the `RPI_*`-style names rather than assuming them);
always reference them as `"$VAR"` and never print the hostname or any credential in
comments, commits, or logs. If SSH is refused (`tailnet policy does not permit you to SSH
to this node`), the fix is an ACL/tag change only the tailnet admin can make — report it
and stop rather than working around it.

**sudo on the Pi is password-gated** — no passwordless sudo, and polkit rejects
non-interactive `systemctl`. Feed the password over stdin so it never appears in a process
list or shell history: `ssh … "sudo -S -p '' <cmd>" <<< "$RPI_PASSWORD_VAR"`.

**You have two machines — use the right one.** Your runner terminal and the Pi are
separate environments: cloud/API credentials (AWS, etc.) live on the **runner**, so run
that tooling there rather than routing it through the Pi. Use the Pi only for what
genuinely requires it — its attached hardware, or its residential IP (some services block
datacenter IPs). The Pi is typically on constrained residential Wi‑Fi and may be carrying
live workloads, so rate-cap any large transfer (`--limit-rate` or equivalent) and never
run full-bandwidth speed tests on it.

**Treat the Pi as a live production device.** Inspect read-only first (`systemctl status`,
`journalctl`, `crontab -l` as root) before changing state: scheduled reboots, watchdog
timers, and `Restart=` policies may already exist, so an unreachable or restarting device
may be behaving as designed — check the clock and the existing automation before declaring
an outage or adding new monitoring. Restart services only when necessary and verify the
device's workload is healthy end-to-end afterwards, reporting failures as failures.
Changes made on the Pi (systemd units, cron, scripts, config) do not live in this repo —
record them in the repo's docs so they can be reproduced or upstreamed.
