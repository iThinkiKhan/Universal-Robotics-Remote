"""Run with native freecadcmd: build the placement study model (gamepad board + DevKitC V4 + straight-line wires).

PROPOSED / NOT FOR ASSEMBLY. XY study at Z = 0: heights are not recorded (M5), so the DevKitC is a zero-thickness board outline lying
in the gamepad's rear plane, pins are small markers and wires are straight lines whose lengths are lower bounds.
From r002 the pose record may also carry an "s3" pose (placed, with its stick wires and the UART link) and "parked" reference bodies for the
display, battery and microphone (sizes from measurements/modules/*-20261112.json; parked outside the gamepad outline, not a layout).

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
             "Limitation": "XY study at Z=0. DevKitC is a zero-thickness outline with pin markers; wires are straight lines (lower bounds). Heights, layers, housings, routing and service loops are not modelled. " + ("The S3 is placed; the display, battery and microphone are parked reference bodies, not a layout." if "s3" in poses[key] else "S3, display, microphone and battery are not placed."),
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

extra = {}
if "s3" in poses[key]:
    def prism(pts, z0, h):
        face = Part.Face(Part.makePolygon([App.Vector(x, y, z0) for x, y in pts] + [App.Vector(pts[0][0], pts[0][1], z0)]))
        return face.extrude(App.Vector(0, 0, h))

    def add_solid(name, label, shape, group, **props):
        o = doc.addObject("Part::Feature", name)
        o.Shape, o.Label = shape, label
        for k, v in props.items():
            o.addProperty("App::PropertyString", k, "Module")
            setattr(o, k, str(v))
        group.addObject(o)
        return o

    s3pose, s3b = poses[key]["s3"], placement.s3_board()
    sg = s3b["geometry"]
    sign = -1.0 if s3pose.get("flip") else 1.0
    s3_group = doc.addObject("App::DocumentObjectGroup", "ESP32_S3")
    s3_group.Label = "ESP32-S3 N16R8 - placed (owner readings 2026-11-12; header order assumed)"
    xy = lambda rect: [placement.to_gamepad(c, s3pose, s3b) for c in rect]
    t = sg["pcb_thickness_mm"]
    mod = sg["module"]
    top = s3b["length"] - mod["top_edge_from_antenna_end_mm"]
    mod_rect = [(mod["u_min"], top - mod["length"]), (mod["u_min"] + mod["width"], top - mod["length"]),
                (mod["u_min"] + mod["width"], top), (mod["u_min"], top)]
    layer = "Layers and heights are not assigned. Drawn from Z=0; heights toward " + ("-Z (board turned over)" if sign < 0 else "+Z")
    add_solid("S3_PCB", "S3 PCB 28 x 57 x 1.55 mm", prism(xy(s3b["rects"]["pcb"]), 0, sign * t), s3_group,
              State="owner_measured", Note=layer)
    add_solid("S3_Module", "S3 module 15.9 x 17.2 mm, top 4.7 mm above PCB underside",
              prism(xy(mod_rect), sign * t, sign * (mod["top_z_from_pcb_underside_mm"] - t)), s3_group,
              State="owner_measured size; top edge approx 0.5 mm from the antenna-end edge", Note=layer)
    ant = xy(s3b["rects"]["antenna"])
    add_solid("S3_Antenna", "S3 antenna overhang 18 x 6.5 mm (flat; thickness not recorded)",
              Part.Face(Part.makePolygon([App.Vector(x, y, 0) for x, y in ant] + [App.Vector(ant[0][0], ant[0][1], 0)])), s3_group,
              State="width and projection owner_measured; centring on the module assumed", Note="Zero thickness")
    uw, ug, u0 = sg["usb"]["width"], sg["usb"]["gap"], sg["usb"]["left_edge_u"]
    for i, (ua, ub) in enumerate(((u0, u0 + uw), (u0 + uw + ug, u0 + 2 * uw + ug))):
        a, b = placement.to_gamepad((ua, 0), s3pose, s3b), placement.to_gamepad((ub, 0), s3pose, s3b)
        o = doc.addObject("Part::Feature", "S3_USB%d_Edge" % (i + 1))
        o.Shape = Part.makeLine(App.Vector(a[0], a[1], 0), App.Vector(b[0], b[1], 0))
        o.Label = "S3 USB connector %d (9 mm wide) at the USB-end edge; body length not recorded, top 4.7 mm" % (i + 1)
        s3_group.addObject(o)
    s3_pin_group = doc.addObject("App::DocumentObjectGroup", "S3_Pins")
    s3_pin_group.Label = "S3 HEADER PINS (44) - markers, order assumed from Espressif DevKitC-1"
    for pn in s3b["pins"]:
        x, y = placement.to_gamepad((pn["u"], pn["v"]), s3pose, s3b)
        o = doc.addObject("Part::Feature", "S3Pin_%s_%02d" % (pn["side"], pn["pos"]))
        o.Shape = Part.makeCylinder(0.5, 0.5, App.Vector(x, y, 0))
        o.Label = "S3 %s-%d %s" % (pn["side"], pn["pos"], pn["name"])
        for name, value in {"PinName": pn["name"], "GPIO": "" if pn["gpio"] is None else str(pn["gpio"]),
                            "State": "assumed order; pitch 2.54 mm is a hypothesis"}.items():
            o.addProperty("App::PropertyString", name, "S3")
            setattr(o, name, value)
        s3_pin_group.addObject(o)
    s3_wire_group = doc.addObject("App::DocumentObjectGroup", "S3_Wires")
    s3_lens = placement.s3_lengths(s3pose, s3b, pose, board, gp)
    s3_wire_group.Label = "WIRES to the S3 (%d) - straight XY lower bounds, not routed" % len(s3_lens)
    by_gpio3 = {pn["gpio"]: pn for pn in s3b["pins"] if pn["gpio"] is not None}
    grounds3 = [pn for pn in s3b["pins"] if pn["name"] == "GND"]
    dk_gpio = {p["gpio"]: p for p in board["pins"] if p["gpio"] is not None}
    for w in s3_lens:
        if w["connector"] == "UART":
            a = placement.to_gamepad((dk_gpio[w["dk_gpio"]]["u"], dk_gpio[w["dk_gpio"]]["v"]), pose, board)
            b = placement.to_gamepad((by_gpio3[w["s3_gpio"]]["u"], by_gpio3[w["s3_gpio"]]["v"]), s3pose, s3b)
            p0, p1, pad_id = App.Vector(a[0], a[1], 0), App.Vector(b[0], b[1], 0), "DevKitC GPIO17"
        else:
            pad = gp["pads"][w["pads"][0]]
            cands = [placement.to_gamepad((pn["u"], pn["v"]), s3pose, s3b) for pn in ([by_gpio3[w["far"]]] if w["far"] != "GND" else grounds3)]
            tgt = min(cands, key=lambda c: math.dist(c, (pad["x"], pad["y"])))
            p0, p1, pad_id = App.Vector(pad["x"], pad["y"], survey_geometry.PAD_HEIGHT_MM), App.Vector(tgt[0], tgt[1], 0), w["pads"][0]
        o = doc.addObject("Part::Feature", "Wire_" + w["wire_id"].replace("-", "_"))
        o.Shape = Part.makeLine(p0, p1)
        o.Label = "%s %s %s -> %s" % (w["wire_id"], w["signal"], pad_id, "S3 GND" if w["far"] == "GND" else "S3 GPIO%s" % w["far"])
        for name, value in {"WireID": w["wire_id"], "Signal": w["signal"], "Pad": pad_id, "FarPin": str(w["far"]),
                            "LengthXYmm": "%.2f" % w["length_mm"], "Settled": "yes",
                            "LowerBound": "Straight XY distance; not a cut length"}.items():
            o.addProperty("App::PropertyString", name, "Wire")
            setattr(o, name, value)
        s3_wire_group.addObject(o)

    parked = poses[key]["parked"]
    pk = doc.addObject("App::DocumentObjectGroup", "ParkedReferences")
    pk.Label = "PARKED REFERENCE BODIES (display, battery, microphone) - sizes only, NOT a layout"
    d = json.loads((project / "measurements/modules/display-physical-20261112.json").read_text(encoding="utf-8"))
    dx, dy = parked["display"]["x"], parked["display"]["y"]
    L, W, T = d["pcb"]["length_mm"]["value"], d["pcb"]["width_mm"]["value"], d["pcb"]["thickness_mm"]["value"]
    sc = d["screen"]
    glass_t = sc["front_to_back_thickness_with_pcb_mm"]["value"] - T
    sd_t = d["full_assembly"]["total_thickness_including_pcb_screen_sd_slot_mm"]["value"] - sc["front_to_back_thickness_with_pcb_mm"]["value"]
    pcb = Part.makeBox(L, W, T, App.Vector(dx, dy, 0))
    for h in d["mounting_holes"]["cad_hole_centers_rear_view_mm"]:
        pcb = pcb.cut(Part.makeCylinder(d["mounting_holes"]["diameter_mm"]["value"] / 2, T, App.Vector(dx + h["x"], dy + h["y"], 0)))
    add_solid("Display_PCB", "Display PCB 86 x 50 x 1.6 mm, 4 holes 3.15 mm (rear view, header right)", pcb, pk,
              State="owner_measured; hole centres derived", Frame="Rear-view datum bottom-left; rear face toward +Z")
    add_solid("Display_Screen", "Display screen 69.25 x 50 mm, 4.0 mm thick on the front (-Z) face",
              Part.makeBox(sc["overall_length_mm"]["value"], W, glass_t, App.Vector(dx + sc["rear_view_bounds_mm"]["x_min"]["value"], dy, -glass_t)), pk,
              State="owner_measured: one visible screen footprint, active area not measured; thickness = 5.6 - 1.6")
    sdd = d["sd_card_slot"]
    add_solid("Display_SDslot", "Display SD slot 28.5 x 16.6 mm, 2.7 mm proud of the PCB rear face",
              Part.makeBox(sdd["reported_width_mm"]["value"], sdd["reported_height_in_plane_mm"]["value"], sd_t,
                           App.Vector(dx + sdd["left_edge_from_left_pcb_edge_mm"]["value"], dy + sdd["bottom_edge_from_bottom_pcb_edge_mm"]["value"], T)), pk,
              State="size owner_measured; 2.7 mm = 8.3 - 5.6 derived; rear-face assumption pending")
    comps = json.loads((project / "hardware/components.json").read_text(encoding="utf-8"))
    comps = comps["components"] if isinstance(comps, dict) else comps
    battery = [c for c in comps if c["id"] == "BAT2"][0]["dimensions_mm"]
    add_solid("Battery_Envelope", "Battery MakerFocus 103665 envelope 65 x 36 x 10 mm (nominal)",
              Part.makeBox(battery[0], battery[1], battery[2], App.Vector(parked["battery"]["x"], parked["battery"]["y"], 0)), pk,
              State="owner-reported nominal size from another project; not measured from a pack in hand")
    m = json.loads((project / "measurements/modules/mic-physical-20261112.json").read_text(encoding="utf-8"))
    r, mt = m["pcb"]["diameter_mm"]["value"] / 2, m["pcb"]["bare_thickness_mm"]["value"]
    mc = App.Vector(parked["mic"]["cx"], parked["mic"]["cy"], 0)
    mic = Part.makeCylinder(r, mt, mc)
    nw, nd = m["notches"]["width_mm"]["value"], m["notches"]["inset_depth_mm"]["value"]
    mic = mic.cut(Part.makeBox(nw, nd + 1, mt, App.Vector(mc.x - nw / 2, mc.y + r - nd, 0)))
    mic = mic.cut(Part.makeBox(nw, nd + 1, mt, App.Vector(mc.x - nw / 2, mc.y - r - 1, 0)))
    add_solid("Mic_PCB", "Microphone PCB diameter 14 mm, 1.15 mm, two 2 x 2 mm notches", mic, pk,
              State="owner_measured; pins, sound port diameter and Z protrusions not recorded")
    s3_polys = placement.s3_footprint(s3pose, s3b)
    extra = {"s3_pose": s3pose, "s3_wires": len(s3_lens), "s3_total_xy_mm": round(sum(w["length_mm"] for w in s3_lens), 2),
             "s3_longest_xy_mm": round(max(w["length_mm"] for w in s3_lens), 2),
             "s3_by_wire_xy_mm": {w["wire_id"]: round(w["length_mm"], 2) for w in s3_lens},
             "s3_overlaps_devkitc_in_xy": any(placement.convex_overlap(q, placement.corners(pose, board)) for q in s3_polys),
             "s3_inside_gamepad_bbox_margin_2mm": all(gp["bbox"][0] + 2 <= x <= gp["bbox"][2] - 2 and gp["bbox"][1] + 2 <= yy <= gp["bbox"][3] - 2
                                                       for q in s3_polys for x, yy in q),
             "display_pcb_volume_mm3": round(pcb.Volume, 1), "mic_pcb_volume_mm3": round(mic.Volume, 1)}
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
expected_wires = sum(len(w["pads"]) for w in lens) + (extra.get("s3_wires", 0))
if n_pins != 38 or n_wire_objects != expected_wires or not shapes_ok or abs(area - board["width"] * board["length"]) > 1e-6:
    raise RuntimeError("The placement model did not survive saving")
by_connector = {}
for w in lens:
    by_connector[w["connector"]] = round(by_connector.get(w["connector"], 0) + w["length_mm"], 2)
report = {"file": output.relative_to(project).as_posix(), "revision": revision, "state": "proposed_xy_study", "native_reopened": True,
          "pose": pose, "devkitc_pins": n_pins, "wires": len(lens), "wire_objects": n_wire_objects,
          "total_length_xy_mm": round(sum(w["length_mm"] for w in lens), 2), "longest_xy_mm": round(max(w["length_mm"] for w in lens), 2),
          "by_connector_xy_mm": by_connector, "devkitc_area_mm2": round(area, 3),
          "not_modelled": ["layers and Z placement", "WROOM-32U module and DevKitC components", "connector housings", "routing and service loops",
                           "enclosure"] + (["display, battery and microphone placement (parked bodies only)", "S3 USB connector bodies, headers and underside parts"] if extra else ["S3, display, microphone, battery"]),
          "lengths_are": "straight-line XY lower bounds, not cut lengths", **extra}
(output.parent / (output.stem + "-validation.json")).write_text(json.dumps(report, indent=2) + "\n")
print(json.dumps(report, indent=2))
