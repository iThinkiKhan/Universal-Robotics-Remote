"""Archive original board photos, source hashes and a portable local gallery."""
import argparse
import hashlib
import html
import json
from pathlib import Path
import re
import shutil
from urllib.parse import quote

def archive(project, board, sources, source_reference, descriptions=None):
    project=Path(project).resolve()
    if not re.fullmatch(r"[a-z0-9][a-z0-9_-]*",board):
        raise ValueError("Board ID must use lowercase letters, digits, hyphens or underscores")
    folder=project/"measurements/photos"/board
    originals=folder/"originals";originals.mkdir(parents=True,exist_ok=True)
    manifest_path=folder/"manifest.json"
    manifest=json.loads(manifest_path.read_text()) if manifest_path.exists() else {
        "schema_version":1,"board_id":board,"source_reference":source_reference,
        "scale":"Unscaled reference photos; not dimensional measurements","photos":[]}
    records={p["filename"]:p for p in manifest["photos"]}
    for item in sources:
        source=Path(item).resolve()
        if not source.is_file() or source.suffix.lower() not in {".jpg",".jpeg",".png",".webp"}:
            raise ValueError(f"Unsupported or missing photo: {source}")
        digest=hashlib.sha256(source.read_bytes()).hexdigest()
        name=source.name;target=originals/name
        if target.exists() and hashlib.sha256(target.read_bytes()).hexdigest()!=digest:
            name=f"{source.stem}-{digest[:12]}{source.suffix.lower()}";target=originals/name
        if target.resolve()!=source:
            shutil.copy2(source,target)
        if hashlib.sha256(target.read_bytes()).hexdigest()!=digest:
            raise RuntimeError(f"Archive verification failed: {name}")
        records[name]={"filename":name,"original_filename":source.name,"sha256":digest,
                       "bytes":target.stat().st_size,"description":(descriptions or {}).get(source.name,records.get(name,{}).get("description","Reference photograph"))}
    manifest["photos"]=sorted(records.values(),key=lambda p:p["filename"])
    manifest_path.write_text(json.dumps(manifest,indent=2)+"\n",encoding="utf-8",newline="\n")
    cards=[]
    for p in manifest["photos"]:
        name=html.escape(p["filename"]);url="originals/"+quote(p["filename"])
        cards.append(f'<article id="photo-{name}"><a href="{url}"><img src="{url}" alt="{html.escape(p["description"],quote=True)}" loading="lazy"></a><h2>{name}</h2><p>{html.escape(p["description"])}</p><small>Original file / unscaled</small></article>')
    page='''<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Board photo archive</title>
<style>body{font:16px system-ui;background:#10161d;color:#e7edf4;margin:0;padding:28px}h1{margin-bottom:8px}header{max-width:900px;margin-bottom:26px}main{display:grid;grid-template-columns:repeat(auto-fit,minmax(300px,1fr));gap:22px}article{background:#1b2530;padding:14px;border:1px solid #334657;border-radius:10px}img{display:block;width:100%;height:350px;object-fit:contain;background:#080c10}h2{font-size:18px}p{line-height:1.5}small{color:#9db4c8}a{color:#76dddb}</style>
<header><h1>'''+html.escape(board)+''' — photo archive</h1><p>Original reference files, unchanged and hash-verified. These handheld views are not to scale. Click a photograph for the full original.</p><a href="manifest.json">Source manifest and SHA-256 hashes</a></header><main>'''+"\n".join(cards)+"</main></html>\n"
    (folder/"index.html").write_text(page,encoding="utf-8",newline="\n")
    return manifest_path

if __name__=="__main__":
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--project",type=Path,required=True)
    parser.add_argument("--board",required=True)
    parser.add_argument("--source-reference",required=True)
    parser.add_argument("photos",nargs="+",type=Path)
    args=parser.parse_args()
    print(archive(args.project,args.board,args.photos,args.source_reference))
