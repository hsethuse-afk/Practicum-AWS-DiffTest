"""DyPyBench HF sample: 26/seaborn/categorical.py (row 6455)"""

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

def draw_quartiles(self, ax, data, support, density, center, split=False):
        """Draw the quartiles as lines at width of density."""
        q25, q50, q75 = np.percentile(data, [25, 50, 75])

        self.draw_to_density(ax, center, q25, support, density, split,
                             linewidth=self.linewidth,
                             dashes=[self.linewidth * 1.5] * 2)
        self.draw_to_density(ax, center, q50, support, density, split,
                             linewidth=self.linewidth,
                             dashes=[self.linewidth * 3] * 2)
        self.draw_to_density(ax, center, q75, support, density, split,
                             linewidth=self.linewidth,
                             dashes=[self.linewidth * 1.5] * 2)
