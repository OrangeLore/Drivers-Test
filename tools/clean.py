#!/usr/bin/env python3
"""Delete legacy/temp leftovers so the folder is clean for git. Safe: only removes scratch files,
build junk, logs and generated artifacts — never the app, datasets, images, tools, or docs.

    python tools/clean.py
"""
import os, glob, shutil

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FILE_PATTERNS = ["_*.ps1", "_*.py", "_*.png", "*.log", "*-testset.json",
                 "start_local.bat", "tools/_*.py", "tools/_*.ps1"]
DIRS = ["figures_alberta", "images/gen", "__pycache__", "tools/__pycache__", "handbooks"]

def main():
    removed = []
    for pat in FILE_PATTERNS:
        for f in glob.glob(os.path.join(BASE, pat)):
            if os.path.basename(f) == "clean.py":
                continue
            try:
                os.remove(f); removed.append(os.path.relpath(f, BASE))
            except Exception as e:
                print("skip", f, e)
    for d in DIRS:
        p = os.path.join(BASE, d)
        if os.path.isdir(p):
            shutil.rmtree(p, ignore_errors=True); removed.append(d + "/")
    print("Removed %d item(s):" % len(removed))
    for r in removed:
        print("  -", r)
    print("Kept: index.html, questions*.js, ontario.js, images/, tools/*.py, docs/, README, LICENSE, run.*")

if __name__ == "__main__":
    main()
