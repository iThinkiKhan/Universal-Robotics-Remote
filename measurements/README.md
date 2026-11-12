# Measurements

`electrical.csv` contains the electrical readings and remaining initial battery/module placeholders. `boards/` owns main-PCB mechanical measurements; `photos/` holds original archives and galleries. Record instrument, power state, reference datum, date and evidence. Unknown values remain blank/null. See ../docs/MEASUREMENTS.md and ../docs/BOARD_SURVEY_WORKFLOW.md.

The main gamepad record is boards/gamepad-gh-wii-u002.json; its first four readings are described in boards/gamepad-gh-wii-u002-FIRST_READINGS.md. Earlier pending DIM01–03 envelope rows were moved out of electrical.csv so these values have one authority.

`boards/gamepad-gh-wii-u002-pads.csv` holds the traced test pads (centre, footprint, printed label and how confident that label is) and is referenced from the board record. `boards/gamepad-gh-wii-u002-features.csv` lists the connectors, pad groups, switches, contacts and separate modules still to be located, all pending until measured; hole positions go in the board JSON instead. The recording format is in ../docs/ECAD_MCAD.md.

`templates/module-readings.csv` and the three sheets in `templates/modules/` (S3 board, display module, microphone breakout) list the caliper readings needed to model those parts. Each part has its own datum (bottom-left of its PCB rectangle in a stated view); values stay blank until measured, and published sizes for these generic modules vary by vendor, so none are assumed. Tier 1 readings place a module in an assembly; tier 2 route the harness.

For MCAD, add measured board outlines, hole centers, thickness, component heights, joystick travel and cable reach here before using them in native CAD. Synthetic toolchain fixtures under cad/toolchain-smoke are not hardware measurements.

## ESP32-S3 physical measurements (2026-11-12)

`modules/esp32-s3-physical-20261112.json` records the owner's S3 N16R8 board dimensions, dual USB connector/antenna/module heights, LED and header measurements, and an explicit 20 mm assembly clearance allowance. It distinguishes reported readings from derived dimensions, approximations and still-missing coordinates. **The USB-end/antenna-end view differs from the blank S3 template sketch; reconcile the datum before placing features in CAD.** The template remains blank by design and is not the live measurement ledger.
