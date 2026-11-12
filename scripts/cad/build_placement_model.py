"""Run with native freecadcmd: build the placement study model (gamepad board + DevKitC V4 + straight-line wires).

PROPOSED / NOT FOR ASSEMBLY. XY study at Z = 0: heights are not recorded (M5), so the DevKitC is a zero-thickness board outline lying
in the gamepad's rear plane, pins are small markers and wires are straight lines whose lengths are lower bounds. The S3, display,
microphone and battery are not placed because their sizes are not recorded.

Environment: ECAD_SURVEY_PROJECT (absolute project root), ECAD_PLACEMENT_REVISION (integer).
The pose is read from cad/assembly/placement-poses.json, key "r<NNN>".
"""
import json
import math
import os
import sys
from pathlib import Path
import FreeCAD as App
import Part

sys.path.insert(0, str(Path(os.environ.get("ECAD_SURVEY_SCRIPTS", Path(__file__).resolve().parent))))
import placement
import survey_geometry

project = Path(os.environ["ECAD_SURVEY_PROJECT"]).resolve()
revision = int(os.environ["ECAD_PLACEMENT_REVISION"])
key = f"r{revision:03d}"
poses = json.loads((project / "cad/assembly/placement-poses.json").read_text(encoding="utf-8"))
if key not in poses:
    raise RuntimeError("No pose recorded for " + key)
pose = poses[key]["devkitc"]
survey = json.loads((project / "measurements/boards/gamepad-gh-wii-u002.json").read_text(encoding="utf-8"))
source = project / "cad/boards" / survey["board_id"] / f"{survey['board_id']}-survey-r{survey['revision']:03d}.FCStd"
output = project / "cad/assembly" / f"placement-r{revision:03d}.FCStd"
if output.exists():
    raise RuntimeError("Existing placement model preserved. Increment the revision for a new snapshot.")
if not source.is_file():
    raise RuntimeError("Build the board survey first: " + source.relative_to(project).as_posix())

board = placement.devkit()
gp = placement.gamepad_data()
wires = placement.button_wires()
lens = placement.lengths(pose, board, gp, wires)

src = App.openDocument(str(source))
body = src.getObject("MeasuredBoardBody")
if body is None:
    raise RuntimeError("The board survey has no measured or traced board body")
body_shape, body_label = body.Shape.copy(), body.Label
pad_shapes = {o.PadId: (o.Shape.copy(), o.Label) for o in src.Objects if o.Name.startswith("Pad_")}
App.closeDocument(src.Name)

doc = App.newDocument("PlacementModel")
doc.Label = f"Placement study {key} — PROPOSED, NOT FOR ASSEMBLY"
rec = doc.addObject("App::FeaturePython", "PlacementRecord")
for k, v in {"State": "proposed — NOT FOR ASSEMBLY",
             "Frame": "Gamepad survey datum: rear surface Z=0, X right, Y up toward USB, +Z away from the rear surface",
             "Pose": json.dumps(pose), "PoseNote": poses[key].get("note", ""),
             "Limitation": "XY study at Z=0. DevKitC is a zero-thickness outline with pin markers; wires are straight lines (lower bounds). Heights, housings, routing and service loops are not modelled; S3, display, microphone and battery are not placed.",
             "DevKitCSource": "hardware/devkitc-v4-header.json (Espressif DevKitC V4 dimensions drawing and header tables)"}.items():
    rec.addProperty("App::PropertyString", k, "Placement")
    setattr(rec, k, v)

gb = doc.addObject("Part::Feature", "MeasuredBoardBody")
gb.Label, gb.Shape = body_label, body_shape
pad_group = doc.addObject("App::DocumentObjectGroup", "TestPads")
pad_group.Label = f"TEST PADS ({len(pad_shapes)}) — copied from the board survey"
for pid in sorted(pad_shapes):
    o = doc.addObject("Part::Feature", "Pad_" + pid)
    o.Shape, o.Label = pad_shapes[pid][0], pad_shapes[pid][1]
    o.addProperty("App::PropertyString", "PadId")
    o.PadId = pid
    pad_group.addObject(o)

