#!/usr/bin/env python3
"""
HumanEval-style runner for DyPyBench via Hugging Face (auto-prep + RightTyper).

Usage examples:
  # first run auto-fetches ~30 items, then runs one:
  python scripts/run_db_taskid.py --t DyPyBench/10

  # run a range
  python scripts/run_db_taskid.py --t DyPyBench/0-29

  # run them all
  python scripts/run_db_taskid.py --t DyPyBench/ALL

Options:
  --k 30           # how many items to fetch on first prep
  --seed 13        # sampling seed
  --json ...       # dataset JSON (auto-created if missing)
  --files_dir ...  # where .py files are written on prep
  --binary ...     # RightTyper CLI path/name (default: righttyper)
  --timeout 60     # per-file timeout seconds
  --force_prep     # force re-fetch from HF and overwrite JSON
  --hf_name ...    # HF dataset name (default: claudios/dypybench_functions)
  --split train    # HF split
"""
from __future__ import annotations

import argparse
import datetime as _dt
import json
import os
import pathlib
import random
import re
import shutil
import subprocess
import sys
import time
from typing import List

# ---------- Defaults ----------
DEFAULT_JSON = "data/datasets/dypybench_hf_subset.json"
DEFAULT_FILES_DIR = "data/hf_subset"
DEFAULT_HF_NAME = "claudios/dypybench_functions"
DEFAULT_SPLIT = "train"


# ---------- Helpers ----------
def _ensure_dirs(*paths: str) -> None:
    for p in paths:
        if p:
            os.makedirs(p, exist_ok=True)


def _to_str(x) -> str:
    if isinstance(x, str):
        return x
    if x is None:
        return ""
    try:
        return str(x)
    except Exception:
        return ""


def _coalesce(*vals) -> str:
    for v in vals:
        s = _to_str(v).strip()
        if s:
            return s
    return ""


def _sanitize(name: str) -> str:
    name = (name or "").strip().replace(" ", "_")
    return re.sub(r"[^A-Za-z0-9._-]+", "_", name)[:80] or "item"


def _wrap_if_needed(src: str) -> str:
    """
    Ensure the emitted file is valid Python:
    - if empty -> minimal stub
    - if starts with 'def ' or 'class ' -> add common imports and keep as is
    - else wrap inside a function so parsing succeeds
    """
    s = (_to_str(src)).strip("\n")
    if not s.strip():
        return "def _empty():\n    pass\n"

    # Common imports that are likely needed for DyPyBench functions
    common_imports = """import sys
import os
import datetime
import warnings
import json
import re
from typing import Any, Dict, List, Optional, Union
try:
    import pandas as pd
except ImportError:
    pd = None
try:
    import requests
except ImportError:
    requests = None
try:
    from bs4 import BeautifulSoup
except ImportError:
    BeautifulSoup = None
try:
    import numpy as np
except ImportError:
    np = None

"""

    sl = s.lstrip()
    if sl.startswith("def ") or sl.startswith("class "):
        return common_imports + s + ("\n" if not s.endswith("\n") else "")

    # Wrap non-def content in a function
    body_lines = [("    " + line if line.strip() else "    pass") for line in s.splitlines()]
    body = "\n".join(body_lines) or "    pass"
    return common_imports + f"def _hf_sample():\n{body}\n"


def _parse_target(spec: str, total: int) -> List[int]:
    """
    Accepts:
      DyPyBench/10
      DyPyBench/0-29
      DyPyBench/ALL
    Returns a list of indices (0-based).
    """
    if "/" not in spec:
        raise ValueError("Use format DyPyBench/<N>, DyPyBench/<A-B>, or DyPyBench/ALL")
    suite, tail = spec.split("/", 1)
    if suite.lower() != "dypybench":
        raise ValueError("Suite must be 'DyPyBench'")

    tail_u = tail.strip().upper()
    if tail_u == "ALL":
        return list(range(total))

    if "-" in tail_u:
        a, b = tail_u.split("-", 1)
        a, b = a.strip(), b.strip()
        if not (a.isdigit() and b.isdigit()):
            raise ValueError("Range must be integers like DyPyBench/0-29")
        start, end = int(a), int(b)
        if start < 0 or end < 0 or start > end or end >= total:
            raise IndexError(f"Range out of bounds: 0 <= start <= end < {total}")
        return list(range(start, end + 1))
    else:
        if not tail_u.isdigit():
            raise ValueError("Index must be an integer like DyPyBench/10")
        idx = int(tail_u)
        if idx < 0 or idx >= total:
            raise IndexError(f"Index out of bounds: 0 <= idx < {total}")
        return [idx]


