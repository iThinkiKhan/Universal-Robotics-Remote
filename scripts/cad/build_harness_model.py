"""Run with native freecadcmd: start the 3D harness model.

Revision 1 holds the surveyed board (copied from its native survey document) and one tap marker on every
pad the proposed harness lands on, carrying the wire IDs. Markers are not wire geometry: wire type, colour,
gauge, length and route are not decided, and no module other than the gamepad board is placed yet.
"""
import json
import os
import sys
from pathlib import Path
import FreeCAD as App
import Part

sys.path.insert(0,str(Path(os.environ.get("ECAD_SURVEY_SCRIPTS",Path(__file__).resolve().parent))))
import harness_taps
import survey_geometry

MARKER_RADIUS_MM=0.3
MARKER_HEIGHT_MM=4.0
project=Path(os.environ["ECAD_SURVEY_PROJECT"]).resolve()
survey_path=project/os.environ["ECAD_SURVEY_RECORD"]
revision=int(os.environ["ECAD_HARNESS_REVISION"])
survey=json.loads(survey_path.read_text(encoding="utf-8"))
board_id=survey["board_id"]
source=project/"cad/boards"/board_id/f"{board_id}-survey-r{survey['revision']:03d}.FCStd"
output=project/"cad/harness"/f"gamepad-harness-r{revision:03d}.FCStd"
if output.exists():
    raise RuntimeError("Existing harness model preserved. Increment the harness revision for a new snapshot.")
if not source.is_file():
    raise RuntimeError("Build the board survey first: "+source.relative_to(project).as_posix())
pads={p["id"]:p for p in survey_geometry.load_pads(project/survey["pads_file"])}
taps,wires=harness_taps.collect(project)
for tap in taps:
    if tap["pad"] not in pads: raise ValueError("Connection list names a pad that is not in the pad table: "+tap["pad"])

src=App.openDocument(str(source))
body=src.getObject("MeasuredBoardBody")
if body is None: raise RuntimeError("The board survey has no measured or traced board body")
board_shape=body.Shape.copy(); board_label=body.Label
pad_shapes={o.PadId:(o.Shape.copy(),o.Label) for o in src.Objects if o.Name.startswith("Pad_")}
App.closeDocument(src.Name)

doc=App.newDocument("HarnessModel")
doc.Label=f"Gamepad harness model r{revision:03d} — PROPOSED, NOT FOR ASSEMBLY"
record=doc.addObject("App::FeaturePython","HarnessRecord")
for key,value in {"State":"proposed — NOT FOR ASSEMBLY","BoardSurvey":source.relative_to(project).as_posix(),
                  "BoardSurveySHA256":harness_taps.hashlib.sha256(source.read_bytes()).hexdigest(),
                  "ConnectionList":harness_taps.SOURCES,"ConnectionListSHA256":harness_taps.lf_sha256(project/harness_taps.SOURCES),
                  "HarnessRegistry":harness_taps.REGISTRY,"HarnessRegistrySHA256":harness_taps.lf_sha256(project/harness_taps.REGISTRY),
                  "Frame":"Board datum frame: rear (component) surface at Z=0, X right, Y up toward USB, +Z away from the rear surface",
                  "Limitation":"Tap markers only. No wire, connector housing or module geometry; wire type, colour, gauge, length and route are not decided. Marker colours identify the connector and are not wire colours."}.items():
    record.addProperty("App::PropertyString",key,"Harness");setattr(record,key,value)
board=doc.addObject("Part::Feature","MeasuredBoardBody")
board.Label=board_label; board.Shape=board_shape
pad_group=doc.addObject("App::DocumentObjectGroup","TestPads")
pad_group.Label=f"TEST PADS ({len(pad_shapes)}) — copied from the board survey"
for pid in sorted(pad_shapes):
    obj=doc.addObject("Part::Feature","Pad_"+pid); obj.Shape=pad_shapes[pid][0]; obj.Label=pad_shapes[pid][1]
    obj.addProperty("App::PropertyString","PadId"); obj.PadId=pid
    pad_group.addObject(obj)
