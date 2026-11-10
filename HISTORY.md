# Engineering history

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
