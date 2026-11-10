# ECAD/MCAD workflow

Native CAD lives under `cad/`; derived STEP files, drawings and review images live under `exports/`. Record units, datum, source revision and validation with every deliverable. Measured records live under `measurements/`; electrical mappings live under `hardware/` and `electronics/`.

## Board survey

Open `cad/boards/gamepad-gh-wii-u002/gamepad-gh-wii-u002-survey-r002.FCStd` in FreeCAD. It contains ten photo references and the measured W/H/T bounding envelope. The irregular contour and hole positions remain unknown. It is not an enclosure or a fabrication model.

### Recording the outline, holes and datum

The builder turns measured geometry into a native body, but only from entries marked `measured`. Nothing is defaulted, and an inconsistent record stops the build with a message rather than producing a plausible-looking model (`scripts/cad/survey_geometry.py`, covered by `tests/test_survey_geometry.py`).

1. **Name the datum first.** Set `origin_description` in `measurements/boards/<board>.json`; coordinates are rejected while it is blank. For the GH-Wii U002 the project owner chose (2026-11-10) the bottom-left corner of the board's bounding rectangle in the **rear (component-side) view with USB at the top**, the battery-connector end of the bottom edge: X right, Y up toward USB, rear surface at Z=0, millimetres. The front view (photo 3081) is its mirror image and sees that corner at the bottom-right, so measure from the rear or convert deliberately.
2. **Outline.** `outline.state` = `measured` and `outline.points_mm` = start point `[x, y]`, then `[x, y]` for each straight segment or `{"to": [x, y], "via": [x, y]}` for a circular arc through a measured mid-point. The contour closes back to the start. The traced span must agree with the measured W and H within 0.5 mm.
3. **Holes.** Add to `mounting_holes` either the centre, `{"id": "A", "x_mm": ..., "y_mm": ..., "diameter_mm": ..., "state": "measured"}`, or the raw caliper readings to the near wall, `"x_near_mm"` and `"y_near_mm"` (datum edge to the hole's left / lower wall; the builder adds half the hole's size). Keep the raw readings when that is what was measured. Slots add `slot_length_mm` (overall) and optional `angle_deg` (0 or 90 with near-wall readings). A hole with only one axis known stays `"state": "partial"` and is listed but not built. Until the contour is measured, located holes are cut into the W x H rectangle and the body is labelled "envelope with holes", never as the board outline. A hole `id` with no `diameter_mm` takes the measured reading of the same id (hole A). `measurements/photos/<board>/hole-map-3089.svg` labels the visible holes in the datum (rear) view, and `hole-map-3081.svg` shows the same letters mirrored from the front; both are identification aids with no scale. A hole that breaks the outline edge belongs in the outline as a notch.
4. **Connectors, pad groups, switches and modules** live in `measurements/boards/<board>-features.csv`. Rows stay `pending` with blank numbers until measured, with instrument and date.
5. Increment the survey `revision`, run `build_board_survey.py` (checks volume, thickness and hole count after reopening the saved file), then `render_board_survey.py` for the axonometric and top review images.

A traced or scanned outline is acceptable if the method, scale reference and uncertainty are recorded and a few points are spot-checked with calipers. Do not take scale from handheld or perspective photographs.

Portable tools under `scripts/cad/` support other boards too:

- `photo_archive.py`: import photographs and create a hash manifest/gallery. It preserves original bytes; remove identifying metadata from public copies before committing and update their hashes.
- `board_survey.py`: create a board-specific survey with unknown readings left blank. It requires an existing project README and an archived photo manifest and refuses to overwrite a survey.
- `build_board_survey.py`: run with FreeCAD's Python runtime to build a revisioned native document. Without measured dimensions it creates metadata/photo references; measured W/H/T creates only a labeled envelope. It refuses an existing output revision.
- `render_board_survey.py`: run in an isolated FreeCAD GUI session to produce a review image and reopen validation. The session closes when finished; do not run it in a session containing unsaved work.

Example survey initialization from the repository root:

```sh
python scripts/cad/board_survey.py --project . --board another-board \
  --name "Another board" --photos measurements/photos/another-board \
  --reference-photo reference.jpg
```

The photo folder must already contain a manifest created with `photo_archive.py`. Run either tool with `--help` for its arguments. The build script takes `ECAD_SURVEY_PROJECT` as an absolute project root and `ECAD_SURVEY_RECORD` as a project-relative JSON path. The render script uses the same project variable plus `ECAD_SURVEY_MODEL` as a project-relative native document path. Use a new survey revision when measured data changes; preserve prior records.

## ECAD/MCAD exchange

The synthetic fixture was checked with KiCad10.0.8, FreeCAD1.0.0 and StepUp13.1.7. Load an actual `.kicad_pcb` through StepUp to bring board outline, drills and available component models into FreeCAD. Agree KiCad grid/aux origin and the MCAD datum before combining geometry. The tested fixture maps KiCad Y to MCAD -Y and uses board top Z0; the physical controller datum remains unmeasured.

Native KiCad STEP and StepUp used different Z frames in this fixture. The CLI exported a1.51 mm dielectric core and placed the reference model1.595 mm above StepUp's1.6 mm envelope/top frame. This is a fixture-specific observation. Verify each board's origin, thickness and model placement independently. StepUp writeback has not been exercised on the unknown gamepad geometry.

`cad/toolchain-smoke/` and `exports/toolchain-smoke/` contain the synthetic50×30×1.6 mm fixture, native review document, STEP files and validation results. The blue test block is clear by3 mm; the red block deliberately intersects the PCB by16 mm³. These are software tests, not gamepad geometry. See THIRD_PARTY.md for reference-model provenance.

See [KiCad CLI](https://docs.kicad.org/10.0/en/cli/cli.html) and [StepUp](https://github.com/easyw/kicadStepUpMod) for application setup. Host configuration and deployment are maintained separately from this project.
