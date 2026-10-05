"""The STEP that goes to Onshape: assembly_servos_above.step without the
electronics (the PCB holder and its 300 components stand beside the doser,
on the board, and don't move when the table is thinned).  Names, colours and
the assembly tree are kept (XCAF read -> remove one component -> write).

    python3 onshape/doser_step.py [out.step]
"""
from __future__ import annotations

import sys
from pathlib import Path

from OCP.IFSelect import IFSelect_RetDone
from OCP.STEPCAFControl import STEPCAFControl_Reader, STEPCAFControl_Writer
from OCP.STEPControl import STEPControl_AsIs
from OCP.TCollection import TCollection_ExtendedString
from OCP.TDataStd import TDataStd_Name
from OCP.TDF import TDF_LabelSequence
from OCP.TDocStd import TDocStd_Document
from OCP.XCAFDoc import XCAFDoc_DocumentTool

HERE = Path(__file__).resolve().parent
SRC = HERE.parent / "STEP" / "assembly_servos_above.step"
DROP = {"electronics"}


def _name(label) -> str:
    a = TDataStd_Name()
    return a.Get().ToExtString() if label.FindAttribute(TDataStd_Name.GetID_s(), a) else ""


def write(out: Path) -> Path:
    doc = TDocStd_Document(TCollection_ExtendedString("doser"))
    r = STEPCAFControl_Reader()
    r.SetNameMode(True)
    r.SetColorMode(True)
    if r.ReadFile(str(SRC)) != IFSelect_RetDone or not r.Transfer(doc):
        raise RuntimeError(f"could not read {SRC}")
    st = XCAFDoc_DocumentTool.ShapeTool_s(doc.Main())
    roots = TDF_LabelSequence()
    st.GetFreeShapes(roots)
    root = roots.Value(1)
    comps = TDF_LabelSequence()
    st.GetComponents_s(root, comps)
    dropped = [comps.Value(i) for i in range(1, comps.Length() + 1) if _name(comps.Value(i)) in DROP]
    names = [_name(lab) for lab in dropped]      # read before removal: removed labels are dead
    for lab in dropped:
        st.RemoveComponent(lab)
    st.UpdateAssemblies()
    w = STEPCAFControl_Writer()
    w.SetNameMode(True)
    w.SetColorMode(True)
    # the root label only: the removed sub-assembly's definition is still in
    # the document as a free shape and would otherwise be written as a root
    w.Transfer(root, STEPControl_AsIs)
    if w.Write(str(out)) != IFSelect_RetDone:
        raise RuntimeError(f"could not write {out}")
    print(f"{out}: dropped {names or 'nothing'}, "
          f"{out.stat().st_size / 1e6:.1f} MB")
    return out


if __name__ == "__main__":
    write(Path(sys.argv[1]) if len(sys.argv) > 1 else Path("/tmp/os/doser_servos_above.step"))
