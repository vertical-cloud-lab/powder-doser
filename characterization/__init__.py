"""Blank-auger vibration characterization for the powder doser.

An empty auger is the only configuration on this rig with a known ground
truth: the true mass change is exactly zero, so every gram the balance
reports is artefact.  That makes it the cleanest available measurement of
the noise floor, and the noise floor is what sets the smallest honest
dose, the tolerance band a closed-loop controller can chase, and how long
you must wait per reading.

Modules
-------
``design``     factor grids, randomised interleaving, do-nothing controls
``sweep``      the run harness (raw + stable logging to CSV)
``analyze``    robust statistics, settle curves, RPM bands, calibration
``selfcheck``  short subset run as a gate on entering a new environment
``balance``    balance line-format parsing and serial streaming
``rig``        host client for the firmware REPL ack protocol
``mock``       offline simulator, for dry runs and for testing the analysis
``robust``     stdlib-only median/MAD statistics

See ``characterization/README.md`` for the run book.
"""

__all__ = [
    "analyze", "balance", "design", "firmware_params", "mock", "rig",
    "robust", "selfcheck", "sweep",
]
