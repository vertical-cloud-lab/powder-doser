#!/usr/bin/env python3
"""Self-test for the dual-printer (A1 mini / H2D) support in
a1_mini_slice_and_send.py - no printer and no slicer install required.

Covers: serial-prefix / profile-based printer detection and its
conflict handling, the per-printer slicer command construction (via a
stub slicer binary that records its argv), the --supports/--set process
overrides, and the per-printer payload/limit checks.

    python test_dual_printer_slice.py
"""

import contextlib
import importlib.util
import io
import json
import os
import stat
import sys
import tempfile
import zipfile

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

PASSES, FAILURES = [], []


def check(name, cond, out=""):
    (PASSES if cond else FAILURES).append(name)
    print(f"{'ok  ' if cond else 'FAIL'}  {name}")
    if not cond and out:
        print("\n".join("      " + ln for ln in str(out).splitlines()))


def load():
    path = os.path.join(HERE, "a1_mini_slice_and_send.py")
    spec = importlib.util.spec_from_file_location("_uut_slice", path)
    mod = importlib.util.module_from_spec(spec)
    sys.modules["_uut_slice"] = mod
    spec.loader.exec_module(mod)
    return mod


def run_exit(fn, *a, **k):
    """Call fn, capturing stdout; return (result_or_None, SystemExit
    message or None, output)."""
    buf = io.StringIO()
    try:
        with contextlib.redirect_stdout(buf):
            return fn(*a, **k), None, buf.getvalue()
    except SystemExit as e:
        return None, str(e), buf.getvalue()


def make_sliced(path, model, fmap="1", bed=65, nozzle=220, load=True,
                ftype="PLA"):
    gcode = "\n".join([
        "; HEADER_BLOCK_START",
        f"; printer_model = {model}",
        f"; filament_map = {fmap}",
        f"; filament_type = {ftype}",
        "; total filament weight [g] : 3.94",
        f"; nozzle_temperature = {nozzle}",
        f"; textured_plate_temp_initial_layer = {bed}",
        "; curr_bed_type = Textured PEI Plate",
        "; CONFIG_BLOCK_END",
        "M620 S0A" if load else "; no load",
        f"M190 S{bed}",
        "G1 X0 Y0",
    ]) + "\n"
    with zipfile.ZipFile(path, "w") as z:
        z.writestr("Metadata/plate_1.gcode", gcode)
    return path


SLICER_STUB = """#!/usr/bin/env python3
import json, os, sys, zipfile
args = sys.argv[1:]
def val(flag):
    return args[args.index(flag) + 1]
out = val('--outputdir')
name = val('--export-3mf')
os.makedirs(out, exist_ok=True)
with open(os.path.join(out, 'args.json'), 'w') as f:
    json.dump(args, f)
with zipfile.ZipFile(os.path.join(out, name), 'w') as z:
    z.writestr('Metadata/plate_1.gcode', '; printer_model = stub\\n')
with open(os.path.join(out, 'result.json'), 'w') as f:
    json.dump({'return_code': 0, 'error_string': 'Success.'}, f)
"""


