"""DyPyBench HF sample: 10/src/click/formatting.py (row 2947)"""

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

def indent(self) -> None:
        """Increases the indentation."""
        self.current_indent += self.indent_increment
