"""FC-1 Faraday-cup charge amplifier: single source of the design data.

Used by gen_sch.py (schematic) and build_pcb.py (board). Coordinates on the
board are KiCad's (mm, origin top-left of the 50 x 40 board, y down).
"""

BOARD_W, BOARD_H = 50.0, 40.0
VERSION = "1.0"
DATE = "2026-11-28"

# ---------------------------------------------------------------- components
# ref: (lib_id, value, footprint, {pin: net}, extra fields)
# Nets: SUM is the inverting input (the guarded node); GUARD is the ADA4530-1
# guard-buffer output; REF is the 2.5 V mid-rail reference.
R0805 = "Resistor_SMD:R_0805_2012Metric_Pad1.20x1.40mm_HandSolder"
R1206 = "Resistor_SMD:R_1206_3216Metric_Pad1.30x1.75mm_HandSolder"
C0805 = "Capacitor_SMD:C_0805_2012Metric_Pad1.18x1.45mm_HandSolder"
C1206 = "Capacitor_SMD:C_1206_3216Metric_Pad1.33x1.80mm_HandSolder"
LED0805 = "LED_SMD:LED_0805_2012Metric_Pad1.15x1.40mm_HandSolder"
SOT23 = "Package_TO_SOT_SMD:SOT-23"

def two(a, b):
    return {"1": a, "2": b}

