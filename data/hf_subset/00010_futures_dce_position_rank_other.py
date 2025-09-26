"""DyPyBench HF sample: 25/akshare/futures/cot.py (row 5520)"""

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

def futures_dce_position_rank_other(date: str = "20160104"):
    date = (
        cons.convert_date(date) if date is not None else datetime.date.today()
    )
    if date.strftime("%Y%m%d") not in calendar:
        warnings.warn("%s非交易日" % date.strftime("%Y%m%d"))
        return {}
    url = (
        "http://www.dce.com.cn/publicweb/quotesdata/memberDealPosiQuotes.html"
    )
    payload = {
        "memberDealPosiQuotes.variety": "c",
        "memberDealPosiQuotes.trade_type": "0",
        "year": date.year,
        "month": date.month - 1,
        "day": date.day,
        "contract.contract_id": "all",
        "contract.variety_id": "c",
        "contract": "",
    }
    r = requests.post(url, data=payload)
    soup = BeautifulSoup(r.text, "lxml")
    symbol_list = [
        item["onclick"].strip("javascript:setVariety(").strip("');")
        for item in soup.find_all(attrs={"class": "selBox"})[-3].find_all(
            "input"
        )
    ]
    big_df = dict()
    for symbol in symbol_list:
        payload = {
            "memberDealPosiQuotes.variety": symbol,
            "memberDealPosiQuotes.trade_type": "0",
            "year": date.year,
            "month": date.month - 1,
            "day": date.day,
            "contract.contract_id": "all",
            "contract.variety_id": symbol,
            "contract": "",
        }
        r = requests.post(url, data=payload)
        soup = BeautifulSoup(r.text, "lxml")
        contract_list = [
            item["onclick"].strip("javascript:setContract_id('").strip("');")
            for item in soup.find_all(attrs={"name": "contract"})
        ]
        if contract_list:
            if len(contract_list[0]) == 4:
                contract_list = [symbol + item for item in contract_list]
                for contract in contract_list:
                    payload = {
                        "memberDealPosiQuotes.variety": symbol,
                        "memberDealPosiQuotes.trade_type": "0",
                        "year": date.year,
                        "month": date.month - 1,
                        "day": date.day,
                        "contract.contract_id": contract,
                        "contract.variety_id": symbol,
                        "contract": "",
                    }
                    r = requests.post(url, data=payload)
                    temp_df = pd.read_html(r.text)[1].iloc[:-1, :]
                    temp_df.columns = [
                        "rank",
                        "vol_party_name",
                        "vol",
                        "vol_chg",
                        "_",
                        "long_party_name",
                        "long_open_interest",
                        "long_open_interest_chg",
                        "_",
                        "short_party_name",
                        "short_open_interest",
                        "short_open_interest_chg",
                    ]
                    temp_df["variety"] = symbol.upper()
                    temp_df["symbol"] = contract
                    temp_df = temp_df[
                        [
                            "long_open_interest",
                            "long_open_interest_chg",
                            "long_party_name",
                            "rank",
                            "short_open_interest",
                            "short_open_interest_chg",
                            "short_party_name",
                            "vol",
                            "vol_chg",
                            "vol_party_name",
                            "symbol",
                            "variety",
                        ]
                    ]
                    big_df[contract] = temp_df
    return big_df
