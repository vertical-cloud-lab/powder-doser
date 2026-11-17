"""Where the electronics go: the PCB assembly on its printed holder,
standing on the board beside the doser (placed by ``ELECTRONICS_POSE``).
Returns None until the electronics models exist."""
from __future__ import annotations

from lib import frames as F

# The auger runs along y on x = 0 and reaches y = 286 at 0 deg, and the
# mounting plate, stepper and rear bracket sweep x = -46..54 behind the
# hinge, so nothing may stand behind the doser on its centre line
# (checks/electronics_clearance.py found the first pose, (0, 150) / (0, 190),
# cut by the tube and the plate).  The holder is turned -90 deg about z, so
# its 120 x 70 mm footprint runs along y with the components facing -x,
# towards the doser, and stands on the +X side of the board: x = 50..120,
# behind the servo and baseplate (y = 140..260, or 180..300 for the
# servos-above baseplate, which reaches y = 170).
_TURN = F.rot_about(F.Z, -90.0)
ELECTRONICS_POSE = {"below": F.T(None, (50.0, 200.0, 0.0)) @ _TURN,
                    "above": F.T(None, (50.0, 240.0, 0.0)) @ _TURN}


def electronics(variant: str):
    try:
        from pcb_holder_assembly import pcb_holder_assembly
    except ImportError:
        return None
    from lib.doser import _instance
    return _instance(pcb_holder_assembly(), ELECTRONICS_POSE[variant], "electronics")
