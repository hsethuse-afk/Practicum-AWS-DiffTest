"""DyPyBench HF sample: 2/PathPlanning/GridBasedSweepCPP/grid_based_sweep_coverage_path_planner.py (row 827)"""

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

def convert_grid_coordinate(ox, oy, sweep_vec, sweep_start_position):
    tx = [ix - sweep_start_position[0] for ix in ox]
    ty = [iy - sweep_start_position[1] for iy in oy]
    th = math.atan2(sweep_vec[1], sweep_vec[0])
    converted_xy = np.stack([tx, ty]).T @ rot_mat_2d(th)

    return converted_xy[:, 0], converted_xy[:, 1]
