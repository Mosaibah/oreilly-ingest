#!/usr/bin/env python3
"""Patch book_title into all *_chunks.jsonl files in the output directory."""

import json
import os
import sys
from pathlib import Path

import config

OUTPUT_DIR = config.OUTPUT_DIR


def patch_file(jsonl_path: Path) -> int:
    book_title = jsonl_path.stem.removesuffix("_chunks")
    tmp_path = jsonl_path.with_suffix(".jsonl.tmp")
    count = 0

    with open(jsonl_path, encoding="utf-8") as src, open(tmp_path, "w", encoding="utf-8") as dst:
        for line in src:
            line = line.strip()
            if not line:
                continue
            chunk = json.loads(line)
            chunk["book_title"] = book_title
            dst.write(json.dumps(chunk, ensure_ascii=False) + "\n")
            count += 1

    os.replace(tmp_path, jsonl_path)
    return count


def main():
    files = sorted(OUTPUT_DIR.rglob("*_chunks.jsonl"))
    if not files:
        print("No *_chunks.jsonl files found.")
        sys.exit(0)

    total_chunks = 0
    for f in files:
        count = patch_file(f)
        print(f"  {count:>5} chunks  {f.relative_to(OUTPUT_DIR)}")
        total_chunks += count

    print(f"\nPatched {total_chunks} chunks across {len(files)} files.")


if __name__ == "__main__":
    main()