groups={}
for tap in taps:
    key=tap["connectors"][0] if len(tap["connectors"])==1 else "SHARED"
    if key not in groups:
        groups[key]=doc.addObject("App::DocumentObjectGroup","Taps_"+key)
        groups[key].Label=("TAPS "+key) if key!="SHARED" else "TAPS shared by several connectors (ground returns)"
    p=pads[tap["pad"]]
    obj=doc.addObject("Part::Feature","Tap_"+tap["pad"])
    obj.Shape=Part.makeCylinder(MARKER_RADIUS_MM,MARKER_HEIGHT_MM,App.Vector(p["x"],p["y"],survey_geometry.PAD_HEIGHT_MM))
    obj.Label=tap["pad"]+" ← "+", ".join(w["wire_id"]+("?" if w["candidate"] else "") for w in tap["wires"])
    for name,value in {"PadId":tap["pad"],"PadLabel":p["label"],"WireIDs":"; ".join(w["wire_id"] for w in tap["wires"]),
                       "Signals":"; ".join(w["signal"] for w in tap["wires"]),"Connectors":"; ".join(tap["connectors"]),
                       "FarEnds":"; ".join(sorted({w["far_end"] for w in tap["wires"]})),
                       "Settled":"yes" if tap["settled"] else "no: candidate pad, the wire lands on one of its candidates",
                       "MarkerRGB":",".join(f"{c:.2f}" for c in tap["rgb"]),
                       "MarkerOnly":"Marker, not wire geometry"}.items():
        obj.addProperty("App::PropertyString",name,"Harness");setattr(obj,name,value)
    groups[key].addObject(obj)
doc.recompute()
output.parent.mkdir(parents=True,exist_ok=True)
doc.saveAs(str(output));App.closeDocument(doc.Name)

check=App.openDocument(str(output))
shape=check.getObject("MeasuredBoardBody").Shape
if not shape.isValid() or len(shape.Solids)!=1 or abs(shape.Volume-board_shape.Volume)>1e-6*board_shape.Volume:
    raise RuntimeError("The board body changed while being copied into the harness model")
for tap in taps:
    obj=check.getObject("Tap_"+tap["pad"]); p=pads[tap["pad"]]
    if obj is None or obj.Shape.isNull() or not obj.Shape.isValid() or len(obj.Shape.Solids)!=1:
        raise RuntimeError("Tap marker "+tap["pad"]+" did not survive saving as one valid solid")
    c=obj.Shape.BoundBox
    if abs((c.XMin+c.XMax)/2-p["x"])>1e-6 or abs((c.YMin+c.YMax)/2-p["y"])>1e-6 or abs(c.ZMin-survey_geometry.PAD_HEIGHT_MM)>1e-6:
        raise RuntimeError("Tap marker "+tap["pad"]+" is not on its pad")
solids=sum(1 for o in check.Objects if o.TypeId=="Part::Feature" and not o.Shape.isNull() and o.Shape.Solids)
App.closeDocument(check.Name)
by_connector={}
for w in wires: by_connector[w["connector"]]=by_connector.get(w["connector"],0)+1
report={"file":output.relative_to(project).as_posix(),"revision":revision,"state":"proposed_taps_only",
        "board_survey":source.relative_to(project).as_posix(),"native_reopened":True,
        "solid_objects":solids,"expected_solid_objects":1+len(pad_shapes)+len(taps),
        "pads_copied":len(pad_shapes),"tap_markers":len(taps),"wires":len(wires),"wires_by_connector":by_connector,
        "wires_with_unsettled_pad":sorted(w["wire_id"] for w in wires if len(w["pads"])>1),
        "pads_with_several_wires":{t["pad"]:[w["wire_id"]+("?" if w["candidate"] else "") for w in t["wires"]] for t in taps if len(t["wires"])>1},
        "not_modelled":["wires and routes","connector housings","S3, display, microphone, button-processor board, battery","lengths"],
        "connection_list_sha256":harness_taps.lf_sha256(project/harness_taps.SOURCES)}
if solids!=report["expected_solid_objects"]: raise RuntimeError("Unexpected geometry in the harness model")
(output.parent/(output.stem+"-validation.json")).write_text(json.dumps(report,indent=2)+"\n")
print(json.dumps(report,indent=2))
