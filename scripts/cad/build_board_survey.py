"""Run with native freecadcmd: create a portable, revisioned board-survey document."""
import hashlib
import json
import os
import math
import sys
from pathlib import Path
import FreeCAD as App
import Part

sys.path.insert(0,str(Path(os.environ.get("ECAD_SURVEY_SCRIPTS",Path(__file__).resolve().parent))))
import survey_geometry

project=Path(os.environ["ECAD_SURVEY_PROJECT"]).resolve()
survey_path=project/os.environ["ECAD_SURVEY_RECORD"]
survey=json.loads(survey_path.read_text())
photos=project/survey["photo_folder"]
manifest=json.loads((photos/"manifest.json").read_text())
output=project/"cad/boards"/survey["board_id"]/f'{survey["board_id"]}-survey-r{survey["revision"]:03d}.FCStd'
if output.exists():
    raise RuntimeError("Existing native survey preserved. Increment the survey revision for a new generated snapshot.")
output.parent.mkdir(parents=True,exist_ok=True)
doc=App.newDocument("BoardSurvey")
doc.Label=survey["name"]+" — "+survey["state"].upper().replace("_"," ")
record=doc.addObject("App::FeaturePython","SurveyRecord")
for key,value in {"BoardID":survey["board_id"],"State":survey["state"],"SurveyJSON":survey_path.relative_to(project).as_posix(),
                  "SourceSHA256":hashlib.sha256(survey_path.read_bytes()).hexdigest(),
                  "PhotoGallery":(Path(survey["photo_folder"])/"index.html").as_posix(),
                  "ModelPolicy":survey["model_policy"],"ReferenceView":survey.get("view_description") or "Unassigned",
                  "Origin":survey.get("origin_description") or "Unassigned"}.items():
    record.addProperty("App::PropertyString",key,"Survey");setattr(record,key,value)
readings=doc.addObject("App::DocumentObjectGroup","Measurements")
values={}
for reading in survey["readings"]:
    obj=doc.addObject("App::FeaturePython","Reading_"+reading["id"])
    obj.Label=reading["id"]+" — "+reading["description"]
    obj.addProperty("App::PropertyString","State");obj.State=reading["state"]
    value=reading["value_mm"]
    if value is not None:
        if reading["state"]!="measured" or type(value) not in (float,int) or not math.isfinite(value) or value<=0:
            raise ValueError("Dimensions require positive measured values")
        obj.addProperty("App::PropertyLength","Value");obj.Value=value
        values[reading["id"]]=value
    else:
        obj.addProperty("App::PropertyString","ValuePending");obj.ValuePending="Not measured — no numeric default"
    readings.addObject(obj)
refs=doc.addObject("App::DocumentObjectGroup","PhotoReferences")
for index,photo in enumerate(manifest["photos"],1):
    path=photos/"originals"/photo["filename"]
    if hashlib.sha256(path.read_bytes()).hexdigest()!=photo["sha256"]:
        raise ValueError("Photo integrity mismatch: "+str(path))
    obj=doc.addObject("App::FeaturePython",f"Photo_{index:02d}")
    obj.Label=photo["filename"]+" — "+photo["description"]
    for name,value in {"ProjectRelativePath":path.relative_to(project).as_posix(),"SHA256":photo["sha256"],"Scale":"UNSCALED reference photograph"}.items():
        obj.addProperty("App::PropertyString",name);setattr(obj,name,value)
    refs.addObject(obj)
modules=doc.addObject("App::DocumentObjectGroup","SeparateModules")
for index,module in enumerate(survey["separate_modules"],1):
    obj=doc.addObject("App::FeaturePython",f"Module_{index:02d}")
    obj.Label=module["name"]
    obj.addProperty("App::PropertyString","Status");obj.Status=module["state"]
    modules.addObject(obj)
geometry=survey_geometry.resolve(survey)      # raises on anything inconsistent; never defaults
def _slot_or_round(hole,height,z):
    p1,p2,r=hole["p1"],hole["p2"],hole["radius"]
    shape=Part.makeCylinder(r,height,App.Vector(p1[0],p1[1],z))
    length=math.dist(p1,p2)
    if length>0:
        box=Part.makeBox(length,2*r,height,App.Vector(0,-r,z))
        box.rotate(App.Vector(0,0,0),App.Vector(0,0,1),math.degrees(math.atan2(p2[1]-p1[1],p2[0]-p1[0])))
        box.translate(App.Vector(p1[0],p1[1],0))
        shape=shape.fuse(box).fuse(Part.makeCylinder(r,height,App.Vector(p2[0],p2[1],z)))
    return shape
