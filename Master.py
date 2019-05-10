# -*- coding: utf-8 -*-
"""
Created on Mon May  6 14:59:45 2019

@author: seery
"""
import sys
import os
import re
import copy
import warnings
import datetime as dt

import itertools
import math
import functools

#from PyQt5.QtWidgets import QMainWindow, QAction, QDockWidget, QWidget, QVBoxLayout, QApplication, QDesktopWidget, QGridLayout, QTreeWidget, QPushButton, QTreeWidgetItem, QStyle, QSizePolicy, QLabel, QLineEdit, QCheckBox, QDialog, QTabWidget
from PyQt5.QtWidgets import *
from PyQt5.QtGui import QIcon
from PyQt5.QtCore import QCoreApplication, Qt, QObject

import numpy as np
import pandas as pd
import matplotlib as mpl
import matplotlib.dates as mdates
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec
#from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas


if 'app' not in locals():
    app = QCoreApplication.instance()
if app is None:  # otherwise kernel dies
    app = QApplication(sys.argv)
X = Telemetry_Grapher()#groups, data_dict)
app.exec_()