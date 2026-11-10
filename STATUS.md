# Project status — 2026-11-10

- Bench firmware 0.1.1 exercises display, touch and microphone on ESP32-S3, with 16 MB flash and 8 MB PSRAM. The corrected interface was confirmed smooth and responsive. Radio and actuator control remain unimplemented.
- Main PCB readings: width125.5 mm, height62.5 mm, thickness1.15 mm, hole A diameter4.83 mm. These are owner-reported measurements; instrument and uncertainty were not supplied. The canonical record is `measurements/boards/gamepad-gh-wii-u002.json`.
- Native FreeCAD r002 contains a rectangular bounding envelope only, top Z0, volume9020.3125 mm³, no hole cuts. Actual contour, hole positions and component clearances remain unmeasured. Loose daughterboards have independent mounting positions.
- Ten hardware photos, a gallery and a measurement guide are available under `measurements/photos/gamepad-gh-wii-u002/`. Perspective photos establish identity/layout, not scale.
- The synthetic toolchain fixture is separate from controller geometry. See `cad/toolchain-smoke/` and `exports/toolchain-smoke/`.

Next mechanical work: agree a physical datum; measure the contour, hole centers, component heights, USB overhang and ribbon routing. Next electrical work: characterize operating rails, joystick ranges, button interfaces and shutdown/backfeed behavior before connecting proposed inputs. See the open issues and docs/PROJECT_PLAN.md.
