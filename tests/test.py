# tests/test.py
from __future__ import annotations
import sys
from pathlib import Path

# Ensure the parent dir that contains 'rightTyperTests/' is on sys.path
# File is .../rightTyperTests/tests/test.py
# parents[0] -> .../rightTyperTests/tests
# parents[1] -> .../rightTyperTests
# parents[2] -> .../(parent that contains 'rightTyperTests')
PKG_PARENT = Path(__file__).resolve().parents[2]
if str(PKG_PARENT) not in sys.path:
    sys.path.insert(0, str(PKG_PARENT))

# Now do the “import the module, then from xxx import a” pattern
try:
    import rightTyperTests  # simulate "module present" gate (like Django does)
except ImportError as e:
    raise RuntimeError(
        "Package 'rightTyperTests' not importable. "
        "Check your repo layout or adjust the sys.path bootstrap above."
    ) from e
else:
    from rightTyperTests.a import split_words


def check(candidate):

    assert candidate("Hello world!") == ["Hello", "world!"]
    assert candidate("Hello,world!") == ["Hello", "world!"]
    assert candidate("Hello world,!") == ["Hello", "world,!"]
    assert candidate("Hello,Hello,world !") == [
        "Hello,Hello,world",
        "!",
    ]
    assert candidate("abcdef") == 3
    assert candidate("aaabb") == 2
    assert candidate("aaaBb") == 1
    assert candidate("") == 0


check(split_words)
print("testDone")
