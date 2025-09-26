"""DyPyBench HF sample: 39/pypdf/_page_labels.py (row 8468)"""

import sys
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

def number2uppercase_roman_numeral(num: int) -> str:
    roman = [
        (1000, "M"),
        (900, "CM"),
        (500, "D"),
        (400, "CD"),
        (100, "C"),
        (90, "XC"),
        (50, "L"),
        (40, "XL"),
        (10, "X"),
        (9, "IX"),
        (5, "V"),
        (4, "IV"),
        (1, "I"),
    ]

    def roman_num(num: int) -> Iterator[str]:
        for decimal, roman_repr in roman:
            x, _ = divmod(num, decimal)
            yield roman_repr * x
            num -= decimal * x
            if num <= 0:
                break

    return "".join([a for a in roman_num(num)])
