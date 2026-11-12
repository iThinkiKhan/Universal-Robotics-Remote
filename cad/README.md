# Mechanical work awaits measurements

Place measured native CAD source here once board outlines, hole centers, joystick heights/travel, ribbon reach, battery dimensions and connector orientation are available. Use measurements/electrical.csv and reference photos as evidence. Derived STEP and review images belong under exports/.

`harness/` holds the 3D harness model. Revision 1 (`scripts/cad/build_harness_model.py`, rendered by `render_harness_model.py`) copies the surveyed board and puts a marker on every pad the proposed harness lands on, with the wire IDs as properties. Markers are not wire geometry and their colours identify the connector, not the wire. Wires, housings and the other modules are added once those modules are measured and placed.

Do not use estimated photo dimensions to claim a fit. No enclosure or printable model has been created in this initial electrical/firmware preparation pass.

`assembly/` holds placement studies (`scripts/cad/build_placement_model.py`, maths in `placement.py`). Revision 1 puts the DevKitC V4 outline, its 38 header pins and straight-line wires to it against the surveyed gamepad board; it is an XY study at Z = 0 and its lengths are lower bounds.
