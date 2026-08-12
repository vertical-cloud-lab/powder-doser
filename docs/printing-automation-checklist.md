# Programmatic printing — objectives checklist

One-page tracker for the lab's Bambu printer automation (A1 mini
"Thumbelina" + H2D). The two reference docs hold the *how*; this page is
only **what's done and what's left**, so objectives don't get lost in
the long-form notes. Check items off (and move them up) as they close.

Reference material:
[H2D doc](h2d-programmatic-access.md) ·
[A1 mini doc](a1-mini-programmatic-access.md) ·
[`scripts/`](../scripts) ·
[PR #23](https://github.com/vertical-cloud-lab/powder-doser/pull/23)
(the full field-debugging history).

## Guiding principles

- **Don't give up Bambu Studio.** The programmatic path is additive:
  desktop Studio (cloud or LAN) keeps working alongside it, and
  `--review` opens every headless slice in Studio for inspection before
  anything is sent. If a step would force a worse UI/workflow than
  Studio for no automation gain, don't take it.
- **Deterministic slicing.** A fixed, whitelisted set of profiles and
  per-job knobs (flattened profile bundles + `--supports` /
  `--set key=value`) rather than settings chosen on the fly.
- **Fail closed.** Wrong-printer, unsliced, and can't-load-filament
  payloads are refused; camera and limit checks abort rather than print
  blind; software guards never replace the hardware interlock.

## Done — verified on real hardware

- [x] LAN transport (MQTT `:8883` + implicit FTPS `:990` with TLS 1.2
      session reuse) — smoke test green on the H2D (2026-05-21) and the
      A1 mini (2026-07).
- [x] Pre-sliced `.gcode.3mf` → print on the **A1 mini**
      (2026-07-27 raw MQTT; 2026-08-04 via `bambulabs_api`).
- [x] Pre-sliced `.gcode.3mf` → print on the **H2D**
      (2026-08-11, `h2d_step4_bambulabs_api.py --expect-printer H2D`).
- [x] Repeat-print soak: same job sends and starts repeatedly with
      `--yes`, no human in the loop (2026-08-04).
- [x] AMS use + tray mapping auto-detected from the sliced file
      (no more hand-editing `use_ams`).
- [x] **Headless slicing, STL → 3MF → real part on the A1 mini**
      (2026-08-12), after fixing the two ghost-print causes (Cool-Plate
      bed default; missing start-G-code / filament-load in flattened
      profiles) — both now guarded against in code.
- [x] Slice inspection before sending: `--review` / `--save-sliced`
      keep the `.gcode.3mf`, which opens cleanly in Studio (CLI XML
      defect auto-repaired).
- [x] Picture access on the **A1 mini** (port-6000 frame capture,
      2026-08-12).
- [x] Latched-state handling (stale `FAILED`/`FINISH`/`print_error`)
      — every send script survives the printer's sticky status.

## Built — needs one verification run on hardware

- [ ] **Verify picture access on the H2D.** RTSPS capture is
      implemented; the field attempt failed only on missing `ffmpeg`,
      and the discovery fix (env var / `imageio-ffmpeg` / package
      managers) is committed but untested. Run: LAN Mode Liveview ON →
      `uv pip install imageio-ffmpeg` →
      `bambu_camera_check.py capture --transport rtsp`.
- [ ] **Reliable bed-clear check.** The simple pixel diff was proven
      too fragile in the field (moved plate → false "not clear").
      Alignment search, multi-reference folders, and the Claude-vision
      judge (`--judge llm`, needs `ANTHROPIC_API_KEY`) are committed
      but have never judged a live frame. Test both verdicts: once with
      a clear plate, once with a part deliberately left on it.
- [ ] **Slice for whichever printer the job targets.** Serial-prefix
      auto-detection + per-printer profiles/IDEX flags/limits are in
      `a1_mini_slice_and_send.py`, CI-verified against the real CLI —
      but no CLI-sliced file has yet *printed* on the H2D. One
      supervised run (`--review` first; `payloads/cube_h2d.gcode.3mf`
      is also ready as a pre-made payload).

## To build

- [ ] **Video streaming / live preview, both printers.** Only
      single-frame capture exists today. A1 mini: the port-6000
      protocol is a continuous frame stream; H2D: RTSPS plays in
      ffplay/VLC/go2rtc. Decide the consumer first (human preview page?
      failure detection?) — that determines whether this is a one-liner
      or a service.
- [ ] **One unified script.** Detect the input: pre-sliced
      `.gcode.3mf` → send as-is; STL / project 3MF → slice, then send.
      In practice: fold `a1_mini_slice_and_send.py`'s slicing stage
      into `h2d_step4_bambulabs_api.py`, which also gives the slice
      path `--camera-check`.
- [ ] **Read the AMS and resolve filaments dynamically.** Parse
      `ams.ams[].tray[]` telemetry (material, colour, remaining) so a
      job asks for "PLA" and the code picks the tray — failing fast
      when the material isn't loaded. Same telemetry carries the
      humidity readings the drying work needs.
- [ ] **Scheduled AMS drying cycles** (AMS HT / AMS 2 Pro, for TPU).
      The `ams_filament_drying` MQTT command is researched and
      documented in the
      [H2D doc](h2d-programmatic-access.md#future-work--scheduled-ams-drying-cycles-ams-ht--ams-2-pro);
      build it as a timer + on-demand route on the relay, skipping
      cycles while a print is running.
- [ ] **Pi relay (Steps 5–6).** Pi on the printers' network + Tailscale;
      FastAPI `/print` and `/print_stl` with the safety envelope.
      Caveat: the BambuStudio binary is x86-only, so slicing must live
      on an x86 box (lab PC / NUC / CI) even if a Pi does the sending.
- [ ] **Reachability from the Pi.** Run `h2d_smoketest.py` *from the
      lab Pi* against both printers — the one open network question.
      Long-term: byu-devices exemption / dedicated AP (the Shawn
      conversation) instead of relying on the currently-observed
      allowance.
- [ ] **Hardware interlock, installed and tested mid-print.** The
      [three options](h2d-programmatic-access.md#hardware-interlock--concrete-options)
      are picked out; this is the gate before anything runs unattended.
- [ ] **"Claude, print this."** The end goal: a request → (slice if
      needed) → camera check → send, driven by Claude over the tailnet
      via the Pi. The CI-runner-to-tailnet plumbing already exists;
      what's missing is the Pi-side blessed script + credentials.
- [ ] **Wire in real payloads.** Point the workflow at the
      `tensegrity-optimization` artifacts and powder-doser parts so a
      design iteration can dispatch its own print.
- [ ] **Supports quality test.** Slice + print an overhang part
      (benchy or similar) with `--supports tree`, reviewing in Studio
      first — confirms the headless path handles support-needing
      geometry, not just cubes.
- [ ] **Commit a CLI-sliced A1-mini reference payload** (like
      `payloads/cube_h2d.gcode.3mf`) so "does the CLI output print"
      has a fixed reference independent of anyone's local profiles.
