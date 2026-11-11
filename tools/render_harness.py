"""Render every proposed harness with locally installed WireViz/Graphviz."""
import hashlib
import json
from pathlib import Path
import subprocess
import sys
ROOT=Path(__file__).resolve().parents[1]
if __name__=='__main__':
    subprocess.run([sys.executable,str(ROOT/'tools/generate_hardware.py'),'--check'],check=True)
    output=ROOT/'electronics/generated';output.mkdir(exist_ok=True)
    paths=[ROOT/'hardware/signals.json',ROOT/'electronics/harnesses.json',ROOT/'electronics/harness-sources-proposed.csv']
    for source in sorted((ROOT/'electronics/harnesses').glob('*-proposed.yml')):
        subprocess.run(['wireviz','-f','ps','-o',str(output),str(source)],check=True)
        paths+=[source,output/(source.stem+'.png'),output/(source.stem+'.svg')]
    manifest={'tool':'WireViz 0.4.1 / Graphviz','sha256':{
        p.relative_to(ROOT).as_posix():hashlib.sha256(p.read_bytes()).hexdigest() for p in paths}}
    (output/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
