"""DyPyBench HF sample: 2/PathTracking/cgmres_nmpc/cgmres_nmpc.py (row 364)"""

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

def plot_figures(plant_system, controller, iteration_num,
                 dt):  # pragma: no cover
    # figure
    # time history
    fig_p = plt.figure()
    fig_u = plt.figure()
    fig_f = plt.figure()

    # trajectory
    fig_t = plt.figure()
    fig_trajectory = fig_t.add_subplot(111)
    fig_trajectory.set_aspect('equal')

    x_1_fig = fig_p.add_subplot(411)
    x_2_fig = fig_p.add_subplot(412)
    x_3_fig = fig_p.add_subplot(413)
    x_4_fig = fig_p.add_subplot(414)

    u_1_fig = fig_u.add_subplot(411)
    u_2_fig = fig_u.add_subplot(412)
    dummy_1_fig = fig_u.add_subplot(413)
    dummy_2_fig = fig_u.add_subplot(414)

    raw_1_fig = fig_f.add_subplot(311)
    raw_2_fig = fig_f.add_subplot(312)
    f_fig = fig_f.add_subplot(313)

    x_1_fig.plot(np.arange(iteration_num) * dt, plant_system.history_x)
    x_1_fig.set_xlabel("time [s]")
    x_1_fig.set_ylabel("x")

    x_2_fig.plot(np.arange(iteration_num) * dt, plant_system.history_y)
    x_2_fig.set_xlabel("time [s]")
    x_2_fig.set_ylabel("y")

    x_3_fig.plot(np.arange(iteration_num) * dt, plant_system.history_yaw)
    x_3_fig.set_xlabel("time [s]")
    x_3_fig.set_ylabel("yaw")

    x_4_fig.plot(np.arange(iteration_num) * dt, plant_system.history_v)
    x_4_fig.set_xlabel("time [s]")
    x_4_fig.set_ylabel("v")

    u_1_fig.plot(np.arange(iteration_num - 1) * dt, controller.history_u_1)
    u_1_fig.set_xlabel("time [s]")
    u_1_fig.set_ylabel("u_a")

    u_2_fig.plot(np.arange(iteration_num - 1) * dt, controller.history_u_2)
    u_2_fig.set_xlabel("time [s]")
    u_2_fig.set_ylabel("u_omega")

    dummy_1_fig.plot(np.arange(iteration_num - 1) *
                     dt, controller.history_dummy_u_1)
    dummy_1_fig.set_xlabel("time [s]")
    dummy_1_fig.set_ylabel("dummy u_1")

    dummy_2_fig.plot(np.arange(iteration_num - 1) *
                     dt, controller.history_dummy_u_2)
    dummy_2_fig.set_xlabel("time [s]")
    dummy_2_fig.set_ylabel("dummy u_2")

    raw_1_fig.plot(np.arange(iteration_num - 1) * dt, controller.history_raw_1)
    raw_1_fig.set_xlabel("time [s]")
    raw_1_fig.set_ylabel("raw_1")

    raw_2_fig.plot(np.arange(iteration_num - 1) * dt, controller.history_raw_2)
    raw_2_fig.set_xlabel("time [s]")
    raw_2_fig.set_ylabel("raw_2")

    f_fig.plot(np.arange(iteration_num - 1) * dt, controller.history_f)
    f_fig.set_xlabel("time [s]")
    f_fig.set_ylabel("optimal error")

    fig_trajectory.plot(plant_system.history_x,
                        plant_system.history_y, "-r")
    fig_trajectory.set_xlabel("x [m]")
    fig_trajectory.set_ylabel("y [m]")
    fig_trajectory.axis("equal")

    # start state
    plot_car(plant_system.history_x[0],
             plant_system.history_y[0],
             plant_system.history_yaw[0],
             controller.history_u_2[0],
             )

    # goal state
    plot_car(0.0, 0.0, 0.0, 0.0)

    plt.show()
