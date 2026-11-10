"""Run in an isolated FreeCAD GUI macro to style/render an existing survey snapshot."""
import json
import os
import sys
from pathlib import Path
import traceback
import FreeCAD as App
import FreeCADGui as Gui
from PySide import QtCore, QtGui

sys.path.insert(0,str(Path(os.environ.get("ECAD_SURVEY_SCRIPTS",Path(__file__).resolve().parent))))
import png_clean      # FreeCAD embeds the output path in saved PNGs; published images must not carry it

project=Path(os.environ["ECAD_SURVEY_PROJECT"]).resolve()
native=project/os.environ["ECAD_SURVEY_MODEL"]
output=project/"exports/boards"/native.parent.name
output.mkdir(parents=True,exist_ok=True)
report={"passed":False,"model":native.relative_to(project).as_posix()}
try:
    Gui.activateWorkbench("PartWorkbench")
    import PartGui
    doc=App.openDocument(str(native))
    envelope=doc.getObject("MeasuredBoardBody")
    measured_outline=envelope is not None
    if envelope is None:
        envelope=doc.getObject("MeasuredBoundingEnvelope")
    if envelope is None:
        raise ValueError("No measured envelope to render yet")
    with_holes=(not measured_outline) and getattr(envelope,"HolesCut","none")!="none"
    traced=measured_outline and getattr(envelope,"OutlineState","measured")=="traced"
    kind=("TRACED_OUTLINE" if traced else "MEASURED_OUTLINE") if measured_outline else ("ENVELOPE_WITH_HOLES" if with_holes else "ENVELOPE_ONLY")
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
    image=output/(native.stem+"-"+kind+".png")
    Gui.activeDocument().activeView().saveImage(str(image),1200,750,"White")
    if measured_outline or with_holes:
        Gui.activeDocument().activeView().setAnimationEnabled(False)   # else the capture can land mid-rotation
        Gui.activeDocument().activeView().viewTop()
        Gui.activeDocument().activeView().fitAll()
        Gui.updateGui()
        Gui.activeDocument().activeView().redraw()
        Gui.updateGui()
        Gui.activeDocument().activeView().saveImage(str(output/(native.stem+"-"+kind+"-TOP.png")),1200,750,"White")
    for rendered in (image,output/(native.stem+"-"+kind+"-TOP.png")):
        if rendered.is_file():
            png_clean.strip_png_metadata(rendered)
    pixels=QtGui.QImage(str(image))
    nonwhite=sum(1 for x in range(0,pixels.width(),10) for y in range(0,pixels.height(),10)
                 if min(QtGui.QColor(pixels.pixel(x,y)).getRgb()[:3])<240)
    doc.save()
    App.closeDocument(doc.Name)
    check=App.openDocument(str(native))
    shape=check.getObject("MeasuredBoardBody" if measured_outline else "MeasuredBoundingEnvelope").Shape
    bounds=shape.BoundBox
    report.update({"passed":shape.isValid() and nonwhite>25,"image":image.relative_to(project).as_posix(),
                   "nonwhite_preview_samples":nonwhite,
                   "envelope_dimensions_mm":[bounds.XLength,bounds.YLength,bounds.ZLength],
                   "limitation":(("Traced (photo-rectified) outline with its stated uncertainty, plus listed holes. Components, connectors and daughterboards remain unmodeled."
                                  if traced else
                                  "Measured outline and listed holes only. Components, connectors and daughterboards remain unmodeled.")
                                 if measured_outline else
                                 "Bounding rectangle with the listed measured holes cut in. The board contour, corner chamfer, notches, components and daughterboards remain unmodeled."
                                 if with_holes else
                                 "Bounding envelope only. Irregular outline, hole positions and component geometry remain unmodeled.")})
    App.closeDocument(check.Name)
except Exception:
    report["error"]=traceback.format_exc()
finally:
    (output/(native.stem+"-render-validation.json")).write_text(json.dumps(report,indent=2)+"\n")
    print(json.dumps(report,indent=2),flush=True)
    for name in list(App.listDocuments()): App.closeDocument(name)
    QtCore.QTimer.singleShot(0,Gui.getMainWindow().close)
