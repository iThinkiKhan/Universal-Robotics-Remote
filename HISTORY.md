# Engineering history

## 2026-11-10 — Board survey
Recorded W125.5/H62.5/T1.15/A4.83 mm and created native FreeCAD r002 as a measured bounding envelope. Reopened the document and verified geometry and a nonblank preview. Actual contour and hole positions remain pending. Ten hardware photos accompany the survey.

## 2026-11-10 — ECAD/MCAD validation
Validated a synthetic PCB fixture using KiCad10.0.8, FreeCAD1.0.0 and StepUp13.1.7. The 14 integration checks cover model loading, valid solids, datum alignment, STEP round trips, clearances and an intentionally injected collision. Fixture dimensions are not gamepad measurements.

## 2026-11-09 — Bench firmware
Display, touch and microphone checks passed. Incremental rendering/capture resolved reported flicker and freezing; recorded capture maximum loop time improved from22.426 seconds to26.369 ms. Smooth operation was confirmed and a bounded five-minute soak passed. This is not long-term qualification.

## 2026-11-10 — Passive bus probe and next input milestone
The project owner constructed a DIY logic analyzer, reporting no communication on the large `SCL`/`SDA` pads during startup and unsuccessful pairing within the observed window. Capture parameters and raw traces were not supplied; no bus identity or absence can be established. Prior owner voltage sweeps established four ~0–3 V joystick axes and active-low behavior for the sampled button types. Agreed to defer the bus and plan a single-channel S3 joystick observer test after checking off-state backfeed/power sequencing.
