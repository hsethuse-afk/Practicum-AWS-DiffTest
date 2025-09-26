"""DyPyBench HF sample: 20/thefuck/rules/pacman_invalid_option.py (row 4415)"""

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

def match(command):
    return command.output.startswith("error: invalid option '-") and any(
        " -{}".format(option) in command.script for option in "surqfdvt"
    )
