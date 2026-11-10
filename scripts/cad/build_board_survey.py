"""Run with native freecadcmd: create a portable, revisioned board-survey document."""
import hashlib
import json
import os
import math
from pathlib import Path
import FreeCAD as App
import Part

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
if all(key in values for key in ("W","H","T")):
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
if shape_count:
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
