# Electrical design record

`harnesses.json` owns the connector plan. `hardware/signals.json` owns GPIO assignments. `tools/generate_hardware.py` reconciles them and generates the firmware header, pin table and WireViz input. The WireViz file uses JSON syntax, a YAML subset; do not edit it independently.

The first diagram is a planning artifact marked NOT FOR ASSEMBLY. J1 numbering, voltage compatibility, mating orientation, pin1, connector part numbers, colors, lengths and gauges remain unresolved. It is not a soldering instruction or purchasing BOM. No gamepad power line is included.

Install WireViz0.4.1 with the dependencies in `wireviz-requirements.lock` and Graphviz, then run from the repository root:

```sh
python tools/generate_hardware.py
python tools/render_harness.py
```

Rendering runs locally and records source/output hashes. PNG/SVG files are under `electronics/generated/`. KiCad schematic/layout work follows the measured interface decision; do not invent black-box pin behavior or PCB dimensions to fill a drawing.
