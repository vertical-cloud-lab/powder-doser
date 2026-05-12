# Meta-CAD tools evaluation — what survives a fresh CI runner?

Closes #6.

## Why this exists

In [PR #2 comment 4309337047][c1] I dismissed Rhino/Grasshopper, Fusion 360
Generative Design, nTop, and Onshape FeatureScript with one line:

> chosen over Rhino/Grasshopper, Fusion Generative Design, nTop, Onshape
> FeatureScript because it's pure-Python and pip-installable — none of the
> others survive the "freshly-cloned repo on a CI runner" test

That was lazy. This directory is the receipt: I actually attempted each tool
inside the agent sandbox (Ubuntu 24.04, dotnet 8/9/10 SDKs, sudo+apt, curl,
no GUI, no vendor credentials) and recorded what happened. The verdicts below
are now backed by the install/build/runtime logs in [`logs/`](logs/) and the
small working examples checked in beside this file.

[c1]: https://github.com/vertical-cloud-lab/powder-excavator/pull/2#issuecomment-4309337047

## Scoreboard

| Tool | Authoring on Linux runner | Headless evaluation on Linux runner | What it would take to use in CI |
|------|---------------------------|-------------------------------------|---------------------------------|
| **CadQuery** (current pick) | ✅ `pip install cadquery` | ✅ pure-Python kernel | Nothing — already works |
| **OpenSCAD** | ✅ `apt install openscad` | ✅ `openscad -o out.stl in.scad` | Nothing — already works |
| **rhino3dm** (NURBS lib only) | ✅ `pip install rhino3dm` (8.17.0) | ✅ pure-Python NURBS IO | Nothing — already works |
| **Rhino Compute** front-end (`rhino.compute`) | ✅ `dotnet build` succeeds | ✅ proxy *runs* on Linux | Pair with a worker (next row) |
| **Rhino Compute** worker (`compute.geometry`) | ✅ `dotnet build` succeeds | ❌ runtime needs `libRhinoLibrary.so` | Windows host **or** Wine + Rhino-Win + license; **or** point at a paid hosted Compute |
| **Grasshopper** (`.gh` definitions) | ⚠️ no Linux authoring tool; can be authored on Windows then evaluated via Compute | ⚠️ same as Compute worker | Same as Compute worker |
| **Onshape FeatureScript** | ✅ author `.fs` as text | ⚠️ validation/exec is server-side | `ONSHAPE_ACCESS_KEY` + `ONSHAPE_SECRET_KEY` GitHub secrets + a free Onshape account |
| **nTop Automate** (Linux headless) | ⚠️ tarball gated by login at app.ntop.com | ⚠️ ditto + paid license | Vendor-issued tarball + license file uploaded as encrypted GitHub secrets; commercial subscription |
| **Fusion 360 / Generative Design** | ❌ 1.4 GB Win-only PE32 GUI installer; no Linux build, no headless mode | ❌ Generative Design is paid cloud, no public REST | Effectively impossible to bolt onto this repo's CI |

Two of those rows — Onshape FeatureScript and nTop Automate — are clearly
**not** "doesn't survive a fresh CI runner". They survive perfectly well if the
maintainer is willing to add a vendor account and put the credentials in
`Settings → Secrets`. That's a different conversation than I had in PR #2 and
the dismissal was wrong. Details below per tool.

## Independent corroboration — Edison literature synthesis

After this evaluation was already drafted, the high-effort PaperQA3 literature
search we kicked off in PR #2 returned (Edison task
[`c0f412d3-d85d-466a-abd1-db6614a2db70`](https://platform.edisonscientific.com/tasks/c0f412d3-d85d-466a-abd1-db6614a2db70),
archived verbatim in
[`edison-c0f412d3-literature-synthesis.md`](edison-c0f412d3-literature-synthesis.md)
— ~72 KB, 60+ peer-reviewed citations, mostly 2020+).
The two answers were produced independently and they agree on the big calls,
but the literature surfaces a few concrete additions worth folding into the
recommendation:

* **Code-CAD primary pick is corroborated.** The synthesis explicitly recommends
  *"CadQuery or build123d"* as the parametric authoring layer, with OpenSCAD or
  Grasshopper as alternatives — same shape as the table above. CAD-Coder
  (Doris 2026) reports 100 % valid-syntax fine-tuned generation specifically of
  CadQuery code, which makes it a slightly better target than build123d for
  any future LLM-assisted geometry step.
* **`build123d` is missing from my scoreboard.** It deserves a row alongside
  CadQuery: same Apache-2.0 OCP/OpenCascade kernel, Python-first, ~2 yr old,
  pure-Python wheels available — i.e. exactly the same fresh-runner story as
  CadQuery. We should treat it as a sibling, not a competitor.
* **Will It Print** (Budinoff 2021, MATLAB, GitHub) is the closest thing to a
  validated open-source AM-DFM checker in the literature: five explicit
  checks (overhang/support, surface-roughness Ra, small-feature, toppling
  risk, warping). A Python port is planned. This is a more credible
  open-source DFM source to lean on than what I have in `cad/dfm.py` today and
  is worth wrapping or reimplementing for the closed-loop side of #6.
* **Closed-loop testing target — the literature canonical answer is
  Jubilee + balance + OpenCV + Ax/BoTorch**, with concrete prior art (Deneault
  2021 "AM ARES" Bayesian-opt of FDM params; Pelkie 2025 Science-Jubilee SDL
  paper). **That is *not* the rig we're actually building.** For
  powder-excavator the planned hardware is a **Genmitsu 3018-Pro V2** desktop
  GRBL CNC plus a **Prusa i3 / MK3 (or Ender)** FDM printer — both manual-load,
  no auto-sample-changer, no integrated load cell or camera. So Jubilee /
  Science-Jubilee is the wrong reference platform here, and Ax/BoTorch is
  overkill while every trial is human-evaluated. The literature pick is the
  right *aspirational* target for a future SDL build-out; the v1 stack that
  matches our actual hardware is in §6 below.
* **Generative-CAD fields beyond my scoreboard.** Topology-optimisation
  commercial tools (nTop, Altair Inspire, Ansys Discovery, Fusion GD, NX) are
  reviewed as a class: the literature finding is that they all "fall short in
  supporting AM-specific constraints" and produce density fields or Pareto
  populations that still need human filtering. That's consistent with my hard
  conclusion that Fusion GD doesn't belong in the CI loop, and softens (but
  doesn't reverse) the case for nTop — even with secrets, the output still
  needs interpretation, not just ingestion.
* **Digital-twin spectrum.** Kritzinger 2018 / Tao 2019 / Lattanzi 2021
  taxonomy (digital model → digital shadow → digital twin); useful framing if
  this work ever turns into a manuscript section.

The synthesis does **not** change the per-tool verdicts in the scoreboard
above. It does add **build123d** as a sibling pick to CadQuery, points at
**Will It Print** as a better DFM target than what I have, and names
**Jubilee + Ax/BoTorch** as the *literature-canonical* physical-feedback rig
(noting we are not actually building that rig — see §6 for the stack that
matches the Genmitsu 3018 + Prusa MK3 / Ender we plan to use). Those are the
concrete follow-ups; everything else in the synthesis is supporting evidence
rather than a course correction.

---

## 1. Rhino / Grasshopper / Rhino Compute

There are three layers and the answer is different for each.

### 1a. `rhino3dm` — the open NURBS kernel as a Python library
Pure-Python, pip-installable, BSD-licensed, no Rhino install, no license:

```
$ pip install rhino3dm   # 8.17.0
$ python rhino3dm_demo.py
Wrote /tmp/.../trough.3dm: ok=True, size=10335 bytes
Re-read ok, objects=4
  - Extrusion       bbox min=-12.0,-40.0,-12.56  max=12.56,0.0,1.18
  - Extrusion       bbox min=-10.4,-40.0,-10.88  max=10.88,0.0,1.02
  - LineCurve       bbox min=0.0,-2.0,16.0  max=0.0,42.0,16.0
  - TextDot         bbox min=0.0,20.0,-17.0  max=0.0,20.0,-17.0
```

[`rhino3dm_demo.py`](rhino3dm_demo.py) builds the trough as two extruded NURBS
half-arcs plus a pivot reference line, writes a real `.3dm` file, and
round-trips it. So **for IO and basic NURBS authoring, "no Rhino on Linux"
is no longer true** — you just don't get the parametric/Grasshopper layer
on top.

### 1b. `compute.rhino3d` (the .NET REST server) — partially Linux-native
Cloned + built both the proxy and the worker on this Ubuntu runner with stock
`dotnet 9`:

```
$ git clone --depth=1 https://github.com/mcneel/compute.rhino3d.git
$ cd compute.rhino3d/src/rhino.compute && dotnet build -c Release
  rhino.compute -> .../rhino.compute.dll
  Build succeeded.    0 Warning(s)    0 Error(s)
$ dotnet rhino.compute.dll --urls=http://127.0.0.1:8081
RC  [INF] Rhino compute started
RC  [INF] Now listening on: http://127.0.0.1:8081
RC  [INF] Application started.
```

So the front-end **builds and runs on Linux** — it's just an
ASP.NET Core reverse-proxy that load-balances geometry workers. The worker
also builds:

```
$ cd ../compute.geometry && dotnet build -c Release
  compute.geometry -> .../compute.geometry.dll
  Build succeeded.    5 Warning(s)    0 Error(s)
```

…but fails at startup because there is no Linux build of Rhino itself:

```
$ dotnet compute.geometry.dll --urls=http://127.0.0.1:8082
Unhandled exception. System.DllNotFoundException: Unable to load shared
library '/usr/lib/rhino3d/libRhinoLibrary.so' or one of its dependencies.
   at RhinoInside.Resolver.PrepareRhinoEnv()
   at compute.geometry.Program.Main(String[] args)
```

The Rhino Compute README confirms: *"Compute is built on top of Rhino 8 for
Windows and can run anywhere Rhino 8 for Windows can run."* So the realistic
deployments today are:

1. Spin up a Windows host (or Windows container/VM) for `compute.geometry`,
   keep `rhino.compute` on Linux in front of it. Doable in CI but heavy.
2. Run the worker under Wine with a Rhino-for-Windows install + license.
   Possible per community projects (`cryinkfly/Rhinoceros-3D-for-Linux`,
   `aaronsb/rhino-wine`), but not "fresh-clone on a Linux runner" simple.
3. Pay for a hosted Compute service and treat it as a remote dependency from
   this repo's CI. That's plausible — see `compute_rhino3d` below.

### 1c. `compute_rhino3d` — Python client to a Compute server
Pip-installable (0.12.2), works against any Compute server URL:

```python
import compute_rhino3d.Util as U, compute_rhino3d.Mesh as MeshM
U.url    = "https://my.compute.host/"
U.apiKey = "..."
mesh_list = MeshM.CreateFromBrep(my_brep)   # POSTs /rhino/geometry/mesh/createfrombrep-brep
```

I pointed the client at a dead URL just to verify the request path is well-formed:

```
ConnectionError: HTTPConnectionPool(host='127.0.0.1', port=65530):
  ... url: /rhino/geometry/mesh/createfrombrep-brep ...
  [Errno 111] Connection refused
```

So there is a real plug-and-play Python path **iff** somebody (us or a vendor)
runs the Windows-side worker. For our purposes that's a maintained dependency,
not something CI bootstraps from scratch.

**Net for the manuscript:** "no Rhino on Linux" was overstated. We can author
NURBS in pure Python, run the orchestrator on Linux, and call out to a hosted
worker. The thing that cleanly *doesn't* work in this CI is "headless
Grasshopper-evaluation on a Linux runner with no external services."

---

## 2. Onshape FeatureScript

I was wrongest about this one. Authoring is just text; evaluation is a REST API
call to `cad.onshape.com`. The Python client is pip-installable:

```
$ pip install onshape-client     # 1.6.3
```

Authoring works fine on the runner — see [`excavator_trough.fs`](excavator_trough.fs),
a real Custom-Feature `.fs` file that defines `troughRadius`, `troughLength`,
`wallThickness` with `LengthBoundSpec` annotations (Onshape will render them as
sliders), sketches the half-annulus profile, and extrudes it.

Anonymous REST is firewalled off, as expected:

```
$ python onshape_rest_probe.py
HTTPError 401 Unauthorized: {"message":"Unauthenticated API request","status":401}
```

…but with `ONSHAPE_ACCESS_KEY` + `ONSHAPE_SECRET_KEY` in
`Settings → Secrets and variables → Actions`, a CI job can:

1. Create a fresh Onshape document via `POST /api/v6/documents`.
2. Push the contents of `excavator_trough.fs` into a Feature Studio via
   `POST /api/v6/featurestudios/{did}/w/{wid}/e/{eid}` — this returns
   FeatureScript compile diagnostics, which is the "validation/feedback"
   half of #6.
3. Insert the custom feature into a Part Studio and call
   `POST /api/v6/partstudios/{...}/features` to actually evaluate it.
4. Pull back STEP/STL via `GET /api/v6/partstudios/{...}/stl` and run the
   same DFM checks we run on CadQuery output.

Free-tier Onshape accounts can do all of this; the only non-trivial part is
that public free documents are world-visible by design. This is a perfectly
reasonable second-source CAD pipeline to add to CI when @sgbaird wants it —
say the word and I'll wire it up.

### Authenticated REST probe (HMAC-SHA256, repo secrets present)

Once `ONSHAPE_ACCESS_KEY` + `ONSHAPE_SECRET_KEY` are set as encrypted
GitHub Actions secrets, [`onshape_rest_probe_auth.py`](onshape_rest_probe_auth.py)
performs an HMAC-signed `GET /api/v6/users/sessioninfo` and
`GET /api/v6/documents`. Latest run after @sgbaird minted a fresh
classroom-scoped API key (captured verbatim in
[`logs/onshape-auth-probe.log`](logs/onshape-auth-probe.log)):

```
== GET /api/v6/users/sessioninfo ==
HTTP 200
{"id": "<redacted>", "name": "Sterling", "role": 5, "state": 1, ...}

== GET /api/v6/documents (own, first page) ==
HTTP 200
items returned: 1
  - name='test'  owner='Vertical Cloud Lab'  modified=2026-05-12T19:02:24Z
```

Drilling one level deeper on the `test` document also returns `200`
on `GET /documents/{did}` (workspace id), `GET /documents/d/{did}/w/{wid}/elements`
(Part Studio + Assembly + BOM), and `GET /parts/d/{did}/w/{wid}/e/{eid}`
(empty, `[]` — the test Part Studio has no geometry yet). HMAC-signed
`POST /api/v6/partstudios/.../translations` with `formatName=STEP`
returns `400` for that empty studio, which is the expected response
for an empty Part Studio rather than an auth failure; once a real
geometry lives in the Part Studio the same call should return a
translation id we can poll and download.

Net: **the API key works end-to-end.** The earlier 401s were the
"requested but not yet approved" state on the Education plan; the
classroom-scoped key minted via the company-settings developer page
clears that gate.

### What we can actually *do* with it (in the context of #16)

[`onshape_upload_step_probe.py`](onshape_upload_step_probe.py) extends
the auth probe into a real round-trip relevant to the Archimedes auger
of issue #16 — proving that the same REST surface CadQuery / build123d
already export to (`*.step`) can be pushed *into* Onshape for
collaboration, downstream CAM, drawing generation, etc. without a
human ever clicking the import dialog:

1. Generate a representative auger barrel locally with CadQuery
   (20 mm OD × 100 mm tall, M3 spindle clearance hole on top, 2.5 mm
   exit hole on the bottom — the parametric envelope from #16) and
   write it to `zoo-output/auger_barrel_cadquery.step`.
2. `GET /documents` → resolve `defaultWorkspace.id` of the first
   document.
3. Upload the STEP as a Blob Element via multipart
   `POST /api/v6/blobelements/d/{did}/w/{wid}` with `translate=true`.
   Onshape returns a `translationId` immediately (HTTP 200).
4. Poll `GET /api/v6/translations/{tid}` until `requestState=DONE`.
   Re-listing elements then shows a brand-new Part Studio
   (`auger_barrel_cadquery`) sitting alongside the original blob.
5. Round-trip: `POST /api/v6/partstudios/d/{did}/w/{wid}/e/{eid}/translations`
   with `formatName=STL` against the freshly-imported Part Studio
   returns `requestState=ACTIVE` (HTTP 200) — so STEP-in / STL-out
   works against geometry we just authored.

Output of the live run is appended to
[`logs/onshape-auth-probe.log`](logs/onshape-auth-probe.log); the
`elements before upload: 3 ... elements after upload: 5` line is the
proof that two new elements (blob + Part Studio) actually persisted in
the workspace.

Concretely, the unlocked verbs are now:

| Verb | Endpoint | Use in this repo |
| --- | --- | --- |
| Author in Python, push to Onshape | `POST /blobelements/.../?translate=true` | Hand a generated STEP from CadQuery / build123d / Zoo to a human reviewer in the Onshape UI without leaving CI. |
| Read geometry back out | `POST /partstudios/.../translations` (`STEP` / `STL` / `3MF`) | CI-driven "convert any Onshape Part Studio to a slicer-ready mesh" — the alternative to having CadQuery as the sole BREP source. |
| Pull existing FeatureScript | `GET /partstudios/d/{did}/w/{wid}/e/{eid}/features` | Treat Onshape as a versioned feature store and synthesise variants from the JSON tree (the FeatureScript-as-code path from §2). |
| Diff workspaces / versions | `GET /documents/d/{did}/changes` | Detect "the auger spec changed in Onshape" and trigger the FDM/CNC pipeline automatically. |

### Zoo (zoo.dev) — KittyCAD design API + ML-ephant text-to-CAD

[`zoo_text_to_cad_probe.py`](zoo_text_to_cad_probe.py) drives the same
auger-shaped use-case through Zoo's hosted APIs (the `kittycad` Python
SDK is a thin wrapper around the same REST endpoints used here). Reads
`ZOO_API_TOKEN` from env; never echoes it.

* **KittyCAD design API** — `GET /user` returns the account profile
  (HTTP 200, identity verified). The Cloudflare edge in front of
  `api.zoo.dev` blocks the default `Python-urllib/3.x` UA with `error
  code: 1010`; the probe sets an explicit project UA on every request.
  The paid endpoint we'd extend this to is
  `POST /file/conversion/{src}/{dst}` (e.g. `step → gltf`,
  `stl → step`) — the headless format-conversion service that pairs
  cleanly with the Onshape upload path above.
* **ML-ephant text-to-CAD** — `POST /ai/text-to-cad/{output_format}`
  with a JSON body `{"prompt": "..."}` queues an async ML job
  (HTTP 201, returns a job id). Polling
  `GET /user/text-to-cad/{id}` reports `status` transitions
  `queued → in_progress → completed|failed`. Jobs typically finish in
  ~5–15 min; outputs are returned as base64-encoded files in the
  job dict and written to `zoo-output/`.

For #16 the prompt sent was the verbatim spec from the issue
("Archimedes auger / helical screw dispenser, 20 mm OD, 100 mm tall,
M3 mounting hole, 2.5 mm exit hole, ~10 mm pitch single-start helix,
~6 mm central shaft"). Run output is captured in
[`logs/zoo-text-to-cad.log`](logs/zoo-text-to-cad.log).

Practical fit for this repo:

* **ML-ephant** is the closest thing to a true *generative* CAD
  endpoint we've found that runs headless on a free-tier token — but
  it's stochastic, not parametric, so it belongs in a "concept
  exploration / first-draft geometry" lane upstream of CadQuery, not
  as a replacement for it. The right pattern is: ML-ephant produces
  a STEP candidate → CadQuery re-imports / measures it → DFM checks
  → if it survives, push back to Onshape via the upload probe above.
* **KittyCAD file conversion** is a useful fallback for the few
  format pairs CadQuery / build123d don't handle natively (e.g.
  `step → gltf` for web preview), but it's not a critical-path
  dependency.

---

## 3. Fusion 360 / Generative Design

This one really does not survive a Linux CI runner. Concrete evidence:

```
$ curl -O https://dl.appstreaming.autodesk.com/.../Fusion%20Admin%20Install.exe
  -> 1.4 GB
$ file Fusion360ClientInstaller.exe
  PE32 executable (GUI) Intel 80386, for MS Windows, 5 sections
$ wine Fusion360ClientInstaller.exe /S
  wine: failed to open L"C:\\windows\\syswow64\\rundll32.exe": c0000135
  ShellExecuteEx failed: Internal error.
```

Even past the wine multilib problem, two structural blockers remain:

* Fusion 360 is a streaming GUI client, not a headless renderer. There is no
  `fusion --batch foo.f3d` mode and no Linux build at all.
* **Generative Design** specifically is a *cloud* job inside Autodesk's
  paid subscription, billed by tokens; there is no public REST endpoint to
  submit a study from outside the GUI. Autodesk's "Design Automation for
  Inventor/Revit" APS service does not cover Fusion Generative Design.

So for the powder-excavator CI loop, Fusion Generative Design is a hard no.
The right Autodesk-adjacent option (if we ever want one) is Inventor +
APS Design Automation, which is its own evaluation.

---

## 4. nTop / nTop Automate

Also wrongly dismissed. nTop *does* publish a Linux headless build —
**nTop Automate for Linux** — distributed as a tarball you extract anywhere,
intended exactly for HPC and CI batch use. From nTop's own support article
([support.ntop.com #16750988785299](https://support.ntop.com/hc/en-us/articles/16750988785299-nTop-Automate-for-Linux-Update)):

> nTop Automate for Linux is the headless (no GUI) version intended for
> large automated/batch workflows and HPC environments… reached general
> availability and can be directly downloaded by authorized users from the
> official user dashboard at https://app.ntop.com/.

What stops it on *this* runner is that the dashboard is login-walled and
requires a paid commercial license:

```
$ curl -I https://app.ntop.com/
HTTP/2 200 — single-page React app behind login; no anonymous downloads
$ pip install ntop_api
ERROR: No matching distribution found for ntop_api
```

But "can't pip install it" ≠ "can't run it in CI". The realistic CI shape is:

1. Buy / extend the existing nTop seat with an Automate license.
2. Drop the `nTop Automate` tarball into a private GCS/S3 bucket (or
   GitHub Releases on a private repo).
3. CI: download the tarball, extract, mount the licence file from
   `secrets.NTOP_LICENSE`, run `ntopcl my_workflow.ntop --output mesh.stl`.
4. Feed the resulting lattice/TPMS geometry through the same DFM checks.

This is the same operational shape as a paid CodeQL or Coverity license in
CI, not exotic. nTop is the best-of-class generative tool in the list and
it's worth doing this if we ever push the trough geometry past what
CadQuery's BREP kernel handles cleanly (e.g. lattice infill of the arms).

---

## 5. Genuine non-Python alternative: OpenSCAD

To not just be "Python with extra steps", I also ran OpenSCAD end-to-end
on this same runner — installs from the distro repo, no Python, no license:

```
$ sudo apt install openscad      # OpenSCAD version 2021.01
$ openscad -o trough.stl excavator_trough.scad
   Halfedges: 732   Edges: 366   Halffacets: 248   Facets: 124   Volumes: 2
$ head -2 trough.stl
solid OpenSCAD_Model
  facet normal -0.760414 0 0.649439
```

[`excavator_trough.scad`](excavator_trough.scad) is a working hollowed
half-cylinder trough, 124 facets, ~80 KB STL. OpenSCAD is the cleanest
"non-Python, fully open, fully CI-compatible" option if we ever want to
replace or dual-source the CadQuery model.

---

## 6. Hardware-aware pipeline for Genmitsu 3018-Pro V2 + Prusa MK3 / Ender

The literature synthesis (§"Independent corroboration") points at **Jubilee +
balance + OpenCV + Ax/BoTorch** as the canonical SDL rig. That is the right
*aspirational* target, but it is not what we are actually building. The
planned hardware for powder-excavator is:

* **Genmitsu 3018-Pro V2** — desktop GRBL CNC, ~300×180×45 mm work envelope,
  ~10k RPM 775 spindle, ER11 collet, Woodpecker-style controller speaking
  GRBL G-code over USB. Manual workholding, no auto-tool-change, no probe by
  default.
* **Prusa i3 / MK3 (or Creality Ender-3)** — manual-load FDM printer, no
  sample changer, no instrumented bed.

Both are good-enough hobby-grade machines; neither is a Jubilee and neither
exposes a closed-loop instrumented-feedback hook out of the box. So the v1
"meta-tool" stack that actually fits this hardware is:

| Stage | Tool | Why it fits this hardware |
|-------|------|---------------------------|
| Parametric CAD | **CadQuery** (or **build123d**) | Unchanged — pip-installable, headless, real STEP/STL out, runs in CI. |
| Second-source / sanity check | **OpenSCAD** | Unchanged — `apt install openscad`, already builds an STL on the runner. |
| FDM slicing (MK3 / Ender) | **PrusaSlicer CLI** | Headless, ships profiles for both MK3S and Ender-3 in-box, exports G-code plus per-print metrics (time, filament use, support volume) that are useful as DFM signals. |
| FDM slicing (Cura / CuraEngine path) | **CuraEngine** (`CuraEngine slice -j fdmprinter.def.json -l model.3mf -o out.gcode`) — feed it **3MF**, not STEP. Cura GUI and CuraEngine CLI are mesh-only (`-l` accepts `.stl`, `.obj`, `.3mf`); STEP/IGES are not supported and unmaintained STEP-reader plugins just tessellate on import. | Headless, packaged for Linux. Use 3MF when Cura is the consumer (units baked in, per-mesh material/profile metadata, ~10× smaller than STL). |
| CNC CAM for the 3018 | **FreeCAD Path workbench** (headless via `freecadcmd`), or **Kiri:Moto** for STL-in / GRBL-out without scripting | Both emit GRBL-flavored G-code suitable for the 3018's Woodpecker controller. FreeCAD Path is the CI-friendly option; Kiri:Moto is the low-friction option. |
| G-code simulation | **Camotics** (apt) or **NC Viewer** (web) | Visualise the toolpath before crashing a 3.175 mm endmill into the bed. Camotics is fine for spot checks. |
| Sender to the 3018 | **UGS** (Universal Gcode Sender) or **bCNC** | Standard GRBL senders. Not a CI thing — listed so the meta-tool list matches reality. |
| DFM | Will-It-Print-style checks (overhang, small feature, warping, toppling, surface) for the FDM side; geometric guards (min endmill diameter, max depth-of-cut per pass, no internal sharp corners smaller than tool radius, no features taller than ~40 mm Z) for the CNC side | Keep `cad/dfm.py` — split FDM-vs-CNC. |
| Design-space exploration | **Manual parameter sweeps + a small pandas/Jupyter scorecard** by default. Optional: **Optuna** with `n_trials≈10–20` if you grow past ~5 parameters and are willing to do that many physical builds | No automated objective function exists yet — every trial requires a human to print/mill/measure. BO over <5 hand-evaluated trials isn't worth the framework overhead; a Latin-hypercube of 6–9 designs evaluated in a notebook beats Ax here. |
| Glue | Python + Jupyter | Unchanged. |

**Net stack for v1:** CadQuery (+ OpenSCAD second source) → PrusaSlicer CLI
for the MK3/Ender parts, FreeCAD Path → GRBL for the 3018 parts → Camotics
preview → manual build/measure → pandas scorecard in Jupyter. Optuna only if
the parameter count justifies it; Ax/BoTorch and Science-Jubilee stay on the
"future SDL" wishlist for if/when a load cell, scale, or webcam ever gets
bolted onto the bench.

### Export-format targets from the CadQuery build

Per the STL-vs-STEP discussion on this PR, the CadQuery build should emit
**three** sibling artefacts per part rather than STL only, and let the
downstream consumer pick:

| Target | Format | Consumer |
|--------|--------|----------|
| `*.stl` | Mesh, ASCII or binary | Lowest-common-denominator slicer input; OpenSCAD diff/sanity check; legacy CAM. |
| `*.3mf` | Mesh + units + per-mesh metadata (zip) | **Preferred slicer input** for Cura / CuraEngine, PrusaSlicer, Bambu Studio / OrcaSlicer. Units baked in, ~10× smaller than STL, no scale-mismatch foot-guns. |
| `*.step` | BREP (OpenCascade) | Archival, FreeCAD Path / Fusion CAM (Genmitsu CNC side), reuse in any other BREP kernel. Note: Cura / CuraEngine do **not** read STEP. |

In CadQuery this is three one-liners against the same `result` object:

```python
import cadquery as cq
cq.exporters.export(result, "trough.stl")
cq.exporters.export(result, "trough.3mf")
cq.exporters.export(result, "trough.step")
```

build123d has the same shape (`export_stl`, `export_3mf`, `export_step`).
OpenSCAD and `rhino3dm` cannot emit STEP — that's CadQuery / build123d /
Onshape (REST `translations` endpoint, `formatName: "STEP"`) only.

### Sending a sliced job to a Bambu printer programmatically

If/when a Bambu printer (X1/X1C, P1/P1S, A1/A1 mini) joins the hardware list,
there is **no official public REST API**, but three working programmatic
paths exist. Pick by whether the printer has **LAN-only mode** enabled and
whether you want to go through Bambu Cloud or stay on the LAN.

| Option | Transport | When to use | Auth |
|--------|-----------|-------------|------|
| **1. Bambu Studio / OrcaSlicer CLI → MQTT push (LAN)** | FTPS upload to `/cache/` (port 990, anonymous + access code) **+** MQTT command on port 8883 to `device/<serial>/request`; subscribe to `device/<serial>/report` for telemetry | Default. CI runner is on the same LAN as the printer; "LAN-only mode" enabled on the printer's touchscreen. | Printer **IP** + **device serial** + 8-digit **LAN access code** (all from the printer's "Network" screen). |
| **2. Bambu Cloud MQTT** | Same protocol, broker `us.mqtt.bambulab.com:8883` (or `cn.…`) | CI runner cannot reach the printer's LAN. | Bambu Cloud account token. Subject to ToS and account quotas. |
| **3. OctoEverywhere / community bridge** | Translates OctoPrint-style HTTP → Bambu MQTT under the hood | Only if you already have an OctoPrint farm. No real advantage over Option 1 otherwise. | Bridge-specific. |

Note: Bambu printers are **not** classic Marlin/Klipper devices and do **not**
expose a `/dev/ttyUSB0` G-code stream. Generic OctoPrint / Moonraker
integrations don't apply directly.

The community Python lib **[`bambulabs-api`](https://pypi.org/project/bambulabs-api/)**
(MIT-licensed) wraps Options 1 and 2. Sketch of the LAN-only flow:

```bash
# 1) slice 3MF -> Bambu .gcode.3mf (a 3MF flavour with embedded G-code,
#    plate thumbnail, and print metadata)
bambu-studio --slice 1 \
  --load-settings "machine.json;process.json;filament.json" \
  --export-3mf out.gcode.3mf \
  trough.3mf

# 2) FTPS-upload + MQTT "project_file" command on the LAN
python -m bambulabs_api send \
  --ip 192.168.1.42 \
  --serial 0123456789ABCDEF \
  --access-code 12345678 \
  --file out.gcode.3mf
```

What this slots into the v1 stack as:

```
CadQuery part ──► trough.3mf  (cq.exporters.export)
                     │
                     ▼
           bambu-studio --slice  (or orca-slicer --slice)
                     │
                     ▼
               out.gcode.3mf
                     │
                     ▼ (FTPS upload + MQTT command, bambulabs-api)
                Bambu printer
                     │
                     ▼ (MQTT report topic)
             live telemetry → pandas scorecard
```

Two practical caveats worth front-loading:

* **Firmware lockdown.** Mid-2024 Bambu rolled out "Authorization Control"
  (the controversy that kicked off the Orca / Bambu split). On the latest
  X1/P1/A1 firmware, third-party MQTT clients still work but require
  **"Developer Mode"** (X1) or **"LAN-only mode"** (P1/A1) to be enabled on
  the printer's touchscreen. Without it, only Bambu Studio / Bambu Handy can
  connect. Confirm firmware version *before* committing this path to CI.
* **CLI profile-baking.** Bambu Studio's CLI flag surface is thinner than
  PrusaSlicer's; profile JSON has to be pre-baked and committed to the repo
  alongside the part source. **OrcaSlicer** is closer to PrusaSlicer-style
  ergonomics here and is the slicer I'd reach for first.

### Cost / Linux-headless reality check for the paid-tool rows

The scoreboard above lists three paid tools as "would survive CI if you pay
the vendor": Rhino+Compute, Onshape FeatureScript, and nTop Automate. Concrete
2026 numbers, so this is not re-litigated next time:

| Tool | List price (USD) | Academic / education option | Linux-headless reality |
|------|------------------|------------------------------|-------------------------|
| **Rhino 8** (single-user, perpetual) | ~$995 commercial | **~$195** academic single-user, perpetual, full-featured (proof of student/educator status required); some authorised resellers occasionally as low as ~$140–$180 | **No native Linux build, no supported headless mode.** Rhino 8 is Windows + macOS only. The pure-Python `rhino3dm` library and the `rhino.compute` proxy run on Linux, but the actual geometry kernel (`compute.geometry`) needs Rhino-for-Windows behind it (Windows host, Wine + license, or a paid hosted Compute). The academic licence does not change that. |
| **Onshape** | Free **Public** plan ($0, all docs world-visible, non-commercial); **Standard** ~$1,500/user/yr (private docs, commercial use); **Professional** ~$2,500/user/yr (PDM, workflows, simulation); **Enterprise** quote-only | **Education plan is free** for verified individual students and educators (full features, non-commercial). Education *Enterprise* (institution-managed) is paid. | Browser + cloud REST API — Linux-native by construction. The runner just `pip install onshape-client` and posts to `cad.onshape.com`. Works in CI today with `ONSHAPE_ACCESS_KEY` / `ONSHAPE_SECRET_KEY` secrets. For an academic project the free Education plan is the obvious entry point, though for an open repo the Public free tier (everything world-visible) is the simplest match. |
| **nTop / nTop Automate** | **Quote-only — no public list price.** Comparable enterprise CAD tools sit in the $2.4k–$8k/user/yr range, and nTop is generally reported at or above that band. Automate is a licensable add-on, also quote-only. | nTop offers academic pricing but **does not publish rates** — institution, seat count, and teaching-vs-research use all factor in. Contact academic@ntop.com. | **nTop Automate for Linux** is a real headless tarball intended for HPC/CI batch use, but the download dashboard (`app.ntop.com`) is login-walled and the runtime requires a paid licence file. So "Linux-headless" is technically yes, "fresh-clone CI without secrets" is no. |

Practical read for this project: **Onshape (free Education plan)** is the only
one of the three that's actually free, Linux-native, and ready to wire into
CI. **Rhino academic** is cheap-ish ($195) but fundamentally Windows/Mac and
doesn't unlock a Linux CI path on its own. **nTop** is the most powerful for
generative/lattice work but the price is opaque and almost certainly not
justified at the v1 trough-design scale; revisit only if/when geometry pushes
past CadQuery's BREP kernel.

---

## Revised recommendation

Drop the original blanket dismissal and replace it with:

* **Primary CAD authoring + CI DFM**: keep CadQuery (best fresh-runner story,
  unifies authoring + DFM + tests in one Python codebase). Treat **build123d**
  as a sibling pick on the same kernel.
* **Non-Python second source**: OpenSCAD is a one-liner to add and gives
  us a sanity check that geometry behaves the same in two kernels.
* **FDM toolchain (MK3 / Ender)**: PrusaSlicer CLI, headless, in CI.
* **CNC toolchain (Genmitsu 3018-Pro V2)**: FreeCAD Path → GRBL G-code (or
  Kiri:Moto for STL-in / GRBL-out without scripting); Camotics for toolpath
  preview; UGS / bCNC as the sender (operator side, not CI).
* **DFM**: split `cad/dfm.py` into FDM checks (Will-It-Print-style) and CNC
  checks (geometric guards against tool radius and Z reach).
* **Design-space exploration**: manual sweeps + a pandas/Jupyter scorecard
  by default; reach for **Optuna** only past ~5 parameters and 15+ physical
  builds. Hold **Ax/BoTorch** and **Science-Jubilee**-style closed-loop SDL
  on the wishlist for if/when the bench gets instrumented.
* **Generative / NURBS path** (if we ever need it):
  * **Onshape FeatureScript** via `onshape-client` + repo secrets — easiest
    to stand up; **free Education plan** covers individual academic use, so
    cost is not a blocker. Linux-native via REST.
  * **nTop Automate** for actual generative / lattice work — genuinely
    Linux-headless-ready, but quote-only commercial pricing (no public
    list), so only worth it if the bimodal compliant-mechanism scoop (#4)
    grows past CadQuery's BREP kernel.
  * **Rhino + Grasshopper via Rhino Compute** — academic Rhino is cheap
    (~$195 perpetual, single-user) but Rhino itself is **Windows / macOS
    only**, so this is viable as a hosted service or a Windows-side worker,
    not as something a Linux CI runner builds from scratch.
* **Fusion 360 Generative Design**: don't pursue. Cloud-token-billed,
  GUI-only authoring, no headless API, no Linux. Inventor + APS Design
  Automation would be the Autodesk-side option to revisit, separately.

If/when @sgbaird wants any of the cloud paths actually wired into this repo,
say which one(s) and I'll do the secrets wiring + workflow in a follow-up PR.

## Files

| File | What it is |
|------|------------|
| [`rhino3dm_demo.py`](rhino3dm_demo.py) | Pure-Python NURBS authoring → real `.3dm` file |
| [`excavator_trough.fs`](excavator_trough.fs) | Real Onshape FeatureScript Custom Feature for the trough |
| [`onshape_rest_probe.py`](onshape_rest_probe.py) | Probe of the Onshape REST API showing 401 anonymous response |
| [`onshape_rest_probe_auth.py`](onshape_rest_probe_auth.py) | HMAC-signed Onshape probe driven by `ONSHAPE_ACCESS_KEY` / `ONSHAPE_SECRET_KEY` env / repo secrets |
| [`excavator_trough.scad`](excavator_trough.scad) | OpenSCAD model that builds an STL on this runner |
| [`edison-c0f412d3-literature-synthesis.md`](edison-c0f412d3-literature-synthesis.md) | Verbatim Edison/PaperQA3 high-effort lit synthesis used in §"Independent corroboration" |
| [`logs/`](logs/) | Captured install / build / runtime output for every claim above |
