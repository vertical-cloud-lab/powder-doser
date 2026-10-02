import cadquery as cq

# Parameters
plate_length_x = 250.0
plate_width_y = 80.0
plate_thickness_z = 5.0
corner_radius = 6.0

# U-notch parameters
notch_depth_x = 24.0
notch_width_y = 31.0
notch_center_y = 0.0

# Hole parameters
hole_dia_m3 = 3.4
nema17_boss_dia = 22.4

# BRK-D hole group (near discharge end)
brk_d_center_x = 35.0
brk_d_center_y = 0.0
brk_d_spacing_x = 38.0
brk_d_spacing_y = 18.0

# TAP hole group
tap_center_x = 95.0
tap_center_y = 0.0
tap_spacing_x = 38.0
tap_spacing_y = 18.0

# BRK-M hole group (near motor end)
brk_m_center_x = 155.0
brk_m_center_y = 0.0
brk_m_spacing_x = 38.0
brk_m_spacing_y = 18.0

# NEMA-17 hole group
nema17_center_x = 215.0
nema17_center_y = 0.0
nema17_spacing = 31.0

# Hinge pillar parameters
hinge_pillar_center_x = 18.0
hinge_pillar_y_positions = [20.5, -20.5]
hinge_pillar_size_x = 14.0
hinge_pillar_size_y = 6.0
hinge_pillar_height_down = 24.5
hinge_pin_hole_dia = 5.2
hinge_pin_hole_depth_from_plate = 18.5

# Clevis tab parameters
clevis_center_x = 73.0
clevis_center_y = 0.0
clevis_size_x = 16.0
clevis_size_y = 6.0
clevis_height_down = 22.0
clevis_pin_hole_dia = 5.2
clevis_pin_hole_depth_from_top = 5.0

# Create main plate with rounded corners
# The plate top surface is at Z=0, extends to Z=-5
result = (
    cq.Workplane("XY")
    .box(plate_length_x, plate_width_y, plate_thickness_z, centered=(True, True, False))
    .translate((0, 0, -plate_thickness_z))  # Move so top is at Z=0
    .edges("|Z")
    .fillet(corner_radius)
)

# Create U-shaped notch at discharge end (X=0)
# Notch is 24mm deep along X, 31mm wide along Y, centered on Y=0
notch = (
    cq.Workplane("XY")
    .workplane(offset=-plate_thickness_z)
    .center(-plate_length_x/2 + notch_depth_x/2, notch_center_y)
    .box(notch_depth_x, notch_width_y, plate_thickness_z, centered=(True, True, False))
)
result = result.cut(notch)

# Compute hole positions for BRK-D group
brk_d_holes = [
    (brk_d_center_x - brk_d_spacing_x/2, brk_d_center_y - brk_d_spacing_y/2),
    (brk_d_center_x + brk_d_spacing_x/2, brk_d_center_y - brk_d_spacing_y/2),
    (brk_d_center_x - brk_d_spacing_x/2, brk_d_center_y + brk_d_spacing_y/2),
    (brk_d_center_x + brk_d_spacing_x/2, brk_d_center_y + brk_d_spacing_y/2),
]

# Compute hole positions for TAP group
tap_holes = [
    (tap_center_x - tap_spacing_x/2, tap_center_y - tap_spacing_y/2),
    (tap_center_x + tap_spacing_x/2, tap_center_y - tap_spacing_y/2),
    (tap_center_x - tap_spacing_x/2, tap_center_y + tap_spacing_y/2),
    (tap_center_x + tap_spacing_x/2, tap_center_y + tap_spacing_y/2),
]

# Compute hole positions for BRK-M group
brk_m_holes = [
    (brk_m_center_x - brk_m_spacing_x/2, brk_m_center_y - brk_m_spacing_y/2),
    (brk_m_center_x + brk_m_spacing_x/2, brk_m_center_y - brk_m_spacing_y/2),
    (brk_m_center_x - brk_m_spacing_x/2, brk_m_center_y + brk_m_spacing_y/2),
    (brk_m_center_x + brk_m_spacing_x/2, brk_m_center_y + brk_m_spacing_y/2),
]

