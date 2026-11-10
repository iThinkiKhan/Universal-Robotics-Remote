"""Run in an isolated FreeCAD GUI macro to style/render an existing survey snapshot."""
import json
import os
from pathlib import Path
import traceback
import FreeCAD as App
import FreeCADGui as Gui
from PySide import QtCore, QtGui

project=Path(os.environ["ECAD_SURVEY_PROJECT"]).resolve()
native=project/os.environ["ECAD_SURVEY_MODEL"]
output=project/"exports/boards"/native.parent.name
output.mkdir(parents=True,exist_ok=True)
report={"passed":False,"model":native.relative_to(project).as_posix()}
try:
    Gui.activateWorkbench("PartWorkbench")
    import PartGui
    doc=App.openDocument(str(native))
    envelope=doc.getObject("MeasuredBoundingEnvelope")
    if envelope is None:
        raise ValueError("No measured envelope to render yet")
    envelope.ViewObject.ShapeColor=(0.12,0.65,0.75)
    envelope.ViewObject.LineColor=(0.05,0.15,0.20)
    envelope.ViewObject.Transparency=45
    envelope.ViewObject.Visibility=True
    doc.recompute()
    Gui.updateGui()
    Gui.activeDocument().activeView().viewAxonometric()
    Gui.activeDocument().activeView().fitAll()
    Gui.updateGui()
    Gui.activeDocument().activeView().redraw()
    Gui.updateGui()
    image=output/(native.stem+"-ENVELOPE_ONLY.png")
    Gui.activeDocument().activeView().saveImage(str(image),1200,750,"White")
    pixels=QtGui.QImage(str(image))
    nonwhite=sum(1 for x in range(0,pixels.width(),10) for y in range(0,pixels.height(),10)
                 if min(QtGui.QColor(pixels.pixel(x,y)).getRgb()[:3])<240)
    doc.save()
    App.closeDocument(doc.Name)
    check=App.openDocument(str(native))
    shape=check.getObject("MeasuredBoundingEnvelope").Shape
    bounds=shape.BoundBox
    report.update({"passed":shape.isValid() and nonwhite>25,"image":image.relative_to(project).as_posix(),
                   "nonwhite_preview_samples":nonwhite,
                   "envelope_dimensions_mm":[bounds.XLength,bounds.YLength,bounds.ZLength],
                   "limitation":"Bounding envelope only. Irregular outline, hole positions and component geometry remain unmodeled."})
    App.closeDocument(check.Name)
except Exception:
    report["error"]=traceback.format_exc()
finally:
    (output/(native.stem+"-render-validation.json")).write_text(json.dumps(report,indent=2)+"\n")
    print(json.dumps(report,indent=2),flush=True)
    for name in list(App.listDocuments()): App.closeDocument(name)
    QtCore.QTimer.singleShot(0,Gui.getMainWindow().close)
