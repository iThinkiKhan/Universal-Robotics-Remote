# Mechanical work awaits measurements

Place measured native CAD source here once board outlines, hole centers, joystick heights/travel, ribbon reach, battery dimensions and connector orientation are available. Use measurements/electrical.csv and reference photos as evidence. Derived STEP and review images belong under exports/.

`harness/` holds the 3D harness model. Revision 1 (`scripts/cad/build_harness_model.py`, rendered by `render_harness_model.py`) copies the surveyed board and puts a marker on every pad the proposed harness lands on, with the wire IDs as properties. Markers are not wire geometry and their colours identify the connector, not the wire. Wires, housings and the other modules are added once those modules are measured and placed.

Do not use estimated photo dimensions to claim a fit. No enclosure or printable model has been created in this initial electrical/firmware preparation pass.

`assembly/` holds placement studies (`scripts/cad/build_placement_model.py`, maths in `placement.py`). Revision 1 puts the DevKitC V4 outline, its 38 header pins and straight-line wires to it against the surveyed gamepad board; it is an XY study at Z = 0 and its lengths are lower bounds. Revision 2 adds the S3 (28 x 57 mm, owner readings 2026-11-12, header order assumed) with its stick wires and UART link, plus the display, battery and microphone as parked reference bodies; the S3 and DevKitC overlap in XY because they cannot share one layer.

`enclosure/` holds enclosure studies. `pod-r001` (`scripts/cad/build_pod_model.py`, checks and views in `pod_layout.py`, record `enclosure/pod-r001.json`) is a concept space claim, not a printable part: a 116.8 x 72.8 x 38.8 mm box for the display, both ESP boards, the battery, charger, regulator, switch and microphone, with the gamepad left whole in its original shell. Module heights for the DevKitC, charger, regulator and switch are assumptions, and nothing of the original shell is measured, so there is no mount. The record lists the state of every size.