corners = [App.Vector(x, y, 0) for x, y in placement.corners(pose, board)]
dk = doc.addObject("Part::Feature", "DevKitC_Outline")
dk.Shape = Part.Face(Part.makePolygon(corners + [corners[0]]))
dk.Label = "ESP32-DevKitC V4 outline 27.94 x 48.26 mm (zero thickness; WROOM-32U not drawn)"
pin_group = doc.addObject("App::DocumentObjectGroup", "DevKitC_Pins")
pin_group.Label = "DEVKITC HEADER PINS (38) — markers"
pin_pos = {}
for p in board["pins"]:
    x, y = placement.to_gamepad((p["u"], p["v"]), pose, board)
    pin_pos[(p["side"], p["pos"])] = (x, y)
    o = doc.addObject("Part::Feature", f"Pin_{p['side']}_{p['pos']:02d}")
    o.Shape = Part.makeCylinder(0.5, 0.5, App.Vector(x, y, 0))
    o.Label = f"{p['side']}-{p['pos']} {p['name']}" + (f" (GPIO{p['gpio']})" if p["gpio"] is not None else "")
    for name, value in {"Header": p["side"], "Position": str(p["pos"]), "PinName": p["name"],
                        "GPIO": "" if p["gpio"] is None else str(p["gpio"]), "MarkerOnly": "Marker, not pin geometry"}.items():
        o.addProperty("App::PropertyString", name, "DevKitC")
        setattr(o, name, value)
    pin_group.addObject(o)

by_gpio = {p["gpio"]: p for p in board["pins"] if p["gpio"] is not None}
grounds = [p for p in board["pins"] if p["name"] == "GND"]
wire_group = doc.addObject("App::DocumentObjectGroup", "Wires")
wire_group.Label = f"WIRES to the DevKitC ({len(lens)}) — straight XY lower bounds, not routed"
for w in lens:
    pins = [by_gpio[w["far"]]] if w["far"] != "GND" else grounds
    for pid in w["pads"]:
        pad = gp["pads"][pid]
        target = min((placement.to_gamepad((p["u"], p["v"]), pose, board) for p in pins),
                     key=lambda c: math.dist(c, (pad["x"], pad["y"])))
        o = doc.addObject("Part::Feature", "Wire_" + w["wire_id"].replace("-", "_") + ("_" + pid if len(w["pads"]) > 1 else ""))
        o.Shape = Part.makeLine(App.Vector(pad["x"], pad["y"], survey_geometry.PAD_HEIGHT_MM), App.Vector(target[0], target[1], 0))
        o.Label = f"{w['wire_id']} {w['signal']} {pid} -> " + ("GND" if w["far"] == "GND" else f"GPIO{w['far']}")
        for name, value in {"WireID": w["wire_id"], "Signal": w["signal"], "Pad": pid, "FarPin": str(w["far"]),
                            "LengthXYmm": f"{math.dist((pad['x'], pad['y']), target):.2f}",
                            "Settled": "yes" if len(w["pads"]) == 1 else "no: candidate pad (the longer candidate sets the length)",
                            "LowerBound": "Straight XY distance; not a cut length"}.items():
            o.addProperty("App::PropertyString", name, "Wire")
            setattr(o, name, value)
        wire_group.addObject(o)
doc.recompute()
output.parent.mkdir(parents=True, exist_ok=True)
doc.saveAs(str(output))
App.closeDocument(doc.Name)

check = App.openDocument(str(output))
n_wire_objects = sum(1 for o in check.Objects if o.Name.startswith("Wire_"))
n_pins = sum(1 for o in check.Objects if o.Name.startswith("Pin_"))
face = check.getObject("DevKitC_Outline").Shape
total = sum(float(o.LengthXYmm) for o in check.Objects if o.Name.startswith("Wire_"))
shapes_ok = all(o.Shape.isValid() and not o.Shape.isNull() for o in check.Objects if o.TypeId == "Part::Feature")
area = face.Area
App.closeDocument(check.Name)
expected_wires = sum(len(w["pads"]) for w in lens)
if n_pins != 38 or n_wire_objects != expected_wires or not shapes_ok or abs(area - board["width"] * board["length"]) > 1e-6:
    raise RuntimeError("The placement model did not survive saving")
by_connector = {}
for w in lens:
    by_connector[w["connector"]] = round(by_connector.get(w["connector"], 0) + w["length_mm"], 2)
report = {"file": output.relative_to(project).as_posix(), "revision": revision, "state": "proposed_xy_study", "native_reopened": True,
          "pose": pose, "devkitc_pins": n_pins, "wires": len(lens), "wire_objects": n_wire_objects,
          "total_length_xy_mm": round(sum(w["length_mm"] for w in lens), 2), "longest_xy_mm": round(max(w["length_mm"] for w in lens), 2),
          "by_connector_xy_mm": by_connector, "devkitc_area_mm2": round(area, 3),
          "not_modelled": ["heights and Z placement", "WROOM-32U module and DevKitC components", "connector housings", "routing and service loops",
                           "S3, display, microphone, battery, enclosure"],
          "lengths_are": "straight-line XY lower bounds, not cut lengths"}
(output.parent / (output.stem + "-validation.json")).write_text(json.dumps(report, indent=2) + "\n")
print(json.dumps(report, indent=2))
