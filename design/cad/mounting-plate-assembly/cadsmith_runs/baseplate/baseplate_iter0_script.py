import cadquery as cq

# Parameters
baseplate_length_x = 300.0
baseplate_width_y = 200.0
baseplate_thickness_z = 6.0
baseplate_x_start = -30.0
baseplate_x_end = 270.0
baseplate_y_center = 0.0
corner_radius = 8.0

discharge_cutout_x = 70.0
discharge_cutout_y = 70.0
discharge_cutout_center_x = 18.0
discharge_cutout_center_y = 0.0

hinge_pillar_width_x = 14.0
hinge_pillar_depth_y = 6.0
hinge_pillar_height_z = 50.0
hinge_pillar_x_center = 18.0
hinge_pillar_y_positions = [27.5, -27.5]
hinge_pin_hole_diameter = 5.2
hinge_pin_hole_height_above_plate = 21.0

clevis_lug_width_x = 14.0
clevis_lug_depth_y = 4.0
clevis_lug_height_z = 25.0
clevis_lug_positions = [(148.0, 8.0), (148.0, -8.0)]
clevis_pin_hole_diameter = 5.2
clevis_pin_hole_depth_from_top = 5.0

leg_cross_section = 18.0
leg_height_z = 150.0
leg_positions = [(-17.0, -87.0), (-17.0, 87.0), (257.0, -87.0), (257.0, 87.0)]
leg_m4_hole_diameter = 4.4
leg_m4_hole_height_from_bottom = 15.0

# Create baseplate with rounded corners, positioned at X=-30 to X=270, centered on Y=0
baseplate_center_x = (baseplate_x_start + baseplate_x_end) / 2.0
baseplate = (
    cq.Workplane("XY")
    .center(baseplate_center_x, baseplate_y_center)
    .rect(baseplate_length_x, baseplate_width_y)
    .extrude(baseplate_thickness_z)
    .edges("|Z")
    .fillet(corner_radius)
)

# Cut discharge opening through the plate
baseplate = (
    baseplate
    .faces(">Z")
    .workplane()
    .center(discharge_cutout_center_x - baseplate_center_x, discharge_cutout_center_y)
    .rect(discharge_cutout_x, discharge_cutout_y)
    .cutThruAll()
)

# Add hinge pillars extending upward from top face
for y_pos in hinge_pillar_y_positions:
    pillar = (
        cq.Workplane("XY")
        .workplane(offset=baseplate_thickness_z)
        .center(hinge_pillar_x_center, y_pos)
        .rect(hinge_pillar_width_x, hinge_pillar_depth_y)
        .extrude(hinge_pillar_height_z)
    )
    baseplate = baseplate.union(pillar)

# Drill coaxial hinge pin holes through both pillars
# Pin holes are at height = baseplate_thickness_z + hinge_pin_hole_height_above_plate
pin_hole_z = baseplate_thickness_z + hinge_pin_hole_height_above_plate
baseplate = (
    baseplate
    .faces(">Y")
    .workplane(centerOption="CenterOfBoundBox")
    .center(hinge_pillar_x_center - baseplate_center_x, pin_hole_z)
    .hole(hinge_pin_hole_diameter, depth=hinge_pillar_depth_y * 2 + 100)
)

# Add clevis lugs extending upward from top face
for (x_pos, y_pos) in clevis_lug_positions:
    lug = (
        cq.Workplane("XY")
        .workplane(offset=baseplate_thickness_z)
        .center(x_pos, y_pos)
        .rect(clevis_lug_width_x, clevis_lug_depth_y)
        .extrude(clevis_lug_height_z)
    )
    baseplate = baseplate.union(lug)

# Drill clevis pin holes through each lug
# Pin holes are 5mm below the top of the lug
clevis_pin_hole_z = baseplate_thickness_z + clevis_lug_height_z - clevis_pin_hole_depth_from_top
for (x_pos, y_pos) in clevis_lug_positions:
    baseplate = (
        baseplate
        .faces(">Y" if y_pos > 0 else "<Y")
        .workplane(centerOption="CenterOfBoundBox")
        .center(x_pos - baseplate_center_x, clevis_pin_hole_z)
        .hole(clevis_pin_hole_diameter, depth=clevis_lug_depth_y + 10)
    )

# Add four support legs extending downward from bottom face
for (x_pos, y_pos) in leg_positions:
    leg = (
        cq.Workplane("XY")
        .center(x_pos, y_pos)
        .rect(leg_cross_section, leg_cross_section)
        .extrude(-leg_height_z)
    )
    baseplate = baseplate.union(leg)

# Drill M4 clearance holes through outermost X face of each leg
# Holes are 15mm above the bottom of each leg (i.e., at z = -leg_height_z + 15)
m4_hole_z = -leg_height_z + leg_m4_hole_height_from_bottom

# For legs at X=-17, drill through the -X face (leftmost)
for (x_pos, y_pos) in [(-17.0, -87.0), (-17.0, 87.0)]:
    baseplate = (
        baseplate
        .faces("<X")
        .workplane(centerOption="CenterOfBoundBox")
        .center(y_pos, m4_hole_z)
        .hole(leg_m4_hole_diameter, depth=leg_cross_section + 10)
    )

# For legs at X=257, drill through the +X face (rightmost)
for (x_pos, y_pos) in [(257.0, -87.0), (257.0, 87.0)]:
    baseplate = (
        baseplate
        .faces(">X")
        .workplane(centerOption="CenterOfBoundBox")
        .center(y_pos, m4_hole_z)
        .hole(leg_m4_hole_diameter, depth=leg_cross_section + 10)
    )

result = baseplate