if geometry["outline"]:
    if "T" not in values: raise ValueError("A measured outline needs a measured thickness T")
    out=geometry["outline"]
    edges=[];prev=out["start"]
    for seg in out["segments"]:
        if seg[0]=="line":
            edges.append(Part.LineSegment(App.Vector(prev[0],prev[1],0),App.Vector(seg[1][0],seg[1][1],0)).toShape());prev=seg[1]
        else:
            edges.append(Part.Arc(App.Vector(prev[0],prev[1],0),App.Vector(seg[1][0],seg[1][1],0),App.Vector(seg[2][0],seg[2][1],0)).toShape());prev=seg[2]
    if math.dist(prev,out["start"])>1e-9:
        edges.append(Part.LineSegment(App.Vector(prev[0],prev[1],0),App.Vector(out["start"][0],out["start"][1],0)).toShape())
    body=Part.Face(Part.Wire(edges)).extrude(App.Vector(0,0,-values["T"]))
    for hole in geometry["holes"]:
        body=body.cut(_slot_or_round(hole,values["T"]+2,-values["T"]-1))
    board=doc.addObject("Part::Feature","MeasuredBoardBody")
    board.Label="MEASURED OUTLINE AND HOLES — components and connectors unmodeled"
    board.Shape=body
    for name,value in {"Limitation":survey["model_policy"],"Datum":survey["origin_description"],
                       "FrameNote":"Top surface Z=0, substrate below. X right, Y up from the named datum.",
                       "HolesCut":", ".join(h["id"] for h in geometry["holes"]) or "none"}.items():
        board.addProperty("App::PropertyString",name);setattr(board,name,value)
elif all(key in values for key in ("W","H","T")):
    envelope=doc.addObject("Part::Feature","MeasuredBoundingEnvelope")
    envelope.Label="MEASURED ENVELOPE ONLY — irregular outline unmodeled"
    envelope.Shape=Part.makeBox(values["W"],values["H"],values["T"],App.Vector(0,0,-values["T"]))
    envelope.addProperty("App::PropertyString","Limitation");envelope.Limitation=survey["model_policy"]
    envelope.addProperty("App::PropertyString","FrameNote");envelope.FrameNote="Envelope frame only: top Z=0, X/Y at rectangle corner. Physical board datum and irregular outline remain unassigned."
doc.recompute();doc.saveAs(str(output));App.closeDocument(doc.Name)
check=App.openDocument(str(output))
shape_count=sum(1 for obj in check.Objects if hasattr(obj,"Shape") and not obj.Shape.isNull() and obj.Shape.Solids)
report={"file":output.relative_to(project).as_posix(),"board_id":survey["board_id"],"revision":survey["revision"],
        "state":survey["state"],"photo_references":len(manifest["photos"]),"solid_objects":shape_count,
        "expected_solid_objects":int(all(key in values for key in ("W","H","T"))),
        "native_reopened":True,"source_sha256":hashlib.sha256(survey_path.read_bytes()).hexdigest()}
if geometry["outline"] and shape_count:
    shape=check.getObject("MeasuredBoardBody").Shape
    bounds=shape.BoundBox
    expected=geometry["volume_mm3"]
    report.update({"geometry":"measured_outline","datum":survey["origin_description"],
                   "bounding_box_mm":[bounds.XLength,bounds.YLength,bounds.ZLength],
                   "holes_cut":len(geometry["holes"]),"hole_ids":[h["id"] for h in geometry["holes"]],
                   "body_volume_mm3":shape.Volume,"expected_volume_mm3":expected,"top_z_mm":bounds.ZMax})
    if not shape.isValid() or len(shape.Solids)!=1: raise RuntimeError("Saved board body is not one valid solid")
    if abs(shape.Volume-expected)>0.01*expected: raise RuntimeError("Saved body volume disagrees with the recorded measurements")
    if abs(bounds.ZLength-values["T"])>1e-6: raise RuntimeError("Saved body thickness does not match T")
elif shape_count:
    shape=check.getObject("MeasuredBoundingEnvelope").Shape
    bounds=shape.BoundBox
    report["envelope_dimensions_mm"]=[bounds.XLength,bounds.YLength,bounds.ZLength]
    report["envelope_volume_mm3"]=shape.Volume
    report["top_z_mm"]=bounds.ZMax
    report["holes_cut"]=0
    if not shape.isValid() or any(abs(a-b)>1e-6 for a,b in zip(report["envelope_dimensions_mm"],[values["W"],values["H"],values["T"]])):
        raise RuntimeError("Saved envelope does not match recorded measurements")
App.closeDocument(check.Name)
if shape_count!=report["expected_solid_objects"]: raise RuntimeError("Unexpected geometry in survey")
(output.parent/(output.stem+"-validation.json")).write_text(json.dumps(report,indent=2)+"\n")
print(json.dumps(report,indent=2))
