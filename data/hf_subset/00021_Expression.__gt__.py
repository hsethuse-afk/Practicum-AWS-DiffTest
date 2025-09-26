"""DyPyBench HF sample: 40/lektor/db.py (row 9468)"""

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

def __gt__(self, other):
        return _BinExpr(self, _auto_wrap_expr(other), operator.gt)
