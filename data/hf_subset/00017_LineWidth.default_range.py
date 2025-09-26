"""DyPyBench HF sample: 26/seaborn/_core/properties.py (row 6654)"""

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

def default_range(self) -> tuple[float, float]:
        """Min and max values used by default for semantic mapping."""
        base = mpl.rcParams["lines.linewidth"]
        return base * .5, base * 2