PARTS = {
    # --- input and integrator
    "J1": ("Connector:Conn_Coaxial", "BNC IN", "Connector_Coaxial:BNC_Amphenol_031-5539_Vertical",
           {"1": "SUM", "2": "SHELL"}, {"MPN": "031-5539", "Manufacturer": "Amphenol RF"}),
    "JP5": ("Jumper:SolderJumper_3_Open", "SHELL: 1-2 GND, 2-3 GUARD", "Jumper:SolderJumper-3_P1.3mm_Open_RoundedPad1.0x1.5mm_NumberLabels",
            {"1": "GND", "2": "SHELL", "3": "GUARD"}, {}),
    "U1": ("Amplifier_Operational:ADA4530-1", "ADA4530-1ARZ", "Package_SO:SOIC-8_3.9x4.9mm_P1.27mm",
           {"1": "REF", "2": "GUARD", "3": None, "4": "GND", "5": "+5VA", "6": "OUT", "7": "GUARD", "8": "SUM"},
           {"MPN": "ADA4530-1ARZ", "Manufacturer": "Analog Devices"}),
    "C1": ("Device:C", "10nF C0G 1%", C1206, two("SUM", "OUT"),
           {"MPN": "CC1206FKNPO9BN103", "Manufacturer": "Yageo", "Note": "C_f low range"}),
    "C2": ("Device:C", "100nF C0G", C1206, two("SUM", "CF2"),
           {"MPN": "C3216C0G1H104J160AA", "Manufacturer": "TDK", "Note": "C_f high range (adds to C1 via JP1)"}),
    "R1": ("Device:R", "DNP (10G)", R1206, two("SUM", "OUT"),
           {"MPN": "HVC1206Z1008KET", "Manufacturer": "Ohmite", "Note": "optional drift bleed, not fitted"}),
    "JP1": ("Jumper:Jumper_2_Open", "RANGE x10", "Connector_PinHeader_2.54mm:PinHeader_1x02_P2.54mm_Vertical",
            two("CF2", "OUT"), {"MPN": "PREC002SAAN-RC + SPC02SYAN", "Manufacturer": "Sullins"}),
    "K1": ("fc1:Coto_9002", "9002-05-01", "fc1:Relay_SPST-NO_Coto_9002_SIP6",
           {"1": "SUM", "4": "RST_SW", "2": "+5V", "3": "COIL_N", "5": "GUARD", "6": None},
           {"MPN": "9002-05-01", "Manufacturer": "Coto Technology"}),
    "R2": ("Device:R", "100R", R0805, two("RST_SW", "OUT"), {"MPN": "RMCF0805FT100R", "Manufacturer": "Stackpole"}),
    # --- reset driver
    "Q1": ("Transistor_BJT:MMBT3904", "MMBT3904", SOT23, {"1": "RST_B", "2": "GND", "3": "COIL_N"},
           {"MPN": "MMBT3904LT1G", "Manufacturer": "onsemi"}),
    "D1": ("Diode:1N4148W", "1N4148W", "Diode_SMD:D_SOD-123", {"1": "+5V", "2": "COIL_N"},
           {"MPN": "1N4148W-TP", "Manufacturer": "Micro Commercial Co"}),
    "R11": ("Device:R", "4k7", R0805, two("RESET_IN", "RST_B"), {"MPN": "RC0805FR-074K7L", "Manufacturer": "Yageo"}),
    "R12": ("Device:R", "100k", R0805, two("RST_B", "GND"), {"MPN": "RC0805FR-07100KL", "Manufacturer": "Yageo"}),
    "D2": ("Device:LED", "RST yellow", LED0805, {"1": "COIL_N", "2": "LED_RST"},
           {"MPN": "LTST-C171KSKT", "Manufacturer": "Lite-On"}),
    "R13": ("Device:R", "1k5", R0805, two("+5V", "LED_RST"), {"MPN": "RC0805FR-071K5L", "Manufacturer": "Yageo"}),
    # --- reference and power
    "U2": ("Reference_Voltage:REF3025", "REF3025AIDBZR", SOT23, {"1": "+5VA", "2": "REF", "3": "GND"},
           {"MPN": "REF3025AIDBZR", "Manufacturer": "Texas Instruments"}),
    "C5": ("Device:C", "1uF", C0805, two("+5VA", "GND"), {"MPN": "CL21B105KAFNNNE", "Manufacturer": "Samsung"}),
    "C6": ("Device:C", "1uF", C0805, two("REF", "GND"), {"MPN": "CL21B105KAFNNNE", "Manufacturer": "Samsung"}),
    "R5": ("Device:R", "10R", R0805, two("+5V", "+5VA"), {"MPN": "RC0805FR-0710RL", "Manufacturer": "Yageo"}),
    "C10": ("Device:C", "10uF", C0805, two("+5V", "GND"), {"MPN": "GRM21BR61E106KA73L", "Manufacturer": "Murata"}),
    "C4": ("Device:C", "10uF", C0805, two("+5VA", "GND"), {"MPN": "GRM21BR61E106KA73L", "Manufacturer": "Murata"}),
    "C3": ("Device:C", "100nF", C0805, two("+5VA", "GND"), {"MPN": "CL21B104KBCNNNC", "Manufacturer": "Samsung"}),
    "D3": ("Device:LED", "PWR green", LED0805, {"1": "GND", "2": "LED_PWR"},
           {"MPN": "LTST-C171GKT", "Manufacturer": "Lite-On"}),
    "R14": ("Device:R", "2k2", R0805, two("+5V", "LED_PWR"), {"MPN": "RC0805FR-072K2L", "Manufacturer": "Yageo"}),
    # --- ADC
    "U3": ("Analog_ADC:ADS1115IDGS", "ADS1115IDGSR", "Package_SO:MSOP-10_3x3mm_P0.5mm",
           {"1": "ADDR", "2": None, "3": "GND", "4": "AIN0", "5": "AIN1", "6": None, "7": None,
            "8": "+5VA", "9": "SDA5", "10": "SCL5"},
           {"MPN": "ADS1115IDGSR", "Manufacturer": "Texas Instruments"}),
    "R3": ("Device:R", "1k", R0805, two("OUT", "AIN0"), {"MPN": "RC0805FR-071KL", "Manufacturer": "Yageo"}),
    "R4": ("Device:R", "1k", R0805, two("REF", "AIN1"), {"MPN": "RC0805FR-071KL", "Manufacturer": "Yageo"}),
    "C7": ("Device:C", "10nF C0G", C0805, two("AIN0", "GND"), {"MPN": "GRM2195C1H103JA01D", "Manufacturer": "Murata"}),
    "C8": ("Device:C", "10nF C0G", C0805, two("AIN1", "GND"), {"MPN": "GRM2195C1H103JA01D", "Manufacturer": "Murata"}),
    "C9": ("Device:C", "100nF", C0805, two("+5VA", "GND"), {"MPN": "CL21B104KBCNNNC", "Manufacturer": "Samsung"}),
    "R10": ("Device:R", "100k", R0805, two("ADDR", "GND"), {"MPN": "RC0805FR-07100KL", "Manufacturer": "Yageo"}),
    "JP2": ("Jumper:SolderJumper_2_Open", "ADDR=VDD 0x49", "Jumper:SolderJumper-2_P1.3mm_Open_RoundedPad1.0x1.5mm",
            two("ADDR", "+5VA"), {}),
    "JP3": ("Jumper:SolderJumper_2_Open", "ADDR=SDA 0x4A", "Jumper:SolderJumper-2_P1.3mm_Open_RoundedPad1.0x1.5mm",
            two("ADDR", "SDA5"), {}),
    "JP4": ("Jumper:SolderJumper_2_Open", "ADDR=SCL 0x4B", "Jumper:SolderJumper-2_P1.3mm_Open_RoundedPad1.0x1.5mm",
            two("ADDR", "SCL5"), {}),
    # --- I2C level shift (3.3 V bus <-> 5 V ADC)
    "Q2": ("Transistor_FET:BSS138", "BSS138", SOT23, {"1": "+3V3", "2": "SDA", "3": "SDA5"},
           {"MPN": "BSS138", "Manufacturer": "onsemi"}),
    "Q3": ("Transistor_FET:BSS138", "BSS138", SOT23, {"1": "+3V3", "2": "SCL", "3": "SCL5"},
           {"MPN": "BSS138", "Manufacturer": "onsemi"}),
    "R6": ("Device:R", "10k", R0805, two("+3V3", "SDA"), {"MPN": "RC0805FR-0710KL", "Manufacturer": "Yageo"}),
    "R7": ("Device:R", "10k", R0805, two("+3V3", "SCL"), {"MPN": "RC0805FR-0710KL", "Manufacturer": "Yageo"}),
    "R8": ("Device:R", "10k", R0805, two("+5VA", "SDA5"), {"MPN": "RC0805FR-0710KL", "Manufacturer": "Yageo"}),
    "R9": ("Device:R", "10k", R0805, two("+5VA", "SCL5"), {"MPN": "RC0805FR-0710KL", "Manufacturer": "Yageo"}),
    "C11": ("Device:C", "100nF", C0805, two("+3V3", "GND"), {"MPN": "CL21B104KBCNNNC", "Manufacturer": "Samsung"}),
    # --- connectors
    "J2": ("Connector_Generic:Conn_01x04", "STEMMA QT", "Connector_JST:JST_SH_SM04B-SRSS-TB_1x04-1MP_P1.00mm_Horizontal",
           {"1": "GND", "2": "+3V3", "3": "SDA", "4": "SCL"}, {"MPN": "SM04B-SRSS-TB(LF)(SN)", "Manufacturer": "JST"}),
    "J3": ("Connector_Generic:Conn_01x04", "STEMMA QT", "Connector_JST:JST_SH_SM04B-SRSS-TB_1x04-1MP_P1.00mm_Horizontal",
           {"1": "GND", "2": "+3V3", "3": "SDA", "4": "SCL"}, {"MPN": "SM04B-SRSS-TB(LF)(SN)", "Manufacturer": "JST"}),
    "J4": ("Connector_Generic:Conn_01x06", "PICO", "Connector_PinHeader_2.54mm:PinHeader_1x06_P2.54mm_Vertical",
           {"1": "GND", "2": "+5V", "3": "+3V3", "4": "SDA", "5": "SCL", "6": "RESET_IN"},
           {"MPN": "PREC006SAAN-RC", "Manufacturer": "Sullins"}),
    # --- test points, chassis, holes
    "TP1": ("Connector:TestPoint", "OUT", "TestPoint:TestPoint_THTPad_D1.5mm_Drill0.7mm", {"1": "OUT"}, {}),
    "H5": ("Mechanical:MountingHole_Pad", "CAN lug M3", "MountingHole:MountingHole_3.2mm_M3_Pad_Via", {"1": "CHASSIS"}, {}),
    "R15": ("Device:R", "0R", R1206, two("CHASSIS", "GND"), {"MPN": "RC1206JR-070RL", "Manufacturer": "Yageo",
            "Note": "can-to-GND link at the BNC; remove to float the can"}),
    "H1": ("Mechanical:MountingHole", "M3", "MountingHole:MountingHole_3.2mm_M3", {}, {}),
    "H2": ("Mechanical:MountingHole", "M3", "MountingHole:MountingHole_3.2mm_M3", {}, {}),
    "H3": ("Mechanical:MountingHole", "M3", "MountingHole:MountingHole_3.2mm_M3", {}, {}),
    "H4": ("Mechanical:MountingHole", "M3", "MountingHole:MountingHole_3.2mm_M3", {}, {}),
    "H6": ("Mechanical:MountingHole", "PTFE standoff", "MountingHole:MountingHole_2.2mm_M2", {}, {}),
}

