"""DyPyBench HF sample: 6/supervisor/supervisorctl.py (row 1880)"""

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

def check_encoding(ctl):
    problematic_enc = not_all_langs()
    if problematic_enc:
        ctl.output('Warning: sys.stdout.encoding is set to %s, so Unicode '
                   'output may fail. Check your LANG and PYTHONIOENCODING '
                   'environment settings.' % problematic_enc)
