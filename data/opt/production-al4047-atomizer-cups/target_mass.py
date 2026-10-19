"""Powder to dispense for byu-vcl PR #232's 7.5 wt% point in the weighed cup (issue #186).

PR #232 defines the point as 4047 powder / (cup + plug + powder) = 7.5 wt%, and got 3.1 g from a
computed 38.71 g of 6063 (cup + plug). This cup was weighed (32.5074 g, without its plug), so the
plug is the one computed term left: its .508" x .5625" body less the #60 vent, at 2.69 g/cm^3,
as in byu-vcl atomizer-charge/composition_spread.py at e639fbd.

    python3 data/opt/production-al4047-atomizer-cups/target_mass.py
"""
import math

IN = 25.4
RHO_6063 = 2.69
W = 0.075                      # powder mass fraction of the charge
CUP_G = 32.5074                # weighed, without the plug (operator, issue #186)
ALREADY_IN_G = 0.0103          # leaked into the cup before the dose (operator)


def plug_g(d_in=0.508, l_in=0.5625, vent_in=0.040):
    area = math.pi * (d_in * IN / 2) ** 2 - math.pi * (vent_in * IN / 2) ** 2
    return area * l_in * IN / 1000 * RHO_6063


if __name__ == "__main__":
    plug = plug_g()
    total = W / (1 - W) * (CUP_G + plug)
    print(f"plug (computed)         {plug:.3f} g")
    print(f"powder for 7.5 wt%      {total:.4f} g")
    print(f"to dispense             {total - ALREADY_IN_G:.4f} g")
    print(f"per 0.1 g of plug error {W / (1 - W) * 0.1 * 1000:.1f} mg of powder")
