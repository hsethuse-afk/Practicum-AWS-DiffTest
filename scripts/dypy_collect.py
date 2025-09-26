#!/usr/bin/env python3
from __future__ import annotations
import argparse, os, glob, json, random, pathlib, datetime, sys

DEFAULT_INCLUDES = ["**/*.py"]
DEFAULT_EXCLUDES = [
    "**/__pycache__/**",
    "**/.git/**",
    "**/.venv/**",
    "**/env/**",
    "**/build/**",
    "**/dist/**",
    "**/.mypy_cache/**",
    "**/site-packages/**",
    "**/tests/**",          # skip tests for now; remove if you want them
]

def discover(root: str, includes: list[str], excludes: list[str]) -> list[str]:
    root = os.path.abspath(root)
    if not os.path.isdir(root):
        raise FileNotFoundError(f"DyPyBench root not found: {root}")

    cand: set[str] = set()
    for g in includes:
        cand |= set(glob.glob(os.path.join(root, g), recursive=True))

    # Remove excluded paths
    for g in excludes:
        for p in glob.glob(os.path.join(root, g), recursive=True):
            if p in cand:
                cand.remove(p)

    # Keep only regular .py files
    files = sorted(p for p in cand if p.endswith(".py") and os.path.isfile(p))
    return files

def main():
    ap = argparse.ArgumentParser(description="Collect a small DyPyBench subset into one JSON file")
    ap.add_argument("--root", required=True, help="Path to local DyPyBench checkout")
    ap.add_argument("--k", type=int, default=25, help="How many files to sample (20–30 recommended)")
    ap.add_argument("--seed", type=int, default=13, help="Random seed for deterministic sampling")
    ap.add_argument("--out", default="data/datasets/dypybench_subset.json", help="Output JSON path")
    ap.add_argument("--include", nargs="*", default=DEFAULT_INCLUDES, help="Glob(s) to include")
    ap.add_argument("--exclude", nargs="*", default=DEFAULT_EXCLUDES, help="Glob(s) to exclude")
    args = ap.parse_args()

    root_abs = os.path.abspath(args.root)
    files = discover(root_abs, args.include, args.exclude)
    if not files:
        print("No Python files found. Check --root and include/exclude patterns.", file=sys.stderr)
        sys.exit(1)

    rnd = random.Random(args.seed)
    rnd.shuffle(files)
    chosen = files[: max(0, args.k)]

    items = []
    for abs_path in chosen:
        rel = os.path.relpath(abs_path, root_abs)
        parts = pathlib.Path(rel).parts
        project = parts[0] if parts else ""
        # textual ID for readability; execution will use numeric index
        textual_id = rel
        items.append({
            "id": textual_id,
            "project": project,
            "rel_path": rel,
            "abs_path": abs_path,
        })

    out_obj = {
        "dataset": "dypybench",
        "created": datetime.datetime.utcnow().replace(microsecond=0).isoformat() + "Z",
        "root": root_abs,
        "count": len(items),
        "items": items,
    }

    os.makedirs(os.path.dirname(args.out), exist_ok=True)
    with open(args.out, "w", encoding="utf-8") as f:
        json.dump(out_obj, f, indent=2, ensure_ascii=False)

    print(f"[OK] wrote {args.out} with {len(items)} items (from {len(files):,} discovered)")

if __name__ == "__main__":
    main()
