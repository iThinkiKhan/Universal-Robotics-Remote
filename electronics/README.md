# Electrical design record

`harnesses.json` owns the connector plan. `hardware/signals.json` owns GPIO assignments. `tools/generate_hardware.py` reconciles them and generates the firmware header, pin table, one WireViz input per connector and an overview of all of them. Pad IDs and held positions come from `harness-sources-proposed.csv`. The WireViz files use JSON syntax, a YAML subset; do not edit them independently.

The diagrams (one per signal connector: J1L, J1R, J2F, J2R, J2D, J2L, J2C, plus `overview-proposed`) are planning artifacts marked NOT FOR ASSEMBLY. Each shows the gamepad test pads, the solder tails with their wire IDs, the JST XH housing, an undecided board-side link and the far-end pins; a far-end pin that is not assigned says so. Connector numbering, voltage compatibility, mating orientation, pin1, connector part numbers, colors, lengths and gauges remain unresolved. It is not a soldering instruction or purchasing BOM. No gamepad power line is included.

Install WireViz0.4.1 with the dependencies in `wireviz-requirements.lock` and Graphviz, then run from the repository root:

```sh
python tools/generate_hardware.py
python tools/render_harness.py
```

Rendering runs locally and records source/output hashes. PNG/SVG files are under `electronics/generated/`. KiCad schematic/layout work follows the measured interface decision; do not invent black-box pin behavior or PCB dimensions to fill a drawing.

`tools/harness_netlist.py` builds the end-to-end netlist (gamepad pad, tail wire, XH pin, far-end pin) from the records into `netlist-proposed.csv`; `--check` verifies it is current. `tools/button_link.py` is a reference model of the proposed WROOM-to-S3 button link (packet format, timeout, gamepad-off rule), exercised by `tests/test_virtual_harness.py`. Both are virtual: nothing is flashed or wired.
