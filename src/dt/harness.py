import importlib.util, sys, types, uuid
from typing import Callable
from .contracts import TargetPair


def _load_function_from_file(path: str, func_name: str) -> Callable:
    mod_name = f"simpledt_mod_{uuid.uuid4().hex}"
    spec = importlib.util.spec_from_file_location(mod_name, path)
    if spec is None or spec.loader is None:
        raise ImportError(f"Cannot load module from {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[mod_name] = module
    spec.loader.exec_module(module)  # type: ignore[attr-defined]
    func = getattr(module, func_name, None)
    if not callable(func):
        raise AttributeError(f"{path} has no callable '{func_name}'")
    # Ensure it's a plain function (early-stage guard)
    if not isinstance(func, types.FunctionType):
        raise TypeError(
            f"'{func_name}' in {path} is not a plain function"
        )
    return func


class HarnessBuilder:
    def build(self, target: TargetPair) -> tuple[Callable, Callable]:
        f_a = _load_function_from_file(target.file_a, target.func_name)
        f_b = _load_function_from_file(target.file_b, target.func_name)
        return f_a, f_b
