# -*- coding: utf-8 -*-
"""
Created on Thu Jun 27 17:34:14 2019

@author: seery
"""
import sys
import io
import csv
import os
import re
import copy
import json
import logging
#import warnings
import datetime as dt
import itertools
import math
import functools

from PyQt5.QtWidgets import QGroupBox, QMainWindow, QAction, QColorDialog, QInputDialog, QHeaderView, QDateTimeEdit, QComboBox, QSpinBox, QDoubleSpinBox, QRadioButton, QDockWidget, QTextEdit, QMessageBox, QWidget, QVBoxLayout, QHBoxLayout, QFormLayout, QApplication, QGridLayout, QTreeWidget, QPushButton, QTreeWidgetItem, QStyle, QSizePolicy, QLabel, QLineEdit, QCheckBox, QSplitter, QDialog, QDialogButtonBox, QAbstractItemView, QTabWidget, QTableView, QTableWidgetItem, QTableWidget, QFileDialog, QListWidget, QListWidgetItem
#from PyQt5.QtWidgets import *
from PyQt5.QtGui import QIcon, QBrush, QColor, QStandardItemModel, QStandardItem, QKeySequence
from PyQt5.QtCore import QTextStream, QFile, QCoreApplication, Qt, QObject, QDateTime, QDate, QSortFilterProxyModel
#import breeze_resources

import numpy as np
import pandas as pd
import matplotlib as mpl

from matplotlib.transforms import Bbox
#from matplotlib.axes._base import _AxesBase

import matplotlib.dates as mdates
import matplotlib.pyplot as plt
from matplotlib.gridspec import GridSpec
from matplotlib import colors as mcolors
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas



x = np.linspace(0, 2*np.pi, 400)
y = np.sin(x**2)


class Restructure(QWidget):
    """Main application window."""

    def __init__(self):
        super().__init__()
#        self.resize(500,500)
        self.test_controls = Test_Controls(self)
        vbox = QVBoxLayout()
        self.axes_frame = Axes_Frame(self)
        vbox.addWidget(self.axes_frame)


        vbox.addWidget(self.test_controls)
        self.setLayout(vbox)
        self.show()


class Subplot_Manager():
    """Wrapper around subplot object (host). Keeps track of contents and settings of each subplot."""
    def __init__(self, host, order=[None], contents=None, index=None):
        self.axes = [host]  # keeps track of parasitic axes
        self.order = order  # keeps track of preferred unit order
        if contents is None:
            self.contents = []
        else:
            self.contents = contents
        self.index = index  # convenience attribute
        self.identify()

    def identify(self):
        self.host().clear()
        if self.contents:
            for c in self.contents:
                self.host().plot(*c)
        self.host().text(0.5, 0.5, str(self.index))

    def host(self):
        return self.axes[0]





class Axes_Frame(FigureCanvas):
    """Central widget in Application Base main window."""

    def __init__(self, parent):
        self.parent = parent
        self.fig = plt.figure()
        super().__init__(self.fig)

        self.gs = GridSpec(1, 1, height_ratios=[1])
        ax = self.fig.add_subplot(self.gs[0], projection='test')
        sp = Subplot_Manager(ax, index=0)
        self.subplots = [sp]
        self.current_sps = []
        self.fig.canvas.mpl_connect(
                'button_press_event', self.select)

    def select(self, event):
        tc = self.parent.test_controls
        sp = self.get_subplot(event)

        if sp:
            tc.message.setText(str(sp.index))
            self.current_sps = [sp]
#            print(sp.host().veggie)
        else:
            tc.message.setText('None')
            self.current_sps = []

    def get_subplot(self, event):
        for sp in self.subplots:
            if event.inaxes in sp.axes:
                return sp
        return None

