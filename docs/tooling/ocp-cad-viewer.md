# Assessment: OCP CAD Viewer for VS Code (CadQuery/build123d)

This note assesses the [OCP CAD Viewer](https://marketplace.visualstudio.com/items?itemName=bernhard-42.ocp-cad-viewer)
VS Code extension as a local, code-first workflow for the parametric CAD work
in this repository. It responds to the question raised in the project issue
"Explore use of OCP CAD Viewer VS Code extension for CadQuery" and is intended
as a short reference for collaborators deciding between cloud-based Onshape
sessions, [CQ-editor](https://github.com/CadQuery/CQ-editor), and an in-editor
CadQuery loop.

## TL;DR

- **Recommendation:** adopt OCP CAD Viewer as the **default local authoring
  loop** for any CadQuery (and build123d) work in this repo. Keep Onshape for
  collaborative review / classroom sharing, and treat CQ-editor as an
  occasional fallback when a contributor does not have VS Code.
- It gives the tightest feedback cycle of the three options (sub-second
  re-render on save), runs entirely against the same `cadquery` Python package
  we already script with, and does not require any change to how parts are
  stored in the repo (the canonical artefact is still a `cad_model.py` that
  exports STEP/STL).

## What it is

OCP CAD Viewer is a VS Code extension by Bernhard Walter (`bernhard-42`) that
embeds a [three-cad-viewer](https://github.com/bernhard-42/three-cad-viewer)
WebGL panel inside VS Code and streams tessellated geometry to it from a
running Python interpreter. The supported front-end libraries are:

- [CadQuery](https://github.com/cadquery/cadquery) (what this repo standardises
  on, per the `cad/<part-name>/<part-name>.py` convention)
- [build123d](https://github.com/gumyr/build123d) (CadQuery's successor-style
  fluent API, also OCP-based)

Both libraries sit on top of the same OpenCascade (OCP) kernel, so the viewer
can introspect any `cq.Workplane`, `cq.Shape`, `cq.Assembly`, or `build123d`
object and render it. The Python side is a small companion package,
[`ocp_vscode`](https://pypi.org/project/ocp-vscode/), which exposes a `show()`
helper and a `show_object()` shim compatible with CQ-editor.

Minimum viable usage:

```python
import cadquery as cq
from ocp_vscode import show

result = cq.Workplane().box(20, 10, 5).edges("|Z").fillet(1.0)
show(result)
```

Save the file (or run the cell) and the viewer panel updates in place.

## Why this fits the powder-doser workflow

Per the existing repository convention, each CAD part lives in
`cad/<part-name>/` as a parametric CadQuery script (`<part-name>.py`) plus
exported `.step`, `.stl`, and rendered `views/*.png`. The OCP CAD Viewer
slots into this without any structural change:

- **Same source artefact.** The viewer consumes the very `cq.Workplane` /
  `cq.Assembly` object that the script already builds before calling
  `cq.exporters.export(...)`. There is nothing new to commit; `ocp_vscode` is
  a dev-only dependency.
- **Same headless renders.** STEP/STL exports and the `render_views.py` VTK
  PNGs (the artefacts we actually commit and reference from READMEs) are
  unaffected. The viewer is purely an authoring aid.
- **No fork in the toolchain.** Both this extension and our existing
  `render_views.py` / `cad/meta-tools/render_step.py` pipeline depend on the
  same `cadquery` + OCP wheels, so contributors only need one Python
  environment.
- **Plays well with assemblies.** `show()` accepts `cq.Assembly`, and the
  viewer panel exposes a tree with per-child visibility/colour toggles —
  useful when iterating on multi-part work like the auger + bracket
  assemblies.

## Comparison

| Aspect | Onshape (current cloud workflow) | CQ-editor (standalone GUI) | **OCP CAD Viewer (VS Code)** |
|---|---|---|---|
| Authoring surface | Browser, mouse-driven feature tree | PyQt window with embedded code editor | The editor we already use (VS Code) |
| Feedback loop | Click-driven; good but requires context switches with code | Re-runs the whole script on F5 | Re-renders on save / per `show()` call; sub-second for small parts |
| Diff / review | Onshape revisions (separate from git) | Git-friendly (plain `.py`) | Git-friendly (plain `.py`) |
| Source of truth | Onshape document (mirrored to STEP) | The `.py` script | The `.py` script |
| Assemblies | Native, mate-based | Supported via `cq.Assembly`, basic viewer | Supported via `cq.Assembly`, tree + colours + transparency |
| Sharing with non-coders | Excellent (link to document) | Poor (must run Python) | Poor (must run Python); export STEP/PNG for sharing |
| Maintenance burden | Account/licence per contributor | One more GUI to install | One VS Code extension + one pip dep |
| Headless / CI | Manual STEP export | Headless mode is awkward | Decoupled from CI: CI keeps using `render_views.py` |

The "tighter feedback cycle than Onshape" intuition from the issue holds up in
practice — the win is not raw render speed (Onshape is fast too) but the
removal of the *code ↔ browser* context switch when the script *is* the model.

## Install / quickstart for this repo

1. Install the extension in VS Code: search for **"OCP CAD Viewer"** by
   `bernhard-42`, or `code --install-extension bernhard-42.ocp-cad-viewer`.
2. Activate the same Python environment you use for the existing
   `render_views.py` scripts (the one with `cadquery==2.7.0` and
   `cadquery-ocp`), then:

   ```sh
   pip install ocp-vscode
   ```

   `ocp-vscode` is the small Python-side companion. The extension can also
   bootstrap it via its "Quickstart CadQuery" button, but using our existing
   environment keeps versions aligned with `cad/meta-tools/`.
3. Make sure VS Code is using that interpreter (`Python: Select Interpreter`).
4. In any `cad/<part-name>/<part-name>.py`, add a guarded preview block, e.g.:

   ```python
   if __name__ == "__main__":
       try:
           from ocp_vscode import show
           show(result)  # or show(assembly)
       except ImportError:
           pass  # ocp_vscode is a dev-only dependency
   ```

   The `try/except` keeps headless CI runs (`render_views.py`,
   `cad/meta-tools/render_step.py`) working unchanged on machines without the
   extension.
5. Open the VS Code OCP sidebar, press **Open Viewer**, then run the file
   (`Run Python File` or `Shift+Enter` per cell with the Jupyter extension).

## Caveats / things to watch

- **Interpreter coupling.** The viewer talks to whichever Python interpreter
  VS Code has selected; if that drifts from the env where `cadquery` is
  installed, `show()` either errors or shows nothing. Document the expected
  env in each module's README the same way `render_views.py` does today.
- **VSCodium / Cursor / other forks.** Not published to the Open VSX
  marketplace; users on VSCodium must side-load the `.vsix` from the
  extension's GitHub releases page.
- **WebGL only.** Like Onshape, the viewer needs a working GPU/WebGL stack;
  remote SSH sessions over slow links can feel laggy. Headless rendering is
  still done by our existing VTK pipeline, not by this extension.
- **Not a substitute for committed renders.** The viewer is an authoring aid;
  `views/*.png` (or `renders/*.png`) committed via `render_views.py` remain
  the canonical previews referenced from READMEs and the paper.
- **No mesh/STL editor.** It visualises CadQuery/build123d objects (and STEP
  via `ocp_tessellate`), but it is not an alternative to MeshLab/Blender for
  imported meshes.

## Sources

- Extension on the VS Code Marketplace:
  <https://marketplace.visualstudio.com/items?itemName=bernhard-42.ocp-cad-viewer>
- Extension source and docs:
  <https://github.com/bernhard-42/vscode-ocp-cad-viewer>
- Python companion package: <https://pypi.org/project/ocp-vscode/>
- Underlying viewer component:
  <https://github.com/bernhard-42/three-cad-viewer>
- CadQuery (what this repo authors against): <https://github.com/cadquery/cadquery>
- CQ-editor (the standalone GUI alternative referenced in the issue):
  <https://github.com/CadQuery/CQ-editor>
