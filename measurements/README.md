# Measurements

`electrical.csv` contains the electrical readings and remaining initial battery/module placeholders. `boards/` owns main-PCB mechanical measurements; `photos/` holds original archives and galleries. Record instrument, power state, reference datum, date and evidence. Unknown values remain blank/null. See ../docs/MEASUREMENTS.md and ../docs/BOARD_SURVEY_WORKFLOW.md.

The main gamepad record is boards/gamepad-gh-wii-u002.json; its first four readings are described in boards/gamepad-gh-wii-u002-FIRST_READINGS.md. Earlier pending DIM01–03 envelope rows were moved out of electrical.csv so these values have one authority.

`boards/gamepad-gh-wii-u002-pads.csv` holds the traced test pads (centre, footprint, printed label and how confident that label is) and is referenced from the board record. `boards/gamepad-gh-wii-u002-features.csv` lists the connectors, pad groups, switches, contacts and separate modules still to be located, all pending until measured; hole positions go in the board JSON instead. The recording format is in ../docs/ECAD_MCAD.md.

For MCAD, add measured board outlines, hole centers, thickness, component heights, joystick travel and cable reach here before using them in native CAD. Synthetic toolchain fixtures under cad/toolchain-smoke are not hardware measurements.