def main():
    mod = load()
    tmp = tempfile.mkdtemp(prefix="dual_test_")

    # --- detection --------------------------------------------------------
    check("alias: 'A1-Mini' -> a1mini",
          mod.normalize_printer_key("A1-Mini") == "a1mini")
    check("alias: 'Thumbelina' -> a1mini",
          mod.normalize_printer_key("Thumbelina") == "a1mini")
    check("alias: 'H2D' -> h2d", mod.normalize_printer_key("H2D") == "h2d")
    check("serial 030... -> a1mini",
          mod.printer_from_serial("0309CA123456789") == "a1mini")
    check("serial 0947... -> h2d (field-confirmed prefix)",
          mod.printer_from_serial("0947AJ622500469") == "h2d")
    check("serial 01P... -> unsupported P1S name",
          mod.printer_from_serial("01P00A123456789") == "P1S")
    check("unknown serial prefix -> None",
          mod.printer_from_serial("ZZZ00A123456789") is None)

    h2d_machine = os.path.join(tmp, "h2d_machine_flat.json")
    with open(h2d_machine, "w") as f:
        json.dump({"name": "Bambu Lab H2D 0.4 nozzle"}, f)
    check("machine JSON name -> h2d",
          mod.printer_from_machine_json(h2d_machine) == "h2d")

    p, err, _ = run_exit(mod.select_printer, "h2d", "0947AJ622500469",
                         None, False)
    check("explicit h2d + matching serial",
          err is None and p[0]["key"] == "h2d" and p[1] == "explicit")
    p, err, _ = run_exit(mod.select_printer, "auto", "0947AJ622500469",
                         None, False)
    check("auto-detect from H2D serial",
          err is None and p[0]["key"] == "h2d" and p[1] == "serial prefix")
    p, err, _ = run_exit(mod.select_printer, "auto", "0309CA123456789",
                         None, False)
    check("auto-detect from A1-mini serial",
          err is None and p[0]["key"] == "a1mini")
    p, err, _ = run_exit(mod.select_printer, "auto", None, h2d_machine, False)
    check("auto-detect falls back to the machine profile",
          err is None and p[0]["key"] == "h2d" and p[1] == "machine profile")
    _, err, _ = run_exit(mod.select_printer, "a1mini", "0947AJ622500469",
                         None, False)
    check("explicit a1mini vs H2D serial is refused",
          err is not None and "H2D" in err)
    p, err, out = run_exit(mod.select_printer, "a1mini", "0947AJ622500469",
                           None, True)
    check("...but --force downgrades it to a warning",
          err is None and p[0]["key"] == "a1mini" and "WARN" in out)
    _, err, _ = run_exit(mod.select_printer, "auto", "0309CA123456789",
                         h2d_machine, False)
    check("serial vs machine-profile conflict is refused",
          err is not None and "wrong machine" in err)
    _, err, _ = run_exit(mod.select_printer, "auto", "01P00A123456789",
                         None, False)
    check("unsupported model (P1S serial) is refused with its name",
          err is not None and "P1S" in err)
    _, err, _ = run_exit(mod.select_printer, "auto", None, None, False)
    check("nothing to detect from -> asks for --printer",
          err is not None and "--printer" in err)
    _, err, _ = run_exit(mod.select_printer, "p1s", None, None, False)
    check("unknown --printer value is refused",
          err is not None and "supported" in err)

    # --- process overrides ------------------------------------------------
    ov = mod.parse_process_overrides(["sparse_infill_density=25%"], "tree")
    check("--supports tree + --set compose",
          ov == {"enable_support": "1", "support_type": "tree(auto)",
                 "sparse_infill_density": "25%"})
    check("--supports off",
          mod.parse_process_overrides([], "off") == {"enable_support": "0"})
    _, err, _ = run_exit(mod.parse_process_overrides,
                         ["machine_start_gcode=G28"], None)
    check("--set outside the whitelist is refused",
          err is not None and "whitelist" in err)
    _, err, _ = run_exit(mod.parse_process_overrides, ["enable_support"],
                         None)
    check("--set without '=' is refused", err is not None)

    # --- per-printer payload / limit checks -------------------------------
    h2d_file = make_sliced(os.path.join(tmp, "h2d.gcode.3mf"),
                           "Bambu Lab H2D", fmap="1,2", bed=55)
    a1_file = make_sliced(os.path.join(tmp, "a1.gcode.3mf"),
                          "Bambu Lab A1 mini", fmap="1", bed=65)
    H2D = mod.PRINTERS["h2d"]
    A1 = mod.PRINTERS["a1mini"]

    _, err, _ = run_exit(mod.check_payload, h2d_file, False, H2D)
    check("H2D slice (filament_map 1,2) passes the H2D check", err is None)
    _, err, _ = run_exit(mod.check_payload, h2d_file, False, A1)
    check("H2D slice is refused for the A1 mini", err is not None)
    _, err, _ = run_exit(mod.check_payload, a1_file, False, A1)
    check("A1-mini slice passes the A1-mini check", err is None)
    _, err, _ = run_exit(mod.check_payload, a1_file, False, H2D)
    check("A1-mini slice is refused for the H2D", err is not None)

    hot = make_sliced(os.path.join(tmp, "hot.gcode.3mf"),
                      "Bambu Lab H2D", fmap="1,2", bed=100)
    _, err, _ = run_exit(mod.summarize_and_check, hot, False, H2D)
    check("100 C bed is fine for the H2D (max 110)", err is None)
    hot_a1 = make_sliced(os.path.join(tmp, "hot_a1.gcode.3mf"),
                         "Bambu Lab A1 mini", bed=100)
    _, err, _ = run_exit(mod.summarize_and_check, hot_a1, False, A1)
    check("100 C bed is refused for the A1 mini (max 80)",
          err is not None and "printer max 80" in err)

    # Low-bed jobs: TPU legitimately runs a 35 C textured-PEI bed
    # (Bambu's own TPU 85A setting) - allowed with a NOTE; the same
    # temperature on PLA is still the Cool Plate ghost-print trap.
    tpu_cold = make_sliced(os.path.join(tmp, "tpu_cold.gcode.3mf"),
                           "Bambu Lab H2D", fmap="1,2", bed=35,
                           nozzle=225, ftype="TPU")
    _, err, out = run_exit(mod.summarize_and_check, tpu_cold, False, H2D)
    check("35 C bed allowed for an all-TPU job",
          err is None and "TPU" in out and "Allowing" in out)
    pla_cold = make_sliced(os.path.join(tmp, "pla_cold.gcode.3mf"),
                           "Bambu Lab H2D", fmap="1,2", bed=35,
                           ftype="PLA;TPU")
    _, err, _ = run_exit(mod.summarize_and_check, pla_cold, False, H2D)
    check("35 C bed still refused when PLA is in the job",
          err is not None and "GHOST-PRINTS" in err)

    # IDEX jobs: the slot>1-implies-AMS inference must NOT auto-enable.
    r, err, out = run_exit(mod.apply_payload_ams, h2d_file, False, "",
                           False, False, True)
    check("IDEX payload leaves AMS flags alone",
          err is None and r == (False, "") and "IDEX job" in out)
    # Control: a file that really loads a slot > 1 (M620 S1A = project
    # slot 2) still auto-enables the AMS on a single-extruder printer.
    two_slot = os.path.join(tmp, "two_slot.gcode.3mf")
    with zipfile.ZipFile(two_slot, "w") as z:
        z.writestr("Metadata/plate_1.gcode",
                   "; CONFIG_BLOCK_END\nM620 S1A\nG1 X0\n")
    r, err, out = run_exit(mod.apply_payload_ams, two_slot, False, "",
                           False, False, False)
    check("(control) slot-2 file on a single-extruder printer auto-enables",
          err is None and r[0] is True)

    # --- profile auto-discovery -------------------------------------------
    for role in ("machine", "process", "filament"):
        p = os.path.join(tmp, f"a1mini_{role}_flat.json")
        with open(p, "w") as f:
            json.dump({"name": "x"}, f)
    stl = os.path.join(tmp, "part.stl")
    open(stl, "wb").close()
    (m, pr, fl, f2), err, out = run_exit(mod.discover_profiles, A1, stl,
                                         None, None, None)
    check("profiles auto-discovered next to the input file",
          err is None and all(x and os.path.isfile(x) for x in (m, pr, fl))
          and f2 is None and "auto-discovered" in out)
    explicit = os.path.join(tmp, "h2d_machine_flat.json")
    (m2, _, _, _), err, _ = run_exit(mod.discover_profiles, A1, stl,
                                     explicit, None, None)
    check("explicit profile path beats discovery", m2 == explicit)

    # H2D with only the generic h2d_* bundle on disk: found, and no
    # filament2 (left profile then runs both tools).
    for role in ("process", "filament"):
        with open(os.path.join(tmp, f"h2d_{role}_flat.json"), "w") as f:
            json.dump({"name": "x"}, f)
    (m, pr, fl, f2), err, out = run_exit(mod.discover_profiles, H2D, stl,
                                         None, None, None)
    check("H2D falls back to the h2d_* bundle when no tensegrity files",
          err is None and m and "h2d_machine" in m and f2 is None)
    # Add a full tensegrity bundle: it wins over h2d_* (it is what is
    # physically installed on the lab H2D), including the right-tool
    # filament2, and prefixes are never mixed.
    for role in ("machine", "process", "filament", "filament2"):
        with open(os.path.join(tmp, f"tensegrity_{role}_flat.json"), "w") as f:
            json.dump({"name": "Bambu Lab H2D 0.6 nozzle"}, f)
    (m, pr, fl, f2), err, out = run_exit(mod.discover_profiles, H2D, stl,
                                         None, None, None)
    check("tensegrity bundle wins for the H2D, filament2 included",
          err is None
          and all(x and "tensegrity_" in x for x in (m, pr, fl, f2)))
    check("no prefix mixing in discovery", "h2d_" not in (m + pr + fl + f2))

    # --- slicer command construction (stub slicer) ------------------------
    stub = os.path.join(tmp, "stub_slicer.py")
    with open(stub, "w") as f:
        f.write(SLICER_STUB)
    os.chmod(stub, os.stat(stub).st_mode | stat.S_IEXEC)
    os.environ.setdefault("DISPLAY", ":0")  # skip the xvfb-run wrapper

    proc_json = os.path.join(tmp, "proc.json")
    with open(proc_json, "w") as f:
        json.dump({"curr_bed_type": "Cool Plate"}, f)
    fil_json = os.path.join(tmp, "fil.json")
    with open(fil_json, "w") as f:
        json.dump({"name": "PLA"}, f)

    def slicer_args(printer, overrides=None, filament2=None):
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            export, out_dir = mod.slice_headless(
                stub, stl, "stl", h2d_machine, proc_json, fil_json,
                arrange=True, timeout_s=60, keep_dir=True,
                bed_type="Textured PEI Plate", printer=printer,
                overrides=overrides or {}, filament2=filament2)
        with open(os.path.join(out_dir, "args.json")) as f:
            args = json.load(f)
        return args, buf.getvalue()

    args, _ = slicer_args(H2D)
    fil_idx = args.index("--load-filaments") + 1
    check("H2D: filament profile loaded once per tool",
          args[fil_idx] == f"{fil_json};{fil_json}")
    check("H2D: Manual filament map 1,2",
          "--filament-map-mode" in args and "Manual" in args
          and args[args.index("--filament-map") + 1] == "1,2")
    check("H2D: --slice 1 (manual-map gating)",
          args[args.index("--slice") + 1] == "1")

    # Per-tool filaments (Tensegrity-inspired: PLA left, TPU 85A right).
    fil2_json = os.path.join(tmp, "fil2.json")
    with open(fil2_json, "w") as f:
        json.dump({"name": "TPU 85A"}, f)
    args, out = slicer_args(H2D, filament2=fil2_json)
    check("H2D: --filament2 gives left;right filament pair",
          args[args.index("--load-filaments") + 1]
          == f"{fil_json};{fil2_json}" and "Per-tool filaments" in out)
    check("H2D: per-tool pair keeps Manual map 1,2",
          args[args.index("--filament-map") + 1] == "1,2")
    _, err, _ = run_exit(mod.slice_headless, stub, stl, "stl", h2d_machine,
                         proc_json, fil_json, arrange=True, timeout_s=60,
                         keep_dir=True, printer=A1, filament2=fil2_json)
    check("--filament2 on a single-extruder printer is refused",
          err is not None and "dual-extruder" in err)

    args, _ = slicer_args(A1)
    check("A1 mini: single filament profile, no IDEX flags",
          args[args.index("--load-filaments") + 1] == fil_json
          and "--filament-map-mode" not in args)
    check("A1 mini: --slice 0", args[args.index("--slice") + 1] == "0")

    args, out = slicer_args(A1, {"enable_support": "1",
                                 "support_type": "tree(auto)"})
    patched = args[args.index("--load-settings") + 1].split(";")[1]
    with open(patched) as f:
        cfg = json.load(f)
    check("overrides + bed type land in the patched process copy",
          cfg.get("enable_support") == "1"
          and cfg.get("support_type") == "tree(auto)"
          and cfg.get("curr_bed_type") == "Textured PEI Plate"
          and "Process overrides" in out)

    # --- flattener: the tensegrity bundle ---------------------------------
    fpath = os.path.join(HERE, "flatten_bambu_profiles.py")
    fspec = importlib.util.spec_from_file_location("_uut_flatten", fpath)
    fmod = importlib.util.module_from_spec(fspec)
    sys.modules["_uut_flatten"] = fmod
    fspec.loader.exec_module(fmod)

    check("tensegrity bundle targets the 0.6-nozzle H2D",
          fmod.BUNDLES["tensegrity"]["printer"] == "Bambu Lab H2D 0.6 nozzle")
    check("tensegrity bundle: TPU 85A is the SECOND (right-tool) filament",
          fmod.BUNDLES["tensegrity"]["filaments"][1] == "Bambu TPU 85A @BBL H2D")

    # Synthetic profiles tree mirroring the real preset relationships
    # (0.6 machine inherits the 0.4 one, whose template sidecar carries
    # the real start G-code; TPU 85A pinned to extruder 2).
    tree = os.path.join(tmp, "studio", "resources", "profiles", "BBL")
    os.makedirs(tree, exist_ok=True)
    presets = [
        {"name": "Bambu Lab H2D 0.4 nozzle"},
        {"name": "Bambu Lab H2D 0.4 nozzle template machine_start_gcode",
         "machine_start_gcode": "M620 S[initial_extruder]A\nT[initial_extruder]"},
        {"name": "Bambu Lab H2D 0.6 nozzle",
         "inherits": "Bambu Lab H2D 0.4 nozzle",
         "nozzle_diameter": ["0.6", "0.6"]},
        {"name": "0.30mm Standard @BBL H2D 0.6 nozzle",
         "compatible_printers": ["Bambu Lab H2D 0.6 nozzle"]},
        {"name": "0.20mm Standard @BBL H2D",
         "compatible_printers": ["Bambu Lab H2D 0.4 nozzle"]},
        {"name": "Bambu PLA Basic @BBL H2D 0.6 nozzle",
         "compatible_printers": ["Bambu Lab H2D 0.6 nozzle"],
         "filament_type": ["PLA"]},
        {"name": "Bambu TPU 85A @BBL H2D",
         "compatible_printers": ["Bambu Lab H2D 0.6 nozzle",
                                 "Bambu Lab H2D 0.8 nozzle"],
         "filament_printable": ["2"], "filament_type": ["TPU"]},
    ]
    for i, p in enumerate(presets):
        with open(os.path.join(tree, f"p{i}.json"), "w") as f:
            json.dump(p, f)

    def run_flattener(*argv):
        old = sys.argv
        sys.argv = ["flatten_bambu_profiles.py",
                    "--studio-dir", os.path.join(tmp, "studio"),
                    "--outdir", os.path.join(tmp, "flat_out")] + list(argv)
        try:
            return run_exit(fmod.main)
        finally:
            sys.argv = old

    _, err, out = run_flattener("--for", "tensegrity")
    flat_dir = os.path.join(tmp, "flat_out")
    files = {n: os.path.join(flat_dir, f"tensegrity_{n}_flat.json")
             for n in ("machine", "process", "filament", "filament2")}
    check("--for tensegrity writes all four flat files",
          err is None and all(os.path.isfile(p) for p in files.values()),
          out)
    with open(files["machine"]) as f:
        mflat = json.load(f)
    check("tensegrity machine: template start G-code inherited from the "
          "0.4-nozzle sidecar (ghost-print guard)",
          "M620" in mflat.get("machine_start_gcode", "")
          and mflat.get("printer_settings_id") == "Bambu Lab H2D 0.6 nozzle")
    with open(files["filament2"]) as f:
        f2flat = json.load(f)
    check("tensegrity filament2 is the flattened TPU 85A",
          f2flat.get("name") == "Bambu TPU 85A @BBL H2D")
    check("TPU right-extruder restriction is surfaced",
          "only printable on the right extruder" in out)
    check("IDEX ready-to-slice hint uses the Manual-map recipe",
          "--filament-map" in out and "--slice 1" in out)

    # Reversed filament order (TPU first -> would map to the left
    # extruder, which its preset forbids) must warn.
    _, err, out = run_flattener("--for", "tensegrity",
                                "--filament", "Bambu TPU 85A @BBL H2D",
                                "--filament",
                                "Bambu PLA Basic @BBL H2D 0.6 nozzle")
    check("TPU in the left-tool position draws a reorder warning",
          err is None and "reorder" in out)

    # A 0.4-nozzle process preset with the 0.6-nozzle machine must warn.
    _, err, out = run_flattener("--for", "tensegrity",
                                "--process", "0.20mm Standard @BBL H2D")
    check("incompatible process/machine pairing draws a warning",
          err is None and "compatible_printers" in out and "WARN" in out)

    print(f"\n{len(PASSES)} passed, {len(FAILURES)} failed")
    for name in FAILURES:
        print(f"  FAILED: {name}")
    return 1 if FAILURES else 0


if __name__ == "__main__":
    sys.exit(main())
