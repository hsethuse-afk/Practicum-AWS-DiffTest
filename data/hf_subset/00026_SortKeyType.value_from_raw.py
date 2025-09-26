"""DyPyBench HF sample: 40/lektor/types/special.py (row 9991)"""

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

def value_from_raw(self, raw):
        if raw.value is None:
            return raw.missing_value("Missing sort key")
        try:
            return int(raw.value.strip())
        except ValueError:
            return raw.bad_value("Bad sort key value")
