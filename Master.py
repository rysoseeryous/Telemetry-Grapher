# -*- coding: utf-8 -*-
"""
Created on Mon May  6 14:59:45 2019

@author: seery
"""
import sys
import io
import csv
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
from PyQt5.QtGui import QIcon, QBrush, QColor, QStandardItemModel, QStandardItem, QKeySequence
from PyQt5.QtCore import *#QCoreApplication, Qt, QObject, QAbstractTableModel

import numpy as np
import pandas as pd
import matplotlib as mpl
import matplotlib.dates as mdates
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec
from matplotlib import colors as mcolors
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas


def gather_files_mod(path):
    """Returns dictionary {filename:path} of all files in path which match types in filetypes."""
    script_paths = []
    filelist = []
    for (dirpath, dirnames, filenames) in os.walk(path):
        filelist.extend(filenames)
    filetypes = re.compile(r'py$')
    for file in filelist:
        if file != 'Master.py':
            if re.search(filetypes, file):
                script_paths.append(file)#os.path.join(path, file))
    return script_paths

# Turn this on to run all the scripts for the first time (harder to debug when it's on)
# ie when the kernel dies. Again.

if 0:
    path = r'P:\FigureWizard'
    script_paths = gather_files_mod(path)
    for script in script_paths:
        exec(open(script).read())

if 'app' not in locals():
    app = QCoreApplication.instance()
if app is None:  # otherwise kernel dies
    app = QApplication(sys.argv)
X = Telemetry_Grapher()#groups, data_dict)
app.exec_()