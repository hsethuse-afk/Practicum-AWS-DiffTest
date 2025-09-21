from typing import List


def parse_nested_parens(paren_string: str) -> List[int]:
    """ Input to this function is a string represented multiple groups for nested parentheses separated by spaces.
    For each of the group, output the deepest level of nesting of parentheses.
    E.g. (()()) has maximum two levels of nesting while ((())) has three.

    >>> parse_nested_parens('(()()) ((())) () ((())()())')
    [2, 3, 1, 3]
    """
    if not paren_string:
        return []

    depths: List[int] = []
    # Split on any whitespace, ignore empty tokens
    groups = paren_string.strip().split()
    for group in groups:
        if group == "":
            continue
        curr = 0
        max_depth = 0
        for ch in group:
            if ch == "(":
                curr += 1
                if curr > max_depth:
                    max_depth = curr
            elif ch == ")":
                curr -= 1
                if curr < 0:
                    raise ValueError(f"Unbalanced parentheses in group: {group}")
            else:
                # unexpected character
                raise ValueError(f"Invalid character '{ch}' in group: {group}")
        if curr != 0:
            raise ValueError(f"Unbalanced parentheses in group: {group}")
        depths.append(max_depth)

    return depths