def _run_righttyper_cli(binary: str, src_path: str, timeout: int) -> dict:
    """
    Run RightTyper CLI on the given file to generate type annotations.
    Uses --output-files to generate annotated versions and --verbose for details.
    """
    t0 = time.perf_counter()
    try:
        # Create output directory for annotated files
        output_dir = os.path.join(os.path.dirname(src_path), "annotated")
        _ensure_dirs(output_dir)

        # Copy file to output directory so RightTyper can modify it
        output_file = os.path.join(output_dir, os.path.basename(src_path))
        shutil.copy2(src_path, output_file)

        proc = subprocess.run(
            [binary, "--output-files", "--overwrite", "--verbose", output_file],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            timeout=timeout,
        )
        elapsed = time.perf_counter() - t0

        # Read the annotated file if it exists
        annotated_content = ""
        if os.path.exists(output_file):
            try:
                with open(output_file, "r", encoding="utf-8") as f:
                    annotated_content = f.read()
            except Exception as e:
                annotated_content = f"Error reading annotated file: {e}"

        return {
            "success": proc.returncode == 0,
            "elapsed_sec": round(elapsed, 4),
            "annotated_content": annotated_content if proc.returncode == 0 else None,
            "error_message": proc.stderr[-1000:].strip() if proc.returncode != 0 else None,
        }
    except subprocess.TimeoutExpired:
        elapsed = time.perf_counter() - t0
        return {"success": False, "elapsed_sec": round(elapsed, 4), "error": "timeout"}


def _prep_from_hf(
    *,
    k: int,
    seed: int,
    out_json: str,
    files_dir: str,
    hf_name: str = DEFAULT_HF_NAME,
    split: str = DEFAULT_SPLIT,
) -> None:
    """
    Fetch ~k DyPyBench functions from Hugging Face, materialize .py files, and write one JSON manifest.
    Robust to weird field types (ints/None).
    """
    try:
        from datasets import load_dataset
    except Exception:
        print(
            "The 'datasets' package is required for Hugging Face fetch.\n"
            "Install it with:  pip install datasets",
            file=sys.stderr,
        )
        sys.exit(1)

    print(f"[prep] Loading HF dataset {hf_name}:{split} …")
    ds = load_dataset(hf_name, split=split)
    n = len(ds)
    if n == 0:
        print("[prep] Dataset is empty.", file=sys.stderr)
        sys.exit(1)

    k = max(0, min(k, n))
    idxs = list(range(n))
    random.Random(seed).shuffle(idxs)
    idxs = idxs[:k]

    files_root = os.path.abspath(files_dir)
    _ensure_dirs(files_root)

    items = []
    for i, row_idx in enumerate(idxs):
        row = ds[row_idx]

        # Safely pull fields (coerce to string, provide fallbacks)
        project = _coalesce(row.get("project"), row.get("nwo"), row.get("repo"), "unknown")
        rel_path_meta = _coalesce(row.get("path"), row.get("filepath"), row.get("file"), row.get("url"))
        identifier_raw = _coalesce(row.get("identifier"), pathlib.Path(rel_path_meta).stem, f"fn_{row_idx}")
        identifier = _sanitize(identifier_raw)

        # Function/source content
        func_src_raw = _coalesce(row.get("function"), row.get("code"), row.get("source"))
        func_src = _wrap_if_needed(func_src_raw)

        # Write a standalone .py
        header = f'"""DyPyBench HF sample: {project}/{rel_path_meta} (row {row_idx})"""\n\n'
        fname = f"{i:05d}_{identifier}.py"
        abs_path = os.path.join(files_root, fname)
        with open(abs_path, "w", encoding="utf-8") as f:
            f.write(header)
            f.write(func_src)

        items.append(
            {
                "id": f"{i:05d}_{identifier}",
                "project": project,
                "rel_path": fname,  # relative to files_root
                "abs_path": abs_path,  # runner uses this path
                "meta": {
                    "hf_name": hf_name,
                    "split": split,
                    "row_index": int(row_idx),
                    "source_rel_path": rel_path_meta,
                    "identifier": identifier,
                },
            }
        )

    out = {
        "dataset": "dypybench_hf",
        "created": _dt.datetime.utcnow().replace(microsecond=0).isoformat() + "Z",
        "root": files_root,
        "count": len(items),
        "items": items,
    }

    _ensure_dirs(os.path.dirname(out_json))
    with open(out_json, "w", encoding="utf-8") as f:
        json.dump(out, f, indent=2, ensure_ascii=False)

    print(f"[prep] Wrote {out_json} with {len(items)} items")
    print(f"[prep] Wrote .py files under {files_root}")


