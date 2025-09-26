"""DyPyBench HF sample: 25/akshare/stock_feature/stock_hot_tgb.py (row 5291)"""

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

def stock_hot_tgb() -> pd.DataFrame:
    """
    淘股吧-热门股票
    https://www.taoguba.com.cn/stock/moreHotStock
    :return: 热门股票
    :rtype: pandas.DataFrame
    """
    url = "https://www.taoguba.com.cn/stock/moreHotStock"
    r = requests.get(url)
    temp_df = pd.concat([pd.read_html(r.text, header=0)[0], pd.read_html(r.text, header=0)[1]])
    temp_df = temp_df[[
        "个股代码",
        "个股名称",
    ]]
    temp_df.reset_index(inplace=True, drop=True)
    return temp_df
