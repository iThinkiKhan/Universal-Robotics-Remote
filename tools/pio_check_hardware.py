"""Fail every PlatformIO build/upload if canonical mappings and generated files diverge."""
from pathlib import Path
import subprocess
import sys

Import("env")
project_root = Path(env.subst("$PROJECT_DIR")).parent
subprocess.run([sys.executable, str(project_root / "tools/generate_hardware.py"), "--check"],
               cwd=project_root, check=True)