# ---------- Main ----------
def main():
    ap = argparse.ArgumentParser(
        description="HumanEval-style runner for DyPyBench via Hugging Face (auto-prep + RightTyper)."
    )
    ap.add_argument("--t", required=True, help="DyPyBench/N, DyPyBench/A-B, or DyPyBench/ALL")
    ap.add_argument("--json", default=DEFAULT_JSON, help="Dataset JSON (auto-created if missing)")
    ap.add_argument("--files_dir", default=DEFAULT_FILES_DIR, help="Where .py files are written on prep")
    ap.add_argument("--k", type=int, default=30, help="How many items to fetch on first prep")
    ap.add_argument("--seed", type=int, default=13, help="Sampling seed for prep")
    ap.add_argument("--binary", default="righttyper", help="RightTyper CLI binary")
    ap.add_argument("--timeout", type=int, default=60, help="Per-file timeout seconds")
    ap.add_argument("--force_prep", action="store_true", help="Force re-fetch from HF and overwrite JSON")
    ap.add_argument("--hf_name", default=DEFAULT_HF_NAME, help="Hugging Face dataset name")
    ap.add_argument("--split", default=DEFAULT_SPLIT, help="Hugging Face split")
    args = ap.parse_args()

    # Prepare JSON if needed
    need_prep = args.force_prep or (not os.path.isfile(args.json))
    if need_prep:
        _prep_from_hf(
            k=args.k,
            seed=args.seed,
            out_json=args.json,
            files_dir=args.files_dir,
            hf_name=args.hf_name,
            split=args.split,
        )

    # Load dataset
    with open(args.json, "r", encoding="utf-8") as f:
        data = json.load(f)
    items = data.get("items", [])
    total = len(items)
    if total == 0:
        print("Dataset has no items. Re-run with --force_prep or check your JSON.", file=sys.stderr)
        sys.exit(1)

    # Parse target
    try:
        indices = _parse_target(args.t, total)
    except Exception as e:
        print(f"Bad --t '{args.t}': {e}", file=sys.stderr)
        sys.exit(1)

    # Output path
    ts = _dt.datetime.now().strftime("%Y%m%d-%H%M%S")
    out_path = f"results/smoke/righttyper_smoke-{ts}.jsonl"
    _ensure_dirs(os.path.dirname(out_path))

    # Check RightTyper
    if shutil.which(args.binary) is None:
        print(
            f"ERROR: RightTyper CLI '{args.binary}' not found on PATH.\n"
            f"Set --binary /path/to/righttyper if needed.",
            file=sys.stderr,
        )
        sys.exit(1)

    # Run
    ok = fail = 0
    with open(out_path, "w", encoding="utf-8") as fout:
        for i in indices:
            item = items[i]
            src = item.get("abs_path") or os.path.join(data.get("root", ""), item.get("rel_path", ""))
            basic_info = {
                "id": item.get("id", ""),
                "success": False,
                "elapsed_sec": 0,
            }
            res = _run_righttyper_cli(args.binary, src, args.timeout)

            # Create clean output
            row = {
                "id": basic_info["id"],
                "success": res.get("success", False),
                "elapsed_sec": res.get("elapsed_sec", 0),
                "annotated_content": res.get("annotated_content"),
                "error_message": res.get("error_message"),
            }
            fout.write(json.dumps(row, ensure_ascii=False) + "\n")
            print(f"[{i}/{total-1}] {'OK' if res.get('success') else 'FAIL'} — {item.get('rel_path', '')}")
            if res.get("success"):
                ok += 1
            else:
                fail += 1

    print(f"\n[RightTyper] success={ok}  fail={fail}  total={ok+fail}")
    print(f"[RightTyper] results → {out_path}")


if __name__ == "__main__":
    main()
