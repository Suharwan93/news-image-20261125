#!/usr/bin/env python3
"""Entry point for the make.fun news-image-20261125 bounty.

Standard library only: copies the entry image (entry.png, rendered by
draw.py from the sourced news in news.json) to /output/entry.png,
where the grader reads it. Deterministic: the same file is copied on
every run, so two runs write identical bytes.

Outside the grader's container, MAKEFUN_OUTPUT_DIR stands in for
/output:
    mkdir -p out && MAKEFUN_OUTPUT_DIR=out python3 main.py
"""

import os
import shutil
import sys

HERE = os.path.dirname(os.path.abspath(__file__))


def main():
    out_dir = os.environ.get("MAKEFUN_OUTPUT_DIR", "/output")
    os.makedirs(out_dir, exist_ok=True)
    src = os.path.join(HERE, "entry.png")
    dst = os.path.join(out_dir, "entry.png")
    shutil.copyfile(src, dst)
    size = os.path.getsize(dst)
    print(f"Wrote {dst} ({size} bytes)")
    assert size <= 1024 * 1024, "entry.png must be <= 1 MiB"
    return 0


if __name__ == "__main__":
    sys.exit(main())
