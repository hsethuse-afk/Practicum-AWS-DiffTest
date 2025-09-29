from typing import List


def separate_paren_groups(paren_string: str) -> List[str]:
    """ Input to this function is a string containing multiple groups of nested parentheses. Your goal is to
    separate those group into separate strings and return the list of those.
    Separate groups are balanced (each open brace is properly closed) and not nested within each other
    Ignore any spaces in the input string.
    >>> separate_paren_groups('( ) (( )) (( )( ))')
    ['()', '(())', '(()())']
    """
    # Remove all whitespace characters
    s = ''.join(ch for ch in paren_string if not ch.isspace())

    groups: List[str] = []
    curr: List[str] = []
    balance = 0

    for ch in s:
        if ch not in '()':
            # Ignore any non-parenthesis characters (spec states only spaces should be ignored,
            # but tolerate other characters by skipping them)
            continue

        if ch == '(':
            balance += 1
            curr.append(ch)
        else:  # ch == ')'
            if balance == 0:
                raise ValueError("Unbalanced parentheses: too many closing parentheses")
            curr.append(ch)
            balance -= 1

        # If we've closed a top-level group, save it
        if balance == 0 and curr:
            groups.append(''.join(curr))
            curr = []

    if balance != 0:
        raise ValueError("Unbalanced parentheses: too many opening parentheses")

    return groups
