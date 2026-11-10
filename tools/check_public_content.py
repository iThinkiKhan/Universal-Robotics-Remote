"""Check tracked/public candidate content for common publication mistakes.

This is a supplemental privacy check, not a replacement for review or a secret scanner.
"""
import re
import subprocess
import sys
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FORBIDDEN = {'.bin', '.elf', '.hex', '.uf2', '.gcode', '.gco', '.bgcode', '.pem', '.key', '.p12', '.pfx'}
PATTERNS = {
    'private IPv4': re.compile(r'\b(?:192\.168\.\d{1,3}\.\d{1,3}|10\.\d{1,3}\.\d{1,3}\.\d{1,3}|172\.(?:1[6-9]|2\d|3[01])\.\d{1,3}\.\d{1,3})\b'),
    'personal home path': re.compile(r'(?:[A-Z]:[\\/]+Users[\\/]+[^\s\\/]+|/home/[a-z_][a-z0-9_-]*/)', re.I),
    'MAC address': re.compile(r'\b(?:[0-9a-f]{2}:){5}[0-9a-f]{2}\b', re.I),
    'private key': re.compile(r'-----BEGIN (?:OPENSSH|RSA|EC|DSA|PRIVATE).*?KEY-----'),
    'GitHub token': re.compile(r'\b(?:gh[pousr]_[A-Za-z0-9]{30,}|github_pat_[A-Za-z0-9_]{40,})\b'),
    'cloud access key': re.compile(r'\b(?:AKIA|ASIA)[A-Z0-9]{16}\b'),
    'personal email': re.compile(r'\b[A-Z0-9._%+-]+@(?!users\.noreply\.github\.com\b)[A-Z0-9.-]+\.[A-Z]{2,}\b', re.I),
}

def jpeg_metadata(data):
    pos = 2
    while pos < len(data):
        if data[pos] != 255:
            return True
        while data[pos] == 255:
            pos += 1
        marker = data[pos]
        pos += 1
        if marker in (0xda, 0xd9):
            return False
        size = int.from_bytes(data[pos:pos + 2], 'big')
        if 0xe1 <= marker <= 0xed or marker in (0xef, 0xfe):
            return True
        if size < 2:
            return True
        pos += size
    return True

def inspect_text(name, data, failures):
    text = data.decode('utf-8', errors='replace')
    for kind, pattern in PATTERNS.items():
        if pattern.search(text):
            failures.append((name, kind))

def check(paths):
    failures = []
    for path in paths:
        if not path.is_file():
            continue
        name = path.relative_to(ROOT).as_posix()
        if name.startswith(('local/', 'backups/', 'internal/')) or path.suffix.lower() in FORBIDDEN or path.name.startswith('.env'):
            failures.append((name, 'private or unsupported public file'))
            continue
        data = path.read_bytes()
        if path.suffix.lower() in ('.jpg', '.jpeg'):
            if jpeg_metadata(data):
                failures.append((name, 'JPEG metadata requires review/removal'))
        elif zipfile.is_zipfile(path):
            with zipfile.ZipFile(path) as archive:
                for member in archive.namelist():
                    if member.endswith(('.xml', '.json', '.txt')):
                        inspect_text(name + ':' + member, archive.read(member), failures)
        elif path.suffix.lower() != '.png':
            inspect_text(name, data, failures)
    return failures

if __name__ == '__main__':
    result = subprocess.run(['git', 'ls-files', '-z'], cwd=ROOT, capture_output=True)
    if result.returncode:
        raise SystemExit('Run inside a Git checkout after staging the candidate files')
    paths = [ROOT / name for name in result.stdout.decode().split('\0') if name]
    if not paths:
        raise SystemExit('No tracked/staged files to inspect')
    failures = check(paths)
    for name, kind in failures:
        print(f'{name}: {kind}')
    print(f'Public content check: {len(paths)} files, {len(failures)} findings')
    sys.exit(bool(failures))
