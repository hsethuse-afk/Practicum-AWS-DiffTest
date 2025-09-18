from .contracts import TargetPair


class DiffPairer:
    """
    Early-stage: no real diffing. Just accept two file paths and a known entrypoint.
    Later you can swap this for a Git-based pairer without touching callers.
    """

    def pair(
        self, file_a: str, file_b: str, func_name: str
    ) -> TargetPair:
        return TargetPair(
            file_a=file_a, file_b=file_b, func_name=func_name
        )
