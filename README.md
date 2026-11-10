# Universal Robotics Remote

An ESP32-S3 handheld robotics controller combining an ILI9341 touchscreen, microphone, and an intact GH-Wii U002 gamepad. The bench firmware exercises the screen, touch and microphone. Radio control and actuator commands are not implemented.

## Current engineering state

The main PCB survey records **125.5 × 62.5 × 1.15 mm**, with hole A diameter **4.83 mm**. The native FreeCAD r002 document is a **bounding envelope only**: the irregular contour, hole coordinates and component clearances remain unmeasured. Ten metadata-stripped hardware photos and an HTML gallery are under `measurements/photos/gamepad-gh-wii-u002/`. No dimensions are inferred from perspective photos.

- `hardware/`: component and signal registries; `hardware/signals.json` owns GPIO assignments.
- `firmware/`: pinned PlatformIO bench application.
- `electronics/`: proposed harnesses; `cad/`: native sources; `exports/`: derived review files.
- `measurements/`: measured facts and reference photos; `scripts/cad/`: portable photo and board-survey tools.
- `docs/`: engineering decisions, measurement guidance, validation and project plan.

## Getting started

See [current status](STATUS.md), [project plan](docs/PROJECT_PLAN.md), [CAD workflow](docs/ECAD_MCAD.md), and [contribution guide](CONTRIBUTING.md).

```sh
git clone https://github.com/iThinkiKhan/Universal-Robotics-Remote.git
cd Universal-Robotics-Remote
python tools/check_public_content.py
python tools/generate_hardware.py --check
python -m unittest discover -s tests
python -m pip install platformio==6.1.19
python -m platformio run -d firmware -e bench
```

Builds do not establish live hardware compatibility or authorize firmware upload. See [measurement guidance](docs/MEASUREMENTS.md) and [publication boundary](docs/PUBLICATION.md). This repository contains no G-code or device backups, and no enclosure is ready for fabrication.
