"""Where the electronics go: the PCB assembly on its printed holder,
standing on the board behind the doser (placed by ``ELECTRONICS_POSE``).
Returns None until the electronics models exist."""
from __future__ import annotations

from lib import frames as F

# holder origin on the board top, behind the doser, centred in x
# (filled in from src/electronics/README.md's recommended pose)
ELECTRONICS_POSE = {"below": F.T(None, (0.0, 150.0, 0.0)),
                    "above": F.T(None, (0.0, 190.0, 0.0))}


def electronics(variant: str):
    try:
        from pcb_holder_assembly import pcb_holder_assembly
    except ImportError:
        return None
    from lib.doser import _instance
    return _instance(pcb_holder_assembly(), ELECTRONICS_POSE[variant], "electronics")
