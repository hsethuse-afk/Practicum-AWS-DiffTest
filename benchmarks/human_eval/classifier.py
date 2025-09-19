import json, sys, inspect, typing

# Change this if you want to require BOTH param and return annotations.
REQUIRE_BOTH = False  # True => must have at least one param annotation AND a return annotation


def type_to_str(t):
    # Try to make annotations readable
    try:
        return (
            typing.get_origin(t).__name__
            if typing.get_origin(t)
            else getattr(t, "__name__", str(t))
        )
    except Exception:
        return str(t)


def build_signature_str(fn, hints: dict) -> str:
    sig = inspect.signature(fn)
    parts = []
    for name, p in sig.parameters.items():
        ann = ""
        if name in hints:
            ann = f": {type_to_str(hints[name])}"
        # include * / ** markers based on kind
        if p.kind is inspect.Parameter.VAR_POSITIONAL:
            param_str = f"*{name}{ann}"
        elif p.kind is inspect.Parameter.VAR_KEYWORD:
            param_str = f"**{name}{ann}"
        elif (
            p.kind is inspect.Parameter.KEYWORD_ONLY
            and "*" not in parts
        ):
            # inject bare * if needed
            parts.append("*")
            param_str = f"{name}{ann}"
        else:
            param_str = f"{name}{ann}"
        parts.append(param_str)

    params = ", ".join(parts)
    ret = ""
    if "return" in hints:
        ret = f" -> {type_to_str(hints['return'])}"
    return f"def {fn.__name__}({params}){ret}"


def has_param_annotation(hints: dict) -> bool:
    return any(k != "return" for k in hints)


def process_obj(obj) -> bool:
    task_id = obj.get("task_id", "")
    entry = obj.get("entry_point", "")
    prompt = obj.get("prompt", "")
    sol = obj.get("canonical_solution", "")

    # Build full source. HumanEval canonical_solution is indented as a body.
    src = prompt + sol

    # Execute in its own module-like dict so imports in prompt (e.g., typing) work.
    mod = {}
    try:
        exec(src, mod)
    except Exception as e:
        # Skip malformed entries
        return

    fn = mod.get(entry)
    if not callable(fn):
        return

    # Resolve type hints (handles forward refs & typing aliases)
    try:
        hints = typing.get_type_hints(fn, globalns=mod, localns=mod)
    except Exception:
        # Fallback to raw __annotations__ if resolution fails
        hints = getattr(fn, "__annotations__", {}) or {}

    param_ok = has_param_annotation(hints)
    ret_ok = "return" in hints
    ok = (param_ok and ret_ok) if REQUIRE_BOTH else (param_ok or ret_ok)

    if ok:
        print(f"{task_id} : {build_signature_str(fn, hints)}")
        return True
    return False


if __name__ == "__main__":
    path = (
        sys.argv[1]
        if len(sys.argv) > 1
        else "./benchmarks/human_eval/human_eval.jsonl"
    )
    count = 0
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            obj = json.loads(line)
            if process_obj(obj):
                count += 1
    print(f"{count} functions have typehints")
