# Engineering history

## 2026-11-11 — Seven-connector harness drawn and 3D harness model started
The owner chose JST XH connectors from stock (6 positions at most) and an ESP32-DevKitC V4 (WROOM-32U) to read the buttons and report them to the S3 over a UART, so the harness became seven connectors: J1L and J1R to the S3, J2F, J2R, J2D, J2L and J2C to the button processor. The generator now writes a WireViz input per connector and an overview, with pad IDs, wire IDs, housing positions and far-end pins; all eight were rendered with WireViz 0.4.1. Started the 3D harness model (r001): the traced board with 24 tap markers for 28 wires, built and rendered in FreeCAD 1.0.0. By the owner's decision the buttons are confirmed at the first read, not pad by pad. Nothing is wired; the far-end pins are proposals, and colours, gauge, lengths, part numbers and board-side headers are undecided. Ground returns first piled onto one 1.2 mm pad; the owner then reported the large VSS pad is ground, so the left-hand connectors return there and the right-hand ones to the large GND pad.

## 2026-11-11 — Pad table completed and button harness proposed (survey r005)
Added 16 pads to the rear-side table (83 in total): the round button test pads H, K-+, a K-- candidate pair, L-1 and L-2, the T, SYNCO, WP and POW_DET test points, four unlabeled ringed pads and the round M+ and M- motor pads. Re-read labels from zoomed crops of photos 3089 and 3086: the round pads beside the left-stick ribbon are L-3, L-X and L-Y, and the P_EN, MSDA and MSCL attributions beside U3 were revised (still low confidence). Built and rendered FreeCAD r005 (84 solids). Extended the harness proposal with J2A and J2B so that both sticks, their clicks and 15 buttons each land on a free round test pad; added a tap map and a button check sheet. Button functions are inferred from printed labels and are not yet measured; no registry, firmware or wiring change.

## 2026-11-10 — Harness package (proposal)
Assembled what a high-quality harness needs: a connection list tying each important connection to pad IDs from the pad table and to the J1 registry pins (3 plan-ready, 10 blocked, 3 held, 6 retained original assemblies), an ordering list split into 12 buy-now lines, 7 buy-after-decision lines and 3 hold lines, a continuity-test sheet, and a plan listing the owner decisions (D1 to D6) and measurements (M1 to M7) still needed. Connector part numbers and wire ranges for JST GH and Hirose DF13 were checked against distributor and manufacturer datasheets and flagged where unconfirmed. Consistency tests keep the proposal in step with the pad table and registry. No electrical connection was made or approved.

## 2026-11-10 — Test pads (survey r004)
Located and recorded 67 pads on the rear surface in the datum frame: the large power and bus column (GND, B+, VSS, VCC, SDA, SCL, +5V, D+, D-), the right- and left-stick test pads and direction pads, both stick ribbon rows, the SW1 and SW2 shoulder pad groups, the motor pads, the battery connector footprint and other labelled test points. Pads were read off the rectified rear-view photograph and snapped to detected circle centres (about ±0.4 mm), each with a label-confidence flag. Ribbon-row pads are hidden by their ribbons and are placed from the visible pitch. Four round pads beside the left-stick ribbon have no legible label. Built r004 in FreeCAD with the pads as thin solids and verified each after reopening. A labelled pad map supports harness planning.

## 2026-11-10 — Board model r003
Agreed the datum (rear view, bottom-left, battery-connector end) and recorded caliper readings for holes B to F, hole A's Y, and A's X from photographs. Rectified two owner photographs onto a millimetre grid in that datum frame, using the caliper-measured holes as control points (residuals 0.04 to 0.33 mm), and traced the board contour at about ±0.4 mm with four hidden stretches bridged. Built r003 in FreeCAD with the contour and six holes and verified volume and hole count after reopening. A third-party flat scan of the OEM-style board matched the hole spacing to 0.1 mm but its edges differ by up to about 1 mm, so it served only as a private cross-check. Caliper spot-checks of the contour and connector/pad positions remain.

## 2026-11-10 — First live L-X input
The owner selected a direct temporary GPIO5-to-L-X probe with common ground, omitting the proposed resistor and capacitor, and confirmed that the S3 display follows the joystick. The serial diagnostic showed progressing acquisition without ADC errors, a16.937 ms recorded maximum loop and no microphone errors. Sampling was stopped afterward. See measurements/bench/lx-01-direct-20261110.md; this records initial visible response, not a calibrated/full-interface acceptance test.

## 2026-11-10 — Board survey
Recorded W125.5/H62.5/T1.15/A4.83 mm and created native FreeCAD r002 as a measured bounding envelope. Reopened the document and verified geometry and a nonblank preview. Actual contour and hole positions remain pending. Ten hardware photos accompany the survey.

## 2026-11-10 — ECAD/MCAD validation
Validated a synthetic PCB fixture using KiCad10.0.8, FreeCAD1.0.0 and StepUp13.1.7. The 14 integration checks cover model loading, valid solids, datum alignment, STEP round trips, clearances and an intentionally injected collision. Fixture dimensions are not gamepad measurements.

## 2026-11-09 — Bench firmware
Display, touch and microphone checks passed. Incremental rendering/capture resolved reported flicker and freezing; recorded capture maximum loop time improved from22.426 seconds to26.369 ms. Smooth operation was confirmed and a bounded five-minute soak passed. This is not long-term qualification.

## 2026-11-10 — Passive bus probe and next input milestone
The project owner constructed a DIY logic analyzer, reporting no communication on the large `SCL`/`SDA` pads during startup and unsuccessful pairing within the observed window. Capture parameters and raw traces were not supplied; no bus identity or absence can be established. Prior owner voltage sweeps established four ~0–3 V joystick axes and active-low behavior for the sampled button types. Agreed to defer the bus and plan a single-channel S3 joystick observer test after checking off-state backfeed/power sequencing.

## 2026-11-10 — Module measurement sheets
Added a reading template and a guide sheet each for the S3 board, display module and microphone breakout. No dimensions were assumed; the models follow once the readings are taken. The battery and enclosure are not yet defined.

## 2026-11-13 — Enclosure pod concept
Owner chose to keep the original shell and add a printed pod. First space-claim model `cad/enclosure/pod-r001` built and checked (no collisions; several heights assumed). Reading sheet `measurements/templates/pod-readings.csv` lists what the next revision needs.