# Compute hole positions for NEMA-17 group (square pattern)
nema17_holes = [
    (nema17_center_x - nema17_spacing/2, nema17_center_y - nema17_spacing/2),
    (nema17_center_x + nema17_spacing/2, nema17_center_y - nema17_spacing/2),
    (nema17_center_x - nema17_spacing/2, nema17_center_y + nema17_spacing/2),
    (nema17_center_x + nema17_spacing/2, nema17_center_y + nema17_spacing/2),
]

# Combine all M3 clearance hole positions
all_m3_holes = brk_d_holes + tap_holes + brk_m_holes + nema17_holes

# Drill all M3 clearance holes through the plate
result = (
    result.faces(">Z")
    .workplane()
    .pushPoints(all_m3_holes)
    .hole(hole_dia_m3)
)

# Drill NEMA-17 central boss clearance hole
result = (
    result.faces(">Z")
    .workplane()
    .center(nema17_center_x, nema17_center_y)
    .hole(nema17_boss_dia)
)

# Create first hinge pillar at Y = +20.5
hinge_pillar_1 = (
    cq.Workplane("XY")
    .workplane(offset=-plate_thickness_z)
    .center(hinge_pillar_center_x, hinge_pillar_y_positions[0])
    .box(hinge_pillar_size_x, hinge_pillar_size_y, hinge_pillar_height_down, 
         centered=(True, True, False))
    .translate((0, 0, -hinge_pillar_height_down))
)

# Create second hinge pillar at Y = -20.5
hinge_pillar_2 = (
    cq.Workplane("XY")
    .workplane(offset=-plate_thickness_z)
    .center(hinge_pillar_center_x, hinge_pillar_y_positions[1])
    .box(hinge_pillar_size_x, hinge_pillar_size_y, hinge_pillar_height_down, 
         centered=(True, True, False))
    .translate((0, 0, -hinge_pillar_height_down))
)

# Combine pillars with plate
result = result.union(hinge_pillar_1).union(hinge_pillar_2)

# Drill coaxial pin holes through both hinge pillars
# Pin holes are parallel to Y-axis, located 18.5mm below plate underside
pin_hole_z = -plate_thickness_z - hinge_pin_hole_depth_from_plate

# Create pin hole through first pillar (Y direction)
pin_hole_1 = (
    cq.Workplane("XZ")
    .workplane(offset=hinge_pillar_y_positions[0])
    .center(hinge_pillar_center_x, pin_hole_z)
    .circle(hinge_pin_hole_dia / 2)
    .extrude(hinge_pillar_size_y, both=True)
)

# Create pin hole through second pillar (Y direction)
pin_hole_2 = (
    cq.Workplane("XZ")
    .workplane(offset=hinge_pillar_y_positions[1])
    .center(hinge_pillar_center_x, pin_hole_z)
    .circle(hinge_pin_hole_dia / 2)
    .extrude(hinge_pillar_size_y, both=True)
)

result = result.cut(pin_hole_1).cut(pin_hole_2)

# Create clevis tab
clevis_tab = (
    cq.Workplane("XY")
    .workplane(offset=-plate_thickness_z)
    .center(clevis_center_x, clevis_center_y)
    .box(clevis_size_x, clevis_size_y, clevis_height_down, 
         centered=(True, True, False))
    .translate((0, 0, -clevis_height_down))
)

result = result.union(clevis_tab)

# Drill clevis pin hole (parallel to Y-axis, 5mm down from top of tab)
clevis_pin_hole_z = -plate_thickness_z - clevis_pin_hole_depth_from_top
clevis_pin_hole = (
    cq.Workplane("XZ")
    .workplane(offset=clevis_center_y)
    .center(clevis_center_x, clevis_pin_hole_z)
    .circle(clevis_pin_hole_dia / 2)
    .extrude(clevis_size_y, both=True)
)

result = result.cut(clevis_pin_hole)