"""DyPyBench HF sample: 31/geopy/geocoders/algolia.py (row 7363)"""

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

def _parse_json(self, response, exactly_one, language):
        if response is None or 'hits' not in response:
            return None
        features = response['hits']
        if not len(features):
            return None
        if exactly_one:
            return self._parse_feature(features[0], language=language)
        else:
            return [
                self._parse_feature(feature, language=language) for feature in features
            ]
