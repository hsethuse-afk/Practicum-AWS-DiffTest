import json, os


def extract_task(
    jsonl_path: str,
    task_id: str,
    out_path: str = None,
) -> str:
    """
    Extract a HumanEval task's canonical solution and save as a .py file.

    Args:
        jsonl_path: Path to HumanEval .jsonl file
        task_id: The task_id to extract (e.g., "HumanEval/0")
        out_path: Optional output path for the .py file (defaults to <entry_point>.py)

    Returns:
        The path to the written .py file
    """
    print(f"privided path is {jsonl_path}")
    with open(jsonl_path, "r", encoding="utf-8") as f:
        for line in f:
            if not line.strip():
                continue
            obj = json.loads(line)
            if obj.get("task_id") == task_id:
                completion = obj.get("completion", "")
                prompt = obj.get("prompt", "")
                canon = obj.get("canonical_solution", "")
                entry = obj.get("entry_point", "solution")
                src = ""
                if completion:
                    src = completion
                else:
                    src = prompt + canon
                out_path = out_path or f"{entry}.py"

                os.makedirs(
                    os.path.dirname(out_path) or ".", exist_ok=True
                )
                with open(
                    out_path, "w", encoding="utf-8", newline="\n"
                ) as out:
                    out.write(src if src.endswith("\n") else src + "\n")

                return out_path

    raise ValueError(f"Task id not found: {task_id}")


def extract_entry(
    jsonl_path: str,
    task_id: str,
) -> str:
    with open(jsonl_path, "r", encoding="utf-8") as f:
        for line in f:
            if not line.strip():
                continue
            obj = json.loads(line)
            if obj.get("task_id") == task_id:
                entry = obj.get("entry_point", "")
                return entry
    return ""
