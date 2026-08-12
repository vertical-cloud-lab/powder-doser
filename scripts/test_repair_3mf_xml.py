#!/usr/bin/env python3
"""Self-test for repair_model_settings_xml() in a1_mini_slice_and_send.py
- no printer or slicer required.

The regression this exists for: the BambuStudio CLI exporter writes
per-object config values into Metadata/model_settings.config without
XML-escaping them, so quoted list-typed options (compatible_printers,
print_extruder_variant) come out as value=""..."" - malformed XML. The
printer prints such a file fine (it only executes plate_1.gcode), but
Bambu Studio's importer aborts on it and the GUI reports the misleading
"The file does not contain any geometry data." (field-seen on
Thumbelina 2026-08-12; reproduced in CI against Studio 02.07.01.62 -
the repaired file then opens cleanly in the same Studio build).

    python test_repair_3mf_xml.py
"""

import importlib.util
import os
import sys
import tempfile
import xml.etree.ElementTree as ET
import zipfile

HERE = os.path.dirname(os.path.abspath(__file__))

PASSES, FAILURES = [], []


def check(name, cond):
    (PASSES if cond else FAILURES).append(name)
    print(f"{'ok  ' if cond else 'FAIL'}  {name}")


def load_module():
    path = os.path.join(HERE, "a1_mini_slice_and_send.py")
    spec = importlib.util.spec_from_file_location("_uut_slice", path)
    mod = importlib.util.module_from_spec(spec)
    sys.modules["_uut_slice"] = mod
    spec.loader.exec_module(mod)
    return mod


# The exact malformed shape the v02.06/v02.07 CLI writes (quotes come
# from opt_serialize on list-typed options; empty value="" is legal and
# must NOT be touched).
BROKEN_CONFIG = """<?xml version="1.0" encoding="UTF-8"?>
<config>
  <object id="2">
    <metadata key="name" value="cube.stl"/>
    <metadata key="compatible_printers" value=""Bambu Lab A1 mini 0.4 nozzle""/>
    <metadata key="compatible_printers_condition" value=""/>
    <metadata key="print_extruder_variant" value=""Direct Drive Standard""/>
  </object>
  <plate>
    <metadata key="plater_id" value="1"/>
    <metadata key="gcode_file" value="Metadata/plate_1.gcode"/>
  </plate>
</config>
"""

GCODE = b"; HEADER_BLOCK_START\n; printer_model = Bambu Lab A1 mini\nG28\n"


def make_3mf(path, config_text):
    with zipfile.ZipFile(path, "w", zipfile.ZIP_DEFLATED) as zf:
        zf.writestr("Metadata/model_settings.config", config_text)
        zf.writestr("Metadata/plate_1.gcode", GCODE)
        zf.writestr("3D/3dmodel.model", "<model/>")


def main():
    mod = load_module()
    tmp = tempfile.mkdtemp(prefix="repair3mf_")

    # 1. The malformed file is repaired: XML parses, values intact.
    p = os.path.join(tmp, "broken.gcode.3mf")
    make_3mf(p, BROKEN_CONFIG)
    check("broken config really is malformed XML",
          _parse_fails(BROKEN_CONFIG))
    check("repair reports a change", mod.repair_model_settings_xml(p) is True)
    fixed = zipfile.ZipFile(p).read(
        "Metadata/model_settings.config").decode()
    root = None
    try:
        root = ET.fromstring(fixed)
    except ET.ParseError:
        pass
    check("repaired config parses as XML", root is not None)
    if root is not None:
        vals = {m.get("key"): m.get("value")
                for m in root.iter("metadata")}
        check("quoted value survives round-trip",
              vals.get("compatible_printers")
              == '"Bambu Lab A1 mini 0.4 nozzle"')
        check("empty value untouched",
              vals.get("compatible_printers_condition") == "")

    # 2. The G-code entry is byte-identical - the print path may not
    #    change under any circumstances.
    check("gcode byte-identical after repair",
          zipfile.ZipFile(p).read("Metadata/plate_1.gcode") == GCODE)

    # 3. Idempotent: a second run is a no-op.
    check("second repair is a no-op",
          mod.repair_model_settings_xml(p) is False)

    # 4. A desktop-style file (already valid XML) is left untouched.
    p2 = os.path.join(tmp, "desktop.gcode.3mf")
    make_3mf(p2, BROKEN_CONFIG.replace(
        '""Bambu Lab A1 mini 0.4 nozzle""', '"ok"').replace(
        '""Direct Drive Standard""', '"ok"'))
    check("valid file untouched", mod.repair_model_settings_xml(p2) is False)

    # 5. A file without model_settings.config (bare-gcode zip) is a no-op.
    p3 = os.path.join(tmp, "bare.gcode.3mf")
    with zipfile.ZipFile(p3, "w") as zf:
        zf.writestr("Metadata/plate_1.gcode", GCODE)
    check("no model_settings.config is a no-op",
          mod.repair_model_settings_xml(p3) is False)

    # 6. Config broken beyond quote-escaping (truncated) - warn and
    #    leave the file alone rather than risk the print path.
    p4 = os.path.join(tmp, "truncated.gcode.3mf")
    make_3mf(p4, BROKEN_CONFIG[:200])
    before = zipfile.ZipFile(p4).read("Metadata/model_settings.config")
    check("still-broken config left untouched",
          mod.repair_model_settings_xml(p4) is False
          and zipfile.ZipFile(p4).read(
              "Metadata/model_settings.config") == before)

    print(f"\n{len(PASSES)} passed, {len(FAILURES)} failed")
    return 1 if FAILURES else 0


def _parse_fails(text):
    try:
        ET.fromstring(text)
        return False
    except ET.ParseError:
        return True


if __name__ == "__main__":
    sys.exit(main())
