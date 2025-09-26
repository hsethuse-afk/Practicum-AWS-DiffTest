"""DyPyBench HF sample: 18/errbot/botplugin.py (row 3803)"""

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

def bot_identifier(self) -> Identifier:
        """
        Get bot identifier on current active backend.

        :return Identifier
        """
        return self._bot.bot_identifier
