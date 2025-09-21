"""
Function extraction utilities for differential testing.

This module provides utilities to extract and build functions from code strings,
particularly useful for processing JSONL results with completions and canonical solutions.
"""

import ast
import types
import re
from typing import Callable, Optional


def load_jsonl(path: str):
    """Load JSONL file with results"""
    import json
    with open(path, 'r') as f:
        return [json.loads(line) for line in f if line.strip()]


def extract_function_from_code(code: str, function_name: Optional[str] = None) -> Optional[Callable]:
    """Execute code and return the first function found"""
    namespace = {}
    try:
        exec(code, namespace)
    except Exception:
        return None

    # If we have a specific function name, try to find it
    if function_name and function_name in namespace:
        return namespace[function_name]

    # Find first user-defined function in namespace
    for name, obj in namespace.items():
        if (callable(obj) and
            not name.startswith('_') and
            isinstance(obj, types.FunctionType) and
            obj.__module__ != 'builtins'):
            return obj
    return None


def get_function_signature_from_completion(completion: str) -> Optional[str]:
    """Extract function signature (def line) from completion"""
    lines = completion.strip().split('\n')
    for line in lines:
        if line.strip().startswith('def '):
            return line.strip()
    return None


def extract_imports_from_completion(completion: str) -> str:
    """Extract import statements from completion"""
    lines = completion.strip().split('\n')
    imports = []
    for line in lines:
        stripped = line.strip()
        if (stripped.startswith('import ') or
            stripped.startswith('from ') and ' import ' in stripped):
            imports.append(line)
        elif stripped.startswith('def '):
            break
    return '\n'.join(imports)


def build_complete_function(completion: str, signature: str, body: str) -> Optional[str]:
    """Combine imports, function signature and body to create complete function"""
    if not signature or not body:
        return None

    match = re.match(r'def\s+(\w+)', signature)
    if not match:
        return None

    # Extract imports from completion
    imports = extract_imports_from_completion(completion)

    # Build complete function
    lines = []
    if imports:
        lines.append(imports)
        lines.append('')

    if signature.endswith(':'):
        lines.append(signature)
    else:
        lines.append(signature + ':')
    lines.extend(body.split('\n'))

    return '\n'.join(lines)


def extract_function_pair_from_record(record: dict) -> tuple[Optional[Callable], Optional[Callable]]:
    """Extract both completion and canonical functions from a JSONL record"""
    completion = record.get('completion', '')
    canonical = record.get('canonical_solution', '')

    if not completion or not canonical:
        return None, None

    # Extract completion function
    comp_func = extract_function_from_code(completion)

    # Build complete canonical function
    signature = get_function_signature_from_completion(completion)
    canon_func = None
    if signature:
        complete_canonical = build_complete_function(completion, signature, canonical)
        if complete_canonical:
            canon_func = extract_function_from_code(complete_canonical)

    return comp_func, canon_func