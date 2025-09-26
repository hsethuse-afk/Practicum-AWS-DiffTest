"""DyPyBench HF sample: 35/blinker/base.py (row 7765)"""

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

def _disconnect(self, receiver_id, sender_id):
        if sender_id == ANY_ID:
            if self._by_receiver.pop(receiver_id, False):
                for bucket in self._by_sender.values():
                    bucket.discard(receiver_id)
            self.receivers.pop(receiver_id, None)
        else:
            self._by_sender[sender_id].discard(receiver_id)
            self._by_receiver[receiver_id].discard(sender_id)
