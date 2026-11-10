"""Initialize a project-specific board survey without inventing dimensions or geometry."""
import argparse
import json
from pathlib import Path
import re

def create(project, board, name, photos, reference_photo=None):
    project=Path(project).expanduser().resolve()
    if not (project/"README.md").is_file():
        raise ValueError("Choose an existing project with a README.md")
    if not re.fullmatch(r"[a-z0-9][a-z0-9_-]*",board):
        raise ValueError("Invalid board ID")
    target=project/"measurements/boards"/(board+".json")
    if target.exists():
        raise ValueError(f"Existing survey preserved: {target}")
    photos=Path(photos)
    if photos.is_absolute(): photos=photos.resolve().relative_to(project)
    if ".." in photos.parts or not (project/photos/"manifest.json").is_file():
        raise ValueError("Photo folder must be an archived manifest inside this project")
    manifest=json.loads((project/photos/"manifest.json").read_text())
    if reference_photo and reference_photo not in {p["filename"] for p in manifest["photos"]}:
        raise ValueError("Reference photograph is not in the archive")
    readings=[]
    for key,label in [("W","Maximum bare main-PCB width; exclude detached modules"),
                      ("H","Maximum main-PCB height; include PCB tabs, exclude connector overhang"),
                      ("T","Bare substrate thickness; exclude solder and components"),
                      ("A","Reference hole diameter; identify the exact hole in survey notes")]:
        readings.append({"id":key,"description":label,"value_mm":None,"state":"pending",
                         "method":None,"date":None,"uncertainty_mm":None,"evidence":None})
    survey={"schema_version":1,"revision":1,"board_id":board,"name":name,
            "photo_folder":photos.as_posix(),"reference_photo":reference_photo,
            "view_description":None,"origin_description":None,
            "state":"awaiting_measurements","readings":readings,
            "outline":{"state":"unmeasured","points_mm":[]},"mounting_holes":[],
            "separate_modules":[],"notes":[],
            "model_policy":"Measured W/H/T can define a bounding envelope only. Do not call a rectangle the board outline. Hole diameter alone does not locate a hole; require datum coordinates. No inferred measurements from handheld photos."}
    target.parent.mkdir(parents=True,exist_ok=True)
    target.write_text(json.dumps(survey,indent=2)+"\n",encoding="utf-8",newline="\n")
    (project/"cad/boards"/board).mkdir(parents=True,exist_ok=True)
    return target

if __name__=="__main__":
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--project",type=Path,required=True)
    parser.add_argument("--board",required=True)
    parser.add_argument("--name",required=True)
    parser.add_argument("--photos",required=True,type=Path)
    parser.add_argument("--reference-photo")
    args=parser.parse_args()
    print(create(args.project,args.board,args.name,args.photos,args.reference_photo))