DNP = {"R1"}
NOT_IN_BOM = {"H1", "H2", "H3", "H4", "H5", "H6", "TP1", "JP2", "JP3", "JP4", "JP5"}

# ------------------------------------------------------------ board placement
# ref: (x, y, rotation_deg, side)  -- KiCad board coordinates, y down
PLACE = {
    "H1": (3.5, 3.5, 0, "F"), "H2": (46.5, 3.5, 0, "F"), "H3": (3.5, 36.5, 0, "F"), "H4": (46.5, 36.5, 0, "F"),
    # analog input (hand-routed, see build_pcb.hand_route)
    "J1": (8.5, 21.5, 180, "F"),
    "JP5": (9.0, 31.0, 0, "F"),
    "U1": (25.0, 23.975, 90, "F"),
    "C1": (20.06, 17.5, 0, "F"),
    "R1": (20.06, 14.0, 0, "F"),
    "C2": (20.06, 10.5, 0, "F"),
    "K1": (18.5, 4.0, 0, "F"),
    "JP1": (24.5, 11.3, 0, "F"),
    "D1": (26.12, 8.3, 0, "F"),
    "R2": (33.74, 9.2, 270, "F"),
    "H6": (19.0, 26.8, 0, "F"),
    "TP1": (27.8, 18.6, 0, "F"),
    # reset driver
    "Q1": (30.2, 11.6, 0, "F"),
    "R11": (29.4, 15.4, 270, "F"),
    "R12": (31.6, 15.4, 270, "F"),
    "D2": (39.6, 4.4, 0, "F"),
    "R13": (39.6, 1.9, 180, "F"),
    # reference, decoupling, power
    "U2": (23.6, 32.0, 90, "F"),
    "C6": (20.0, 31.4, 90, "F"),
    "C5": (27.2, 31.6, 90, "F"),
    "C3": (30.0, 21.5, 0, "F"),
    "C4": (29.6, 25.6, 90, "F"),
    "R5": (29.6, 30.6, 90, "F"),
    "C10": (32.0, 30.6, 90, "F"),
    "R14": (34.4, 30.6, 90, "F"),
    "D3": (36.8, 30.6, 90, "F"),
    "C11": (39.2, 30.6, 90, "F"),
    "H5": (12.5, 35.8, 0, "F"),
    "R15": (17.6, 32.6, 90, "F"),
    # ADC and its front end
    "U3": (37.6, 21.0, 0, "F"),
    "R3": (33.4, 18.6, 0, "F"),
    "C7": (32.0, 25.6, 90, "F"),
    "R4": (34.4, 25.6, 90, "F"),
    "C8": (36.8, 25.6, 90, "F"),
    "C9": (39.2, 25.6, 90, "F"),
    "R10": (34.6, 15.0, 90, "F"),
    "JP2": (39.4, 12.4, 0, "F"),
    "JP3": (39.4, 9.8, 0, "F"),
    "JP4": (39.4, 7.2, 0, "F"),
    "R8": (37.6, 16.8, 0, "F"),
    "R9": (37.6, 14.6, 0, "F"),
    # level shifters, bus pull-ups, connectors
    "Q2": (43.4, 17.6, 180, "F"),
    "Q3": (43.4, 22.0, 180, "F"),
    "R6": (47.6, 17.6, 90, "F"),
    "R7": (47.6, 22.0, 90, "F"),
    "J2": (46.6, 11.0, 90, "F"),
    "J3": (46.6, 28.6, 90, "F"),
    "J4": (19.0, 37.6, 90, "F"),
}

