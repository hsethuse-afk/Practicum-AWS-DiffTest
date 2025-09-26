"""DyPyBench HF sample: 40/lektor/devcli.py (row 9712)"""

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

def publish_plugin_cmd():
    """Publishes the current version of the plugin in the current folder.

    This generally requires that your setup.py has at least the bare minimum
    configuration for valid publishing to PyPI.
    """
    info = ensure_plugin()
    for key in "author", "author_email", "license", "url":
        if not info[key]:
            raise click.UsageError(
                "Cannot publish plugin without setting " '"%s" in setup.py.' % key
            )
    register_package(info["path"])
    publish_package(info["path"])