class Test_Controls(QWidget):

    def __init__(self, parent):
        super().__init__()
        self.parent = parent

        hbox = QHBoxLayout()
        self.message = QLabel()
        hbox.addWidget(self.message)

        self.insert_button = QPushButton('Insert')
        self.insert_button.clicked.connect(self.insert)
        hbox.addWidget(self.insert_button)

        self.pop_button = QPushButton('Populate')
        self.pop_button.clicked.connect(self.populate)
        hbox.addWidget(self.pop_button)

        self.clear_button = QPushButton('Clear')
        self.clear_button.clicked.connect(self.clear)
        hbox.addWidget(self.clear_button)

        self.weights_edit = QLineEdit()
        self.weights_edit.returnPressed.connect(self.adjust_weights)
        hbox.addWidget(self.weights_edit)

        self.up_button = QPushButton('Up')
        self.up_button.clicked.connect(self.reorder)
        hbox.addWidget(self.up_button)

        self.down_button = QPushButton('Down')
        self.down_button.clicked.connect(self.reorder)
        hbox.addWidget(self.down_button)

        self.delete_button = QPushButton('Delete')
        self.delete_button.clicked.connect(self.delete)
        hbox.addWidget(self.delete_button)

        self.setLayout(hbox)


    def insert(self):
        af = self.parent.axes_frame
        if not af.current_sps: return
        i = af.current_sps[0].index
        nplots = af.gs.get_geometry()[0] + 1
        weights = af.gs.get_height_ratios()
        weights.insert(i+1, 1)
        af.gs = GridSpec(nplots, 1, height_ratios=weights)
        for j in range(nplots):
            if j == i+1:
                ax = af.fig.add_subplot(af.gs[j], projection='test')
                af.subplots.insert(j, Subplot_Manager(ax, index=j))
            else:
                sp = af.subplots[j]
                sp.host().set_position(af.gs[j].get_position(af.fig))
                sp.index = j
                sp.identify()
        af.draw()

    def populate(self):
        af = self.parent.axes_frame
        if not af.current_sps: return
        sp = af.current_sps[0]
        sp.contents.append((x,y))
        ax = sp.host()
        ax.veggie = 'pumpkin'
        sp.identify()
        af.draw()

    def clear(self):
        af = self.parent.axes_frame
        if not af.current_sps: return
        sp = af.current_sps[0]
#        test = GridSpec(10,10, height_ratios=[1,2,3,4,5,6,7,8,9,10])
#        print(test.nplots)
        par = sp.host().twinx()
        par.plot(x,y)
        par.set_position(af.gs[sp.index].get_position(af.fig))
        print(par)
        sp.axes.append(par)
#        sp.contents = None
#        sp.identify()
        af.draw()

    def adjust_weights(self):
        af = self.parent.axes_frame
        weights = []
        for i in self.weights_edit.text():  # parse weighting input
            if i in '0, []':  # ignore zero, commas, spaces, and brackets
                continue
            elif i.isdigit():
                weights.append(int(i))
            else:
                print('Only integer inputs <10 allowed')
                self.weights_edit.clear()
                return
        if len(weights) != len(af.subplots):
            print('Figure has {} subplots but {} weights were provided'
                    .format(len(af.subplots), len(weights)))
            self.weights_edit.clear()
            return
        nplots = af.gs.get_geometry()[0]
        af.gs = GridSpec(nplots, 1, height_ratios=weights)
        for i, sp in enumerate(af.subplots):
            sp.index = i
            sp.host().set_position(af.gs[i].get_position(af.fig))
            sp.identify()
        print('new weights: ', weights)
        self.weights_edit.clear()
        af.draw()

    def reorder(self):
        af = self.parent.axes_frame
        caller = QObject.sender(self)
        if caller == self.up_button:
            inc = -1
        if caller == self.down_button:
            inc = 1
        sp = af.current_sps[0]
        i = sp.index
        j = i+inc

        nplots = af.gs.get_geometry()[0]
        weights = af.gs.get_height_ratios()

        # if can be moved up/down
        if 0 <= j < nplots:
            weights[i], weights[j] = weights[j], weights[i]
            af.subplots[i], af.subplots[j] = af.subplots[j], af.subplots[i]
            af.current_sps = [af.subplots[j]]
            self.message.setText(str(j))
            af.gs = GridSpec(nplots, 1, height_ratios=weights)
            for i, sp in enumerate(af.subplots):
                sp.index = i
                sp.host().set_position(af.gs[i].get_position(af.fig))
                sp.identify()
            af.draw()
        else:

            print("can't reorder")

    def delete(self):
        af = self.parent.axes_frame
        if not af.current_sps: return
        sp = af.current_sps[0]
        i = sp.index
        sp.host().remove()
        del af.subplots[i]
        weights = af.gs.get_height_ratios()
        del weights[i]
        nplots = af.gs.get_geometry()[0]
        af.gs = GridSpec(nplots-1, 1, height_ratios=weights)
        for i, sp in enumerate(af.subplots):
            sp.index = i
            sp.host().set_position(af.gs[i].get_position(af.fig))
            sp.identify()
        af.draw()



