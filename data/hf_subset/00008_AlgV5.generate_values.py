"""DyPyBench HF sample: 39/pypdf/_encryption.py (row 8550)"""

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

def generate_values(
        user_password: bytes,
        owner_password: bytes,
        key: bytes,
        p: int,
        metadata_encrypted: bool,
    ) -> Dict[Any, Any]:
        u_value, ue_value = AlgV5.compute_U_value(user_password, key)
        o_value, oe_value = AlgV5.compute_O_value(owner_password, key, u_value)
        perms = AlgV5.compute_Perms_value(key, p, metadata_encrypted)
        return {
            "/U": u_value,
            "/UE": ue_value,
            "/O": o_value,
            "/OE": oe_value,
            "/Perms": perms,
        }
