# text-to-cad and Onshape

How the [text-to-cad](https://github.com/earthtojake/text-to-cad) workflow (cadgen/build123d models → STEP plus kinematics sidecars, with checks, URDF/SDF and slicing) could work with Onshape's REST API. It builds on the lab's earlier API work: [PR #170](https://github.com/vertical-cloud-lab/powder-doser/pull/170) (`onshape_build.py`: a Part Studio per STEP, 72 placed instances, in-place re-import, shaded views), byu-vcl [#234](https://github.com/vertical-cloud-lab/byu-vcl/pull/234) (native sketch/extrude features plus STEP import) and [#245](https://github.com/vertical-cloud-lab/byu-vcl/pull/245) (import, then `copyWorkspace` into vcl-shared).

Written for issue #172 on 2026-10-03. Endpoint names are `operationId`s from Onshape's [OpenAPI spec](https://cad.onshape.com/api/openapi) (v1.221), browsable in [Glassworks](https://cad.onshape.com/glassworks/explorer).

**Update (2026-10-05):** the servos-above lowering was made in Onshape through the API, in one document with a branch per variant. The text-to-cad design was rebuilt as a FeatureScript feature, and its baseplate matches the build123d one at IoU 1.0000. The thinner-table variant uses three standard features driven by one variable. Together they took 54 calls; see [`../onshape/README.md`](../onshape/README.md). Option C below turned out cheaper than estimated: FeatureScript that mirrors the build123d code compiled and regenerated on its first upload.

## Short answer

Yes, and neither replaces the other:

- **Git and cadgen stay the source of truth** for generated geometry, kinematics and checks, which run locally and in CI at no cost. **Onshape is the shared view people can edit**, and the API connects the two in both directions.
- **Most valuable new step:** push the cadgen kinematics sidecar into the existing Onshape assembly as real mates and gear relations. The live document has none (probe below), and the API can create every one the doser needs.
- **Second:** the return path. Export an Onshape *version* to STEP and run the same cadgen checks on it in GitHub Actions.
- **The limit is the annual API-call quota, not capability.** The current sync spends 77 calls per run even when nothing changed; batching cuts that to 1–6.

## Options at a glance

| # | Option | How (endpoints) | Effort | Value | API calls |
|---|---|---|---|---|---|
| A1 | PR #170's geometry push, batched | as now (`createTranslation`, `uploadFileUpdateElement`), but one `modify` call carrying every `transformDefinitions` entry instead of 72 `transformOccurrences` calls | 1 h | High (quota) | 77 → 1–6 per run |
| A2 | Sidecar kinematics → real mates | assembly `addFeature`: `mateConnector`, `mate` (REVOLUTE/SLIDER + limits), `mateRelation` GEAR, `mateGroup` | 1–2 days | High | about 40, once |
| A3 | Poses and renders in Onshape | `updateMateValues` + `getAssemblyShadedViews` | 2 h | Low (cadgen snapshots do it free) | 2 per frame |
| B1 | Onshape version → STEP → cadgen checks in CI | `createAssemblyExportStep` → `getTranslation` → `GET /documents/d/{did}/externaldata/{fid}` → `read_scene` | 0.5–1 day | High once people edit in Onshape | 4–6 per check |
| B2 | Trigger B1 automatically | `createWebhook` (`onshape.model.lifecycle.createversion`) → relay → GitHub `repository_dispatch` | 1 day + a relay | Medium | 1 to register; notifications free |
| B3 | Write results back | `createComment`, `createVersion`, `updateWVEPMetadata` (one part per call) | 2 h | Medium | 1–3 per check |
| C1 | Native, editable parts from code | `addPartStudioFeature` (feature JSON, proven in byu-vcl #234), Feature Studio, Variable Studio, configurations | days per part | Low–medium | 2+ per feature |
| D1 | Checks inside Onshape | `getAssemblyMassProperties` (needs materials); `evalFeatureScript` + `evCollision` (Part Studio only) | 0.5 day | Medium | 1 per query |
| E1 | URDF/SDF/MuJoCo from Onshape | onshape-to-robot, or Onshape's own URDF export (`translateFormat`, `formatName: "URDF"`); both need A2 | 0.5–1 day after A2 | Medium | 3–220 (see E) |

## What the read-only probe found (2026-10-03)

The probe made 10 GET calls against the PR #170
[document](https://cad.onshape.com/documents/ae9f107d3972fc9d390e541f/w/b4151a24f733d0ffc48da6d2/e/dfbe0ae499cd860a85aa8da6),
using the lab's key with basic auth, as `onshape_build.py` does. All 10 returned 2xx, so all 10 count against the quota. Nothing was written.

| Call | Result |
|---|---|
| `getDocument` | Reachable. Owner is "Vertical Cloud Lab" (owner type 1, a company). The document is private. The key sees the full permission set, including DELETE, but the key's own scopes still exclude delete: #170 and #245 got 403s. |
| `getAssemblyDefinition` (`includeMateFeatures`, `includeMateConnectors`) | 72 instances and 72 occurrences, 29 distinct parts, no subassemblies. **No mates, no mate connectors, no fixed occurrence.** |
| `getFeatures` | Empty feature list. |
| `getFeatureSpecs` | 23 assembly feature types can be created, including:<br>• `mate`: SLIDER, CYLINDRICAL, REVOLUTE, PIN_SLOT, PLANAR, BALL, FASTENED, PARALLEL, with `limitsEnabled`, `limitAxialZMin/Max` and `limitZMin/Max`.<br>• `mateRelation`: GEAR, RACK_AND_PINION, SCREW, LINEAR, with `relationRatio` and `reverseDirection`.<br>• Also `mateConnector`, `mateGroup`, `animatemate`, `explosionStep`, `editMassProperties`, `editCustomMaterial` and `simulation`. |
| `getMateValues`, `getNamedPositions`, `getExplodedViews` | All empty. |
| `getAssemblyMassProperties` | Returned 200, but **mass is 0** because no part has a material. Volume is 2.56 L, including the mounting board. |
| `getAssemblyBoundingBoxes` | x −125 to 125 mm, y 0 to 285.8 mm, z −40 to 111.7 mm, including the board. |
| `getWMVEPsMetadata` (mounting-plate studio) | • Part names are the ones #170 set.<br>• Appearance is RGB 160,160,160. That is the STEP's own `COLOUR_RGB('Steel - Satin',0.627…)`, so **colour survives import**.<br>• Material is empty.<br>• Material, Appearance, Description, Part number and Revision are editable.<br>• No company custom properties. |
| Response headers | `X-Rate-Limit-Remaining` is 3000, 1000 or 250 depending on the endpoint and drops by 1 per call. This is the short-window limiter ([errors guide](https://onshape-public.github.io/docs/api-adv/errors/), 429 + `Retry-After`), not the annual quota. |

## A. text-to-cad → Onshape

**Geometry.** There are three ways to import:

- **Per-part Part Studios** (#170's approach) are right for the long-lived document. A changed STEP is updated in place: `uploadFileUpdateElement`, then `updatePartStudioFeature` to point the Import feature at the blob's new microversion. Part ids, tabs and instances survive this, so mates survive too.
- **One composite import** of a cadgen assembly STEP (`flattenAssemblies=false`) gives an assembly tab plus Part Studios, with instances already placed, in about 5 calls. But each re-import creates new tabs and ids, so mates and drawings made in Onshape are lost. Use it for review or hand-off copies, for example one per release tag.
- **A flattened import** (`flattenAssemblies=true`, as in byu-vcl #234 and #245) puts every part in place in one Part Studio. `evCollision` needs that layout (section D).

What comes through: solid and product names (#170 renames them in the STEP text; cadgen writes its labels as names) and per-body colour. What does not: materials, PMI, and the sidecar (kinematics, appearance, animation). Those have to be pushed as features or metadata.

**Batching (A1).** `modify` takes a list of `transformDefinitions`, and `insertTransformedInstances` inserts and places many instances in one call (plus one GET for their ids). Read `getAssemblyDefinition` once and send only the transforms that differ from `layout.py`:

```python
c.post(f"{base}/modify", json={"editDescription": "layout.py", "transformDefinitions": [
    {"isRelative": False, "occurrences": [{"path": [iid]}], "transform": M}  # 4x4 row-major, metres
    for iid, M in changed.items()]})
```

**Kinematics (A2).** cadgen's `<name>.step.json` holds a `kinematics` block: `mates` (`kind`, `parent`, `child`, `axis.origin`/`axis.dir` in world mm, `limits.value`), `couplings` (`gears: {dof: ratio}`) and `poses`. Each maps to an assembly feature (`addFeature`, body `BTFeatureDefinitionCall-1406`):

| cadgen | Onshape | Doser |
|---|---|---|
| `revolute(..., limits)` | 2 × `mateConnector` + `mate` REVOLUTE, `limitsEnabled`, `limitAxialZMin/Max` | Hinge 0–45°; auger in its brackets; both servo pinions; stepper pinion |
| `slider` / `cylindrical` | `mate` SLIDER (`limitZMin/Max`) / CYLINDRICAL | Solenoid plunger, 0–7.6 mm. The solenoid must first be split into frame and plunger (`purchased_parts.adafruit412_pieces()`). |
| `fastened`, or the children of a cadgen group | one `mateGroup` (`occurrencesQuery`) per rigid set | The 52 fasteners ride with their host parts; everything that tilts is one group |
| `couple("tilt", {"hinge": 1, "servo_l": -2, "servo_r": -2})` | one `mateRelation` GEAR per pair: `relationRatio` = abs(r_b / r_a), `reverseDirection` when the signs differ | 14T ↔ 28T: ratio 2; 20T ↔ 44T: ratio 2.2 |
| `poses` | No endpoint creates named positions. Set poses with `updateMateValues` (metres and radians). | Home; 45° tilt |
| `animation` | No Animate endpoint | Keep clips in cadgen |

- **Fix can't be set over REST** (nothing in the spec covers it). Fix the baseplate by hand once; it holds, because the sync never re-creates that instance.
- **Mate connectors need geometry.** The [assemblies guide](https://onshape-public.github.io/docs/api-adv/assemblies/) documents connectors on a face (`BTMInferenceQueryWithOccurrence-1083`, `CENTROID` inference). The sketch below finds the cylinder coaxial with the sidecar axis via `getPartStudioBodyDetails` and slides the connector along it onto the sidecar's origin, so the solver keeps the `layout.py` pose. The enum also has `PART_ORIGIN`; with an offset that would be simpler, but it is undocumented, so try it on a copy first.
- **Put the hinge first in every gear relation:** onshape-to-robot treats the first mate as the source and keeps one relation per target joint.
- **Make re-runs safe:** store the created feature ids in `onshape_document.json`, as #170 stores instance ids, and rebuild only when the sidecar's hash changes. Once mates exist, pose with `updateMateValues`, not transforms.

## B. Onshape → text-to-cad

- **Export a version, not the workspace.** Versions are immutable, so a commit can cite one (`getDocumentVersions` lists them; a push from git can mark its result with `createVersion`, named after the git SHA).
- **STEP:** `createAssemblyExportStep` (`POST /assemblies/d/{did}/v/{vid}/e/{eid}/export/step`, body `{"storeInDocument": false, "stepVersionString": "AP242"}`), poll `getTranslation` every 5–10 s until `DONE`, then `GET /documents/d/{did}/externaldata/{resultExternalDataIds[0]}`. Single parts: `createPartStudioExportStep`. Commit the result as an *imported* STEP (cadgen's term) under `STEP/imported/onshape/`, with the version id in the file name. glTF exports are for viewing only; Parasolid (`exportParasolid`) is no use, because OCC cannot read it.
- **Checks** run as for generated parts:
  - `read_scene`, then `overlap_volume`/`closest_points` across the tilt range. STEP carries no mates, so pose from the sidecar or from `getAssemblyDefinition` + `getMateValues`.
  - `mass_properties` with the density table.
  - `cadgen stl build`, then `$dfam-check` and `$gcode`; the same STL serves the DEM sim.
- **Triggers,** cheapest first:
  1. Manual: `workflow_dispatch` with a version id, or an `@claude` comment.
  2. A [webhook](https://onshape-public.github.io/docs/app-dev/webhook/) on `onshape.model.lifecycle.createversion` (not `onshape.model.lifecycle.changed`, which fires on every edit), registered with `createWebhook` `{documentId, events, url, options: {collapseEvents: true}, isTransient: false}`. The callback must be public HTTP(S) with a CA-signed certificate, which GitHub can't receive directly. A small relay (Cloudflare Worker or Lambda) checks `documentId`/`webhookId` and calls `POST /repos/vertical-cloud-lab/powder-doser/dispatches`. Notifications don't count against the quota. Don't expose the production Pi for this.
  3. Cron polling: 1 call per poll (365 a year if daily); only on a large plan.
- **Write-back:** one `createComment` per check run (summary plus a link to the Actions run). `updateWVEPMetadata` for lasting facts such as Revision, one part per call (no batch endpoint). Release candidates (`createReleasePackage`) need release management (Professional/Enterprise); skip them unless the company has it.

## C. Native, parametric Onshape parts

- **It works:** in byu-vcl #234, four sketches and four extrudes made through `addPartStudioFeature` gave the same volume as CadQuery, 108,840.279 mm³.
- **FeatureScript instead of feature JSON:** `createFeatureStudio`, then `updateFeatureStudioContents` (plain text, so it can live in git), then `addPartStudioFeature` with `namespace: "e<featureStudioId>::m<microversion>"` (the form #170 uses for its blob). `getFeatureScriptRepresentation` reads a hand-made Part Studio back as FeatureScript for review and diffs.
- **Shared numbers** (gear module, Ø25.0 tube, Ø25.5 bores) can live in a Variable Studio (`createVariableStudio`, `setVariables`, `setVariableStudioReferences`), synced from the JSON file the build123d models read.
- **Variants** such as "servos below" vs "servos above" can be an assembly configuration, which switches instances and mates but not mate connectors ([configurations guide](https://onshape-public.github.io/docs/api-adv/configs/)). Encode it with `encodeConfigurationMap` and pass it as `configuration=` to shaded views, mass properties, bounding boxes and exports.
- **Pros over build123d:** people who don't code can edit; drawings, BOM, configurations and release management are native; nothing is lost in translation.
- **Cons:** every regeneration and evaluation is a metered API call, and with no local kernel CI can't run offline. LLMs write build123d far more reliably than FeatureScript or feature JSON (#234 built only a simplified base natively and imported the rest). cadgen checks still need an export, and feature JSON is hard to review.

**Verdict:** keep build123d as the generator. Use native features only for the few parts people will own in Onshape, or for one reusable lab feature, such as a gear pair from module and tooth count. Onshape's public Spur Gear feature may already cover that.

## D. Checks inside Onshape

- **Interference:** Onshape has a UI tool ([help](https://cad.onshape.com/help/Content/View/interference_detection.htm)) but no REST endpoint; nothing in the spec matches interfere, clash or collision.
  - Workaround 1, the one to use: export to STEP and run cadgen's `overlap_volume` on each pair at sampled tilt angles, as #170's `layout.py` already does with OCC booleans.
  - Workaround 2: `evalFeatureScript` with `evCollision(context, {tools, targets})`, which returns `ClashType.INTERFERE`, `ABUT_*` and so on ([FsDoc](https://cad.onshape.com/FsDoc/library.html#evCollision-Context-map)). Part Studio only, so it needs a flattened import and checks one pose per call. It is a POST, so the probe didn't try it.
- **Mass and servo torque:** `getAssemblyMassProperties` works once parts have materials (Material metadata or `editCustomMaterial`) and the purchased parts (MG996R, NEMA 11, solenoid) have `editMassProperties` overrides. It only covers the whole assembly, so the tilting parts would need their own subassembly. Computing locally is cheaper and stays in git: `cadgen.geometry.mass_properties` on the tilting group gives mass and centre of mass. Take the moment about the hinge at each angle, then divide by 2 for the gear ratio and by 2 for the two servos.
- **Bounding boxes:** `getAssemblyBoundingBoxes` and `getPartStudioBoundingBoxes` are approximate ("meant for graphics", per the [FeatureScript guide](https://onshape-public.github.io/docs/api-adv/fs/)); `evBox3d` with `tight` is exact.
- **Views and animation:** `getNamedViews`, `getExplodedViews`, `getNamedPositions` and `getDisplayStates` read them, and `getAssemblyShadedViews` accepts `explodedViewId`, `namedPositionId`, `displayStateId` and `configuration`. Nothing creates named positions, exploded views or animations (`explosionStep` and `animatemate` are in the feature specs, but adding them via `addFeature` is untested). `updateMateValues` plus a shaded view costs 2 calls per frame; `cadgen step snapshot --kinematics/--animation --video` does it locally for free.

## E. Robotics and simulation

| Route | Needs | Gears | Cost |
|---|---|---|---|
| text-to-cad `$urdf` / `$sdf` skills | cadgen meshes per link, inertials from `mass_properties`, XML written by hand + `cadgen urdf validate` | `<mimic multiplier="-2">`, written by hand | 0 calls; reviewable in git |
| [onshape-to-robot](https://onshape-to-robot.readthedocs.io) v1.8.3 | A2 done, with mates named `dof_tilt`, `dof_auger`, `dof_tap`. Rigid sets grouped or FASTENED; otherwise every loose instance becomes its own link fixed to the base, which is wrong for anything that tilts. Materials or mass overrides. The first instance becomes the base. | Reads GEAR relations into URDF/SDF `<mimic>` and MuJoCo `<equality><joint polycoef>` | 100–220 calls on the first run (estimate: STL and mass per part). Only runs against versions are cached. Calls from its App Store app (announced April 2026) are exempt ([issue #170](https://github.com/Rhoban/onshape-to-robot/issues/170)). |
| Onshape URDF export ([March 2026](https://forum.onshape.com/discussion/30410/improvements-to-onshape-march-13-2026)) | A2 done; `translateFormat` with `formatName: "URDF"` and `urdfMeshFormat` | Not documented | 3–5 calls; users report problems with loops |

The mechanism is small: base, tilt body, auger, two servo pinions, the stepper pinion and the plunger. So the `$urdf` and `$sdf` skills are the default. MuJoCo output is the one thing only onshape-to-robot provides. Switch to it if Onshape becomes where the mechanism is edited, and run it against a version.

## Sketch: push the sidecar's mates into the #170 assembly (A2)

This has not been run yet. Try it on a `copyWorkspace` copy first. The feature and parameter names come from the live `getFeatureSpecs` response. The sketch assumes a connector's +Z points along the face's `direction`; the solver check on its last line catches the case where it doesn't.

```python
import json
import numpy as np
from onshape_build import DOC_JSON, Onshape        # PR #170's client and document record

def P(bt, pid, **kw): return {"btType": bt, "parameterId": pid, **kw}
def enum(pid, name, v): return P("BTMParameterEnum-145", pid, enumName=name, value=v)
def qty(pid, e, bt="BTMParameterQuantity-147"): return P(bt, pid, expression=e)
def flag(pid, v): return P("BTMParameterBoolean-144", pid, value=v)
def refs(pid, qs): return P("BTMParameterQueryWithOccurrenceList-67", pid, queries=qs)
def feats(pid, ids):
    return refs(pid, [{"btType": "BTMFeatureQueryWithOccurrence-157", "path": [], "featureId": i} for i in ids])
def vec(v): return np.array([v["x"], v["y"], v["z"]])

def add(c, base, bt, ftype, name, params):
    out = c.post(f"{base}/features", json={"btType": "BTFeatureDefinitionCall-1406", "feature": {
        "btType": bt, "featureType": ftype, "name": name, "parameters": params}})
    if out.get("featureState", {}).get("featureStatus") not in ("OK", "INFO"):
        raise RuntimeError(f"{name}: {out.get('featureState')}")
    return out["feature"]["featureId"]

def axis_connector(c, base, did, wid, inst, T, axis, name):
    """Connector on the face of `inst` that is coaxial with the sidecar axis, slid onto its origin."""
    Ti = np.linalg.inv(np.array(T).reshape(4, 4))                    # world -> part frame, metres
    o, d = (Ti @ np.r_[np.array(axis["origin"]) / 1000, 1])[:3], Ti[:3, :3] @ np.array(axis["dir"], float)
    bodies = c.get(f"/partstudios/d/{did}/w/{wid}/e/{inst['elementId']}/bodydetails")["bodies"]
    for f in next(b for b in bodies if b["id"] == inst["partId"])["faces"]:
        s = f["surface"]
        if s["type"] != "CYLINDER":
            continue
        fo, fd = vec(s["origin"]), vec(s["direction"])
        if np.linalg.norm(np.cross(fd, d)) < 1e-6 and np.linalg.norm(np.cross(o - fo, fd)) < 1e-5:
            mid = (vec(f["box"]["minCorner"]) + vec(f["box"]["maxCorner"])) / 2   # axis-aligned faces
            return add(c, base, "BTMMateConnector-66", "mateConnector", name, [
                enum("originType", "Origin type", "ON_ENTITY"),
                refs("originQuery", [{"btType": "BTMInferenceQueryWithOccurrence-1083", "inferenceType":
                     "MID_AXIS_POINT", "path": [inst["id"]], "deterministicIds": [f["id"]]}]),
                flag("transform", True), qty("translationZ", f"{np.dot(o - mid, fd) * 1000:.4f} mm")])
    raise LookupError(f"{name}: no cylinder on the sidecar axis")

def push_kinematics(sidecar, part_of, rigid_sets):
    """part_of: cadgen label -> Onshape part name (use #170 placement names for repeated parts);
    rigid_sets: lists of part names that move as one (each fastener goes with its host part)."""
    c, rec = Onshape(), json.loads(DOC_JSON.read_text())
    did, wid = rec["documentId"], rec["workspaceId"]
    base = f"/assemblies/d/{did}/w/{wid}/e/{rec['assembly']['elementId']}"
    T = {o["path"][0]: o["transform"] for o in c.get(base)["rootAssembly"]["occurrences"]}
    inst = {r["part"]: {"id": r["instanceId"], **r} for r in rec["assembly"]["instances"]}
    kin = json.load(open(sidecar))["kinematics"]
    for names in rigid_sets:
        add(c, base, "BTMMateGroup-65", "mateGroup", f"Group {names[0]}", [refs("occurrencesQuery",
            [{"btType": "BTMIndividualOccurrenceQuery-626", "path": [inst[n]["id"]]} for n in names])])
    mates = {}
    for m in (m for m in kin["mates"] if m["kind"] != "fastened"):   # fastened pairs are in rigid_sets
        ends = [inst[part_of[m[k].lstrip("#")]] for k in ("parent", "child")]
        mcs = [axis_connector(c, base, did, wid, i, T[i["id"]], m["axis"], f"{m['name']} {k}")
               for k, i in zip(("parent", "child"), ends)]
        params = [enum("mateType", "Mate type", m["kind"].upper()), feats("mateConnectorsQuery", mcs)]
        if "value" in m["limits"]:                                   # revolute: degrees; slider: mm
            u, lim = ("deg", "limitAxialZ") if m["kind"] == "revolute" else ("mm", "limitZ")
            params += [flag("limitsEnabled", True)] + [qty(lim + s, f"{v} {u}", "BTMParameterNullableQuantity-807")
                                                       for s, v in zip(("Min", "Max"), m["limits"]["value"])]
        mates[m["name"]] = add(c, base, "BTMMate-64", "mate", m["name"], params)
    for cp in kin.get("couplings", []):
        (a, ra), *rest = cp["gears"].items()                         # list the hinge first: it drives
        for b, rb in rest:
            add(c, base, "BTMMateRelation-1412", "mateRelation", f"{cp['name']} {a}:{b}", [
                enum("relationType", "Relation type", "GEAR"), feats("matesQuery", [mates[a], mates[b]]),
                qty("relationRatio", f"{abs(rb / ra):g}"), flag("reverseDirection", rb / ra < 0)])
    after = {o["path"][0]: o["transform"] for o in c.get(base)["rootAssembly"]["occurrences"]}
    print("moved by the solver:", [i for i in T if not np.allclose(T[i], after[i], atol=1e-5)] or "nothing")
```

For the doser, this comes to 6 movable mates (hinge, auger, two servo pinions, stepper pinion, plunger), 3 gear relations and a handful of groups. That is about 40 calls, once: each connector costs a `bodydetails` GET plus a POST, so cache `bodydetails` per Part Studio to save some.

## Recommendations, in order

1. **A1 now (1 h).** Batch the transforms, skip unchanged ones, render only on change, and give every script a call counter with a hard ceiling (byu-vcl #245 already logs `api_calls_used`). Check the company's plan: [annual quotas](https://onshape-public.github.io/docs/auth/limits/) are 2,500 per user (Free, Standard, EDU Student), 2,500 per company (EDU Educator), 5,000 per user (Professional) and 10,000 per full user (Enterprise). Failed calls, webhook notifications and public App Store apps don't count.
2. **A2 next (1–2 days).** Run it on a `copyWorkspace` copy and check that nothing moved, then Fix the baseplate by hand. After that, people can drag the tilt in Onshape, and B1 and E1 become possible.
3. **B1 once someone actually edits in Onshape (0.5–1 day).** Start with a manual trigger plus a comment back. Add the webhook relay only if it ends up used weekly.
4. **Materials and mass overrides (D), alongside A2 (1 h).** Keep the torque budget computed locally anyway.
5. **C and E only on demand.**

**Risks:**

- **Quota:** running out partway through a run; give each workflow a budget. Translations are polled, and every poll counts.
- **Broken mates:** a mate breaks when an imported part's faces change. Re-resolve connectors from the sidecar axis on every geometry update instead of storing face ids.
- **Ownership:** create documents with `ownerId` = the company and `ownerType: 1`, as #170 does (the probe confirmed that document is company-owned). API keys get 403 moving documents, so place them in folders with `copyWorkspace` + `parentId` (#245). The key has no delete scope: safer for CI, but superseded tabs are deleted by hand.
- **Terms of use:** Onshape forbids UI automation, so stay on REST (#234).
- **Source of truth:** never sync automatically in both directions. Git wins, and Onshape edits come back only as reviewed, versioned imports. Colours and names round-trip; materials, mates and sidecars don't travel inside STEP.