# --------------------------------------------------------------- net classes
NETCLASS = {
    "HiZ": {"nets": ["SUM"], "clearance": 0.5, "track": 0.3},
    "Guard": {"nets": ["GUARD"], "clearance": 0.2, "track": 0.4},
    "Power": {"nets": ["+5V", "+5VA", "+3V3", "GND", "CHASSIS"], "clearance": 0.2, "track": 0.4},
}
DEFAULT_TRACK = 0.25
DEFAULT_CLEARANCE = 0.2

# Guarded region (board coords, mm): polygon used for the guard copper on both
# layers and for the solder-mask opening.  It wraps the BNC centre pin, the
# input trace, the SUM bus up to K1 pin 1, and U1's input end.
GUARD_POLY = [
    (7.0, 18.6), (11.2, 18.6), (11.2, 19.1), (16.05, 19.1), (16.05, 1.8),
    (21.9, 1.8), (21.9, 5.3), (20.75, 5.3), (20.75, 19.1), (24.95, 19.1),
    (24.95, 23.9), (11.2, 23.9), (11.2, 24.4), (7.0, 24.4),
]
# boxes covering GUARD_POLY (used to keep silkscreen off the bare guard copper)
GUARD_BOXES = [(7.0, 18.6, 11.2, 24.4), (11.2, 19.1, 24.95, 23.9), (16.05, 1.8, 20.75, 19.1), (16.05, 1.8, 21.9, 5.3)]