class CustomAxes(mpl.axes.Axes):
    name = 'test'
    veggie = 'cucumber'

#    def twinx(self):
##        print('custom twinx function')
##        gs = self.figure.canvas.gs
###        print(gs.get_geometry())
##        print(gs._nrows)
#        super().twinx()






class GridSpec(GridSpec):
    def get_grid_positions(self, fig, raw=False):
        """
        return lists of bottom and top position of rows, left and
        right positions of columns.

        If raw=True, then these are all in units relative to the container
        with no margins.  (used for constrained_layout).
        """
        nrows, ncols = self.get_geometry()
        nrows = fig.canvas.gs.get_geometry()[0]
        print(nrows, ncols)

        if raw:
            left = 0.
            right = 1.
            bottom = 0.
            top = 1.
            wspace = 0.
            hspace = 0.
        else:
            subplot_params = self.get_subplot_params(fig)
            left = subplot_params.left
            right = subplot_params.right
            bottom = subplot_params.bottom
            top = subplot_params.top
            wspace = subplot_params.wspace
            hspace = subplot_params.hspace
        tot_width = right - left
        tot_height = top - bottom

        # calculate accumulated heights of columns
        cell_h = tot_height / (nrows + hspace*(nrows-1))
        sep_h = hspace * cell_h
        if self._row_height_ratios is not None:
            norm = cell_h * nrows / sum(self._row_height_ratios)
            cell_heights = [r * norm for r in self._row_height_ratios]
        else:
            cell_heights = [cell_h] * nrows
        sep_heights = [0] + ([sep_h] * (nrows-1))
        cell_hs = np.cumsum(np.column_stack([sep_heights, cell_heights]).flat)

        # calculate accumulated widths of rows
        cell_w = tot_width / (ncols + wspace*(ncols-1))
        sep_w = wspace * cell_w
        if self._col_width_ratios is not None:
            norm = cell_w * ncols / sum(self._col_width_ratios)
            cell_widths = [r * norm for r in self._col_width_ratios]
        else:
            cell_widths = [cell_w] * ncols
        sep_widths = [0] + ([sep_w] * (ncols-1))
        cell_ws = np.cumsum(np.column_stack([sep_widths, cell_widths]).flat)

        fig_tops, fig_bottoms = (top - cell_hs).reshape((-1, 2)).T
        fig_lefts, fig_rights = (left + cell_ws).reshape((-1, 2)).T
        return fig_bottoms, fig_tops, fig_lefts, fig_rights






mpl.projections.register_projection(CustomAxes)

#### THE ACTUAL RUN COMMAND
if 'app' not in locals():
    app = QCoreApplication.instance()
if app is None:  # otherwise kernel dies
    app = QApplication(sys.argv)
X = Restructure()

app.exec_()
