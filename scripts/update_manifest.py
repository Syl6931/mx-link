#!/usr/bin/env python3
"""Rebuild MANIFEST.sha256 from distributable Git files (never include .git)."""
from pathlib import Path
import hashlib
import subprocess

root = Path(__file__).resolve().parent.parent
names = subprocess.check_output(
    ["git", "ls-files", "--cached", "--others", "--exclude-standard", "-z"], cwd=root
).split(b"\0")
files = sorted(Path(name.decode()) for name in names if name)
lines = []
for rel in files:
    if (rel.as_posix() == "MANIFEST.sha256" or ".git" in rel.parts or
            "__pycache__" in rel.parts):
        continue
    path = root / rel
    if path.is_file():
        lines.append(f"{hashlib.sha256(path.read_bytes()).hexdigest()}  ./{rel.as_posix()}")
(root / "MANIFEST.sha256").write_text("\n".join(lines) + "\n", encoding="utf-8")
print(f"Manifest updated ({len(lines)} distributable files)")
