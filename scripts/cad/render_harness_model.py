"""Run in an isolated FreeCAD GUI session to style and render an existing harness model snapshot."""
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
native=project/os.environ["ECAD_HARNESS_MODEL"]
output=project/"exports/harness"
output.mkdir(parents=True,exist_ok=True)
report={"passed":False,"model":native.relative_to(project).as_posix()}
try:
    Gui.activateWorkbench("PartWorkbench")
    import PartGui
    doc=App.openDocument(str(native))
    board=doc.getObject("MeasuredBoardBody")
    board.ViewObject.ShapeColor=(0.12,0.65,0.75); board.ViewObject.LineColor=(0.05,0.15,0.20); board.ViewObject.Transparency=45
    taps=[o for o in doc.Objects if o.Name.startswith("Tap_")]
    for o in doc.Objects:
        if o.Name.startswith("Pad_"):
            o.ViewObject.ShapeColor=(0.78,0.78,0.74); o.ViewObject.LineColor=(0.45,0.45,0.42)
    for o in taps:
        rgb=tuple(float(c) for c in o.MarkerRGB.split(","))
        o.ViewObject.ShapeColor=rgb; o.ViewObject.LineColor=rgb
        o.ViewObject.Transparency=0 if o.Settled=="yes" else 60
    for o in doc.Objects:                                   # documents built headless carry no view state
        if o.TypeId=="Part::Feature": o.ViewObject.Visibility=True
    doc.recompute(); Gui.updateGui()
    view=Gui.activeDocument().activeView()
    view.setAnimationEnabled(False)
    images=[]
    for name,setter in (("AXO",view.viewAxonometric),("TOP",view.viewTop)):
        setter(); view.fitAll(); Gui.updateGui(); view.redraw(); Gui.updateGui()
        image=output/(native.stem+"-TAPS-"+name+".png")
        view.saveImage(str(image),1600,1000,"White")
        png_clean.strip_png_metadata(image); images.append(image)
    pixels=QtGui.QImage(str(images[0]))
    nonwhite=sum(1 for x in range(0,pixels.width(),10) for y in range(0,pixels.height(),10)
                 if min(QtGui.QColor(pixels.pixel(x,y)).getRgb()[:3])<240)
    doc.save(); App.closeDocument(doc.Name)
    report.update({"passed":nonwhite>25,"images":[i.relative_to(project).as_posix() for i in images],
                   "nonwhite_preview_samples":nonwhite,"tap_markers_shown":len(taps),
                   "limitation":"Tap markers on the traced board only. Marker colours identify the connector, not the wire. No wires, housings or other modules are modelled."})
except Exception:
    report["error"]=traceback.format_exc()
finally:
    (output/(native.stem+"-render-validation.json")).write_text(json.dumps(report,indent=2)+"\n")
    print(json.dumps(report,indent=2),flush=True)
    for name in list(App.listDocuments()): App.closeDocument(name)
    QtCore.QTimer.singleShot(0,Gui.getMainWindow().close)