# GUARD stitching vias (inside GUARD_POLY, clear of SUM by > 0.5 mm)
GUARD_VIAS = [(7.6, 19.1), (10.7, 19.1), (7.6, 23.9), (10.7, 23.9), (16.9, 2.6), (16.9, 8.0), (16.9, 13.0),
              (20.1, 7.0), (20.1, 12.2), (20.1, 15.8), (13.5, 20.2), (13.5, 22.9), (22.0, 23.1), (22.0, 19.9)]
# GND stitching vias (filled in after routing)
GND_VIAS = []

# manual reference-designator positions (x, y, angle); "hide" hides the reference on silk
REF_POS = {"C2": (14.9, 10.5, 0), "R1": (14.9, 13.2, 0), "D3": "hide", "JP2": "hide", "JP3": "hide", "JP4": "hide",
           "J1": "hide", "JP5": "hide"}

# silkscreen: (text, x, y, size, angle, justify(-1 left, 0 centre, 1 right), side)
SILK = [
    ("FC-1 charge amp", 1.2, 8.2, 1.0, 0, -1, "F"),
    ("v1.0 2026-11-28", 1.2, 9.6, 0.8, 0, -1, "F"),
    ("powder-doser", 1.2, 10.9, 0.8, 0, -1, "F"),
    ("J1: BNC IN", 1.2, 12.2, 0.8, 0, -1, "F"),
    ("CAN", 14.0, 31.0, 0.9, 0, 0, "F"),
    ("SHELL", 3.3, 31.0, 0.7, 0, 0, "F"),
    ("OUT", 25.6, 18.6, 0.8, 0, 0, "F"),
    ("x10", 24.5, 16.4, 0.8, 0, 0, "F"),
    ("4B", 41.9, 7.2, 0.8, 0, 0, "F"),
    ("4A", 41.9, 9.8, 0.8, 0, 0, "F"),
    ("49", 41.9, 12.4, 0.8, 0, 0, "F"),
    ("ADDR JP2-4", 37.0, 9.8, 0.8, 90, 0, "F"),
    ("RST", 42.4, 4.4, 0.8, 0, 0, "F"),
    ("D3 PWR", 36.8, 33.4, 0.8, 0, 0, "F"),
    ("QT", 42.0, 11.0, 0.8, 90, 0, "F"),
    ("QT", 42.0, 28.6, 0.8, 90, 0, "F"),
    ("GND", 19.0, 35.5, 0.8, 0, 0, "F"),
    ("5V", 21.54, 35.5, 0.8, 0, 0, "F"),
    ("3V3", 24.08, 35.5, 0.8, 0, 0, "F"),
    ("SDA", 26.62, 35.5, 0.8, 0, 0, "F"),
    ("SCL", 29.16, 35.5, 0.8, 0, 0, "F"),
    ("RST", 31.7, 35.5, 0.8, 0, 0, "F"),
    ("FC-1 Faraday-cup charge amplifier", 35.0, 24.6, 0.8, 0, 0, "B"),
    ("v1.0  2026-11-28", 35.0, 26.0, 0.8, 0, 0, "B"),
    ("vertical-cloud-lab/powder-doser", 35.0, 27.4, 0.8, 0, 0, "B"),
    ("ADA4530-1, Cf 10 nF or 110 nF (JP1)", 35.0, 28.8, 0.8, 0, 0, "B"),
    ("ADS1115 0x48, reset = GP10 high", 35.0, 30.2, 0.8, 0, 0, "B"),
    ("Bare guard area: clean with IPA,", 35.0, 31.6, 0.8, 0, 0, "B"),
    ("hold the board by its edges", 35.0, 33.0, 0.8, 0, 0, "B"),
    ("JLCJLCJLCJLC", 35.0, 34.8, 0.8, 0, 0, "B"),
]
