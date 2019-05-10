# -*- coding: utf-8 -*-
"""
Created on Thu May  2 08:41:04 2019

@author: seery
"""
import sys
import os
import re
#import warnings
import datetime as dt

import itertools
import math
import functools

from PyQt5.QtWidgets import QMainWindow, QAction, QDockWidget, QWidget, QVBoxLayout, QApplication, QDesktopWidget, QGridLayout, QTreeWidget, QPushButton, QTreeWidgetItem, QStyle, QSizePolicy, QLabel, QLineEdit, QCheckBox
from PyQt5.QtGui import QIcon#, QAbstractItemView causes ImportError
from PyQt5.QtCore import QCoreApplication, Qt

import numpy as np
import pandas as pd
import matplotlib as mpl
import matplotlib.dates as mdates
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas


class Telemetry_Grapher(QMainWindow):
    def __init__(self, data, data_dict):
        super().__init__()
        self.data = data
        self.data_dict = data_dict
        self.start = '2018-12-06 00:00'
        self.end = '2018-12-09 00:00'  # dummy start/end from PHI_HK, default will be None
        self.set_preferences()
#         self.width = 1200
#         self.height = 700
        self.setWindowTitle('Telemetry Plot Configurator COPY')
        self.setWindowIcon(QIcon('satellite.png'))
        self.statusBar().showMessage('No subplot selected')
        fileMenu = self.menuBar().addMenu('File')
        exitAction = QAction('Exit', self)
        exitAction.setShortcut('Ctrl+Q')
        exitAction.setStatusTip('Exit application')
        exitAction.triggered.connect(self.close)
        restoreAction = QAction('Restore Docks', self)
        restoreAction.triggered.connect(self.restore_docks)
        fileMenu.addAction(exitAction)
        fileMenu.addAction(restoreAction)

        self.docked_SF = QDockWidget("Series Frame", self)
        self.series_frame = Series_Frame(self)
        self.docked_SF.setWidget(self.series_frame)
        self.docked_CF = QDockWidget("Control Frame", self)
        self.control_frame = Control_Frame(self)
        self.docked_CF.setWidget(self.control_frame)
        self.addDockWidget(Qt.LeftDockWidgetArea, self.docked_SF)
        self.addDockWidget(Qt.BottomDockWidgetArea, self.docked_CF)
        self.axes_frame = Axes_Frame(self)
        self.master_frame = QWidget()
        self.master_frame.setLayout(QVBoxLayout())
        self.master_frame.layout().addWidget(self.axes_frame)
        self.setCentralWidget(self.master_frame)
        self.resizeDocks([self.docked_SF], [600], Qt.Horizontal)
#         self.resize(self.width, self.height)
#         self.center()
        self.showMaximized()
        self.control_frame.setFixedHeight(self.control_frame.height())


    def closeEvent(self, event):
        """Hides any floating QDockWidgets and closes all created figures upon application exit."""
        for qw in QApplication.topLevelWidgets():
            if isinstance(qw, QDockWidget):
                qw.hide()
        plt.close('all')
        event.accept()

    def restore_docks(self):
        self.docked_CF.show()
        self.docked_SF.show()

    def set_preferences(self):
#        if self.start is None:
#            startCondition = lambda index: index == True
#        else:
#            startCondition = lambda index: index >= self.start
#        if self.end is None:
#            endCondition = lambda index: index == True
#        else:
#            endCondition = lambda index: index <= self.end
        if self.start is None: self.start = min([self.data[name].index[0] for name in self.data.keys()])
        if self.end is None: self.end = max([self.data[name].index[-1] for name in self.data.keys()])
        self.timespan = pd.to_datetime(self.end)-pd.to_datetime(self.start)
        if self.timespan < dt.timedelta(days=1):
            self.dotsize = 0.8
        else:
            self.dotsize = 0.5
        if self.timespan >= dt.timedelta(days=2) and self.timespan < dt.timedelta(days=4):
            self.dateformat = mdates.DateFormatter('%d/%b %H:%M')
            self.major_locator = mdates.DayLocator()
        elif self.timespan >= dt.timedelta(days=4):
            self.dateformat = mdates.DateFormatter('%d/%b %H:%M')
            self.major_locator = mdates.DayLocator()
        else:
            self.dateformat = mdates.DateFormatter('%d %b %Y %H:%M')
            self.major_locator = mdates.HourLocator(interval=2)
# Legacy
    def center(self):
        qr = self.frameGeometry()
        cp = QDesktopWidget().availableGeometry().center()
        qr.moveCenter(cp)
        self.move(qr.topLeft())


class Series_Frame(QWidget):
    """Manages imported data. Shows hierarchically the series (with assigned units) available to plot and the series plotted in the selected subplot(s)."""

    def __init__(self, parent):
        super().__init__()
        self.parent = parent
#         self.resize(300,parent.height)
        grid = QGridLayout()
        w = QWidget()
        ncols = 2
        self.available = QTreeWidget(w)
#        self.available.setSelectionMode(QAbstractItemView.MultiSelection)
        self.available.setHeaderLabels(["Available Series", "Unit"])
        self.available.setColumnCount(ncols)
        self.plotted = QTreeWidget(w)
#        self.plotted.setSelectionMode(QAbstractItemView.MultiSelection)
        self.plotted.setHeaderLabels(["Plotted Series", "Unit"])
        self.available.setColumnCount(ncols)
        self.add = QPushButton('Add')
        self.add.clicked.connect(lambda: self.transfer('Add'))
        self.remove = QPushButton('Remove')
        self.remove.clicked.connect(lambda: self.transfer('Remove'))
        self.searchAvailable = QLineEdit()
        self.searchAvailable.setPlaceholderText('Search')
        self.searchAvailable.textChanged.connect(lambda: self.search(self.searchAvailable, self.available))
        self.searchPlotted = QLineEdit()
        self.searchPlotted.setPlaceholderText('Search')
        self.searchPlotted.textChanged.connect(lambda: self.search(self.searchPlotted, self.plotted))

        grid.addWidget(self.searchAvailable, 0, 0)
        grid.addWidget(self.searchPlotted, 0, 1)
        grid.addWidget(self.available, 1, 0)
        grid.addWidget(self.plotted, 1, 1)
        grid.addWidget(self.add, 2, 0)
        grid.addWidget(self.remove, 2, 1)
        self.setLayout(grid)

        self.populate_tree(parent.data_dict, self.available)
        self.searchable_available = parent.data.copy()
        self.searchable_plotted = {}
        self.available.expandAll()
        self.available.resizeColumnToContents(0)

    def cleanup(self):
        """Sorts both trees and deletes any dataframe references that contain no series."""
        for tree in [self.available, self.plotted]:
            tree.sortItems(0,0)  # sort by column 0 in ascending order
            to_delete = []
            for i in range(tree.topLevelItemCount()):
                if tree.topLevelItem(i).childCount() == 0:
                    to_delete.append(i)
                else:
                    tree.topLevelItem(i).sortChildren(0,0)
            for x in to_delete:
                tree.takeTopLevelItem(x)

    def read_tree(self, tree):
        """Reads tree into standard contents format {name: {series:units}}."""
        level0s = [tree.topLevelItem(i) for i in range(tree.topLevelItemCount())]
        contents = None
        if level0s:
            names = [n.text(0) for n in level0s]
            series = [[level0.child(i).text(0) for i in range(level0.childCount())] for level0 in level0s]
            units = [[level0.child(i).text(1) for i in range(level0.childCount())] for level0 in level0s]
            contents = {}
            all_units = []
            for n,s,u in zip(names, series, units):
                contents[n] = dict(zip(s,u))
                all_units.extend(u)
        else:
            contents = None
            all_units = []  # probably?
        return contents, all_units


    def update_subplot_contents(self, sp):
        """Reads plotted tree into selected subplots' contents."""
        if sp is not None:
            contents, all_units = self.read_tree(self.plotted)
            if not sp.order: sp.order = [None]
        else:
            contents = None
        sp.contents = contents

    def populate_tree(self, contents, target_tree):
        """Adds contents to target_tree with no repeats and sorts."""
        if contents is not None:
            target_level0 = [target_tree.topLevelItem(i) for i in range(target_tree.topLevelItemCount())]
            target_names = [n.text(0) for n in target_level0]
            for name, series_units in contents.items():
                if name in target_names:  # if dataframe already exists in target_tree, get its level0 entry
                    i = target_names.index(name)
                    level0 = target_level0[i]
                else:  # if not, create it and add it
                    level0 = QTreeWidgetItem([name])
                    target_tree.addTopLevelItem(level0)
                for series, unit in series_units.items():  # add series/units to their corresponding level0 entry
                    level1 = QTreeWidgetItem([series, unit])
                    level0.addChild(level1)
                level0.setExpanded(True)
            target_tree.resizeColumnToContents(0)
            self.cleanup()

    # Can I make this allow multiple item selection?
    # How do I make it deselectable?
    def transfer(self, caller):
        """Swaps series or entire dataframe references from available to plotted or vice versa."""
        TG = self.parent
        AF = TG.axes_frame
        CF = TG.control_frame
        selected_sps = AF.current_sps
        if not selected_sps:
            TG.statusBar().showMessage('Select a subplot to add or remove series')
        elif len(selected_sps) > 1:
            TG.statusBar().showMessage('Series can only be added to one subplot')
        else:
            sp = selected_sps[0]
            if caller == 'Add':
                sourceTree = self.available
                targetTree = self.plotted
            if caller == 'Remove':
                sourceTree = self.plotted
                targetTree = self.available
            selection = sourceTree.selectedItems()
            if selection:
                selected = selection[0]
                if selected.parent() is None:  # if selected QTreeWidgetItem (qtwi) is topLevelItem (level0)
                    children = [selected.child(i) for i in range(selected.childCount())]
                    for child in children: selected.removeChild(child)
                    name = selected.text(0)
                    series = [child.text(0) for child in children]
                    units = [child.text(1) for child in children]
                    contents = {name: dict(zip(series,units))}
                else:  # if selected qtwi has a parent (level1, single series)
                    parent = selected.parent()
                    i = parent.indexOfChild(selected)
                    child = parent.takeChild(i)
                    name = parent.text(0)
                    series = child.text(0)
                    units = child.text(1)
                    contents = {name: {series:units}}
                self.populate_tree(contents, targetTree)
                self.cleanup()  # takes care of any empty level0 references
                self.update_subplot_contents(sp)  # assign contents to subplot
                CF.refresh_subplot(sp)
            else:
                TG.statusBar().showMessage('No series selected')

    def search(self, search_bar, tree):
        user_input = re.compile(search_bar.text(), re.IGNORECASE)
        level0s = [tree.topLevelItem(i) for i in range(tree.topLevelItemCount())]
        if level0s:
            names = [n.text(0) for n in level0s]
            series = [[level0.child(i).text(0) for i in range(level0.childCount()) if user_input.search(level0.child(i).text(0))] for level0 in level0s]
            units = [[level0.child(i).text(1) for i in range(level0.childCount()) if user_input.search(level0.child(i).text(0))] for level0 in level0s]
            contents = {}
            for n,s,u in zip(names, series, units):
                contents[n] = dict(zip(s,u))
            tree.clear()
            self.populate_tree(contents, tree)
            self.cleanup()
        #  THIS WORKS. BUT. I need to be able to save what was there before in a class attribute
        #  That attribute also needs to be affected by transferring series into the plotted tree.
        #  ^ this edit will occur in update_subplot_contents

class Subplot_Manager():
    """Wrapper around subplot object (host). Keeps track of contents and settings of each subplot."""
    def __init__(self, host, order=[None], contents=None, weight=1, index=None, fig_index=0, legend=False, colorCoord=False):
        self.axes = [host]  # keeps track of parasitic axes
        self.order = order  # keeps track of preferred unit order
        self.contents = contents # standard contents format: {name: {series:units}}
#        self.weight = weight  # convenience attribute
        self.index = index  # convenience attribute
        self.legend = legend  # legend toggle
        self.colorCoord = colorCoord  # color coordination toggle

    def host(self):
        return self.axes[0]


class Axes_Frame(FigureCanvas):
    """Container for figure with subplots. New Axes_Frame objects are created and when a new Figure tab is created (TBI)."""
    def __init__(self, parent):
        self.parent = parent
        self.fig = plt.figure(constrained_layout=False)  # not working with gridspec in controls frame. Look into later.
        super().__init__(self.fig)
        self.weights = [1]
        gs = gridspec.GridSpec(1, 1, figure=self.fig, height_ratios=self.weights)
        ax0 = self.fig.add_subplot(gs[0])
        self.subplots = [Subplot_Manager(ax0, index=0)]
        self.current_sps = []
        self.fig.canvas.mpl_connect('button_press_event', self.select_subplot)
        self.fig.suptitle(parent.control_frame.titleEdit.text(), fontsize=20)
        mpl.rc('font', family='serif')
        self.draw()

        ### These will be moved to plotting preferences QDockWidget
        self.unit_dict = {  # ylabels for each unit type so units can be identified by shorthand letters
            'T':'Temperature [°C]',
            'V':'Voltage [V]',
            'I':'Current [A]',
            'P':'Power [W]'
        }
        self.color_dict = {  #when color coordination is on, assign map unit types to these colors
            'T':'r',
            'V':'b',
            'I':'g',
            'P':'y',
        }
        self.linestyles = [  # when color coordination is on, use linestyles in this order to differentiate series
            '-',
            '--',
            '-.',
            ':',
        ]



    def select_subplot(self, event, force_select=None):
        """Highlights clicked-on subplot and displays subplot contents in plotted tree.
        Shift and Ctrl clicking supported.
        Click within figure but outside subplots to deselect axis and clear plotted tree.
        Provide force_select=X to programmatically select subplots in list X (wrapped by Subplot_Manager object)."""
        TG = self.parent
        CF = TG.control_frame
        SF = TG.series_frame
        widths = {True:1.5, False:0.5}
        SF.plotted.clear()
        modifiers = QApplication.keyboardModifiers()

        def highlight(sps, invert=False):
            if sps:
                for sp in sps:
                    if invert:
                        plt.setp(sp.host().spines.values(), linewidth=widths[False])
                        if sp in self.current_sps: self.current_sps.remove(sp)
                    else:
                        plt.setp(sp.host().spines.values(), linewidth=widths[True])
                        self.current_sps.append(sp)
            else:
                self.current_sps = []

        if force_select is not None:
            highlight([force_select])
        else:
            if event.inaxes is None:
                highlight(self.subplots, invert=True)
                self.current_sps = []
            else:
                sp = self.subplots[[sp.host() for sp in self.subplots].index(event.inaxes)]
                if modifiers == Qt.ControlModifier:
                    highlight([sp], invert=(sp in self.current_sps))
                elif modifiers == Qt.ShiftModifier:
                    if not self.current_sps:
                        highlight([sp])
                    elif len(self.current_sps) == 1:
                        current_i = self.current_sps[0].index
                        highlight(self.subplots, invert=True)
                        highlight(self.subplots[min([current_i, sp.index]):max([current_i, sp.index])+1])
                    else:
                        highlight(self.subplots, invert=True)
                        highlight([sp])
                else:
                    highlight(self.subplots, invert=True)
                    highlight([sp])
        if len(self.current_sps) == 1:
            sp = self.current_sps[0]
            SF.populate_tree(sp.contents, SF.plotted)
            CF.legendToggle.setCheckable(True)
            CF.legendToggle.setChecked(sp.legend)
            CF.colorCoord.setCheckable(True)
            CF.colorCoord.setChecked(sp.colorCoord)
            TG.statusBar().showMessage('Selected subplot: {}'.format(sp.index))
        else:
            SF.plotted.clear()
            if self.current_sps:
                CF.legendToggle.setChecked(any([sp.legend for sp in self.current_sps]))
                CF.colorCoord.setChecked(any([sp.colorCoord for sp in self.current_sps]))
                TG.statusBar().showMessage('Selected subplots: {}'.format(sorted([sp.index for sp in self.current_sps])))
            else:
                CF.legendToggle.setChecked(False)
                CF.colorCoord.setChecked(False)
                TG.statusBar().showMessage('No subplot selected')
        self.draw()


class Control_Frame(QWidget):
    """Contains all buttons for controlling the organization of subplots and saving the figure."""
    def __init__(self, parent):
        super().__init__()
        self.parent = parent
        self.grid = QGridLayout()

        self.reorderUp = QPushButton()
        self.reorderUp.setIcon(self.style().standardIcon(getattr(QStyle, 'SP_TitleBarShadeButton')))
        self.reorderUp.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.reorderUp.clicked.connect(lambda: self.reorder(parent.axes_frame.current_sps, 'up'))
        self.reorderDown = QPushButton()
        self.reorderDown.setIcon(self.style().standardIcon(getattr(QStyle, 'SP_TitleBarUnshadeButton')))
        self.reorderDown.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.reorderDown.clicked.connect(lambda: self.reorder(parent.axes_frame.current_sps, 'down'))
        self.insert = QPushButton('Insert')
        self.insert.clicked.connect(lambda: self.insert_subplot(parent.axes_frame.current_sps))
        self.delete = QPushButton('Delete')
        self.delete.clicked.connect(lambda: self.delete_subplot(parent.axes_frame.current_sps))
        self.clear = QPushButton('Clear Subplot')
        self.clear.clicked.connect(lambda: self.clear_subplot(parent.axes_frame.current_sps))
        self.legendToggle = QCheckBox('Legend')
        self.legendToggle.clicked.connect(lambda: self.toggle_legend(parent.axes_frame.current_sps))
        self.cycle = QPushButton('Cycle Primary')
        self.cycle.clicked.connect(lambda: self.cycle_subplot(parent.axes_frame.current_sps))
        self.colorCoord = QCheckBox('Color by Unit')
        self.colorCoord.clicked.connect(lambda: self.color_coordinate(parent.axes_frame.current_sps))
        self.weighting = QLabel('Weighting:')
        self.weightsEdit = QLineEdit('[1]')
        self.weightsEdit.returnPressed.connect(self.adjust_weights)
        self.title = QLabel('Figure title:')
        self.titleEdit = QLineEdit('New_Figure')
        self.titleEdit.returnPressed.connect(self.rename)
        self.save = QPushButton('Save')
        self.save.clicked.connect(self.save_figure)
        self.pathEdit = QLineEdit(os.getcwd()+'\\'+self.titleEdit.text()+'.jpg')

        col_weights = [1, 1, 1, 1, 100]
        for i,cw in enumerate(col_weights):
            self.grid.setColumnStretch(i,cw)
        objects = [
            self.reorderUp,
            self.reorderDown,
            self.insert,
            self.delete,
            self.clear,
            self.legendToggle,
            self.colorCoord,
            self.cycle,
            self.weighting,
            self.title,
            self.save,
            self.weightsEdit,
            self.titleEdit,
            self.pathEdit,
        ]
        positions = [
            (0,0,3,1),
            (3,0,3,1),
            (0,1,2,1),
            (2,1,2,1),
            (4,1,2,1),
            (0,2,2,1),
            (2,2,2,1),
            (4,2,2,1),
            (0,3,2,1),
            (2,3,2,1),
            (4,3,2,1),
            (0,4,2,1),
            (2,4,2,1),
            (4,4,2,1),
        ]
        for o,p in zip(objects, positions):
            self.grid.addWidget(o,*p)
        self.setLayout(self.grid)

    def cleanup_axes(self):
        AF = self.parent.axes_frame
        for sp in AF.subplots[0:-1]:  # set all non-base xaxes invisible
            sp.host().xaxis.set_visible(False)
        AF.subplots[-1].host().xaxis.set_visible(True)
#        if sp.index != nplots:
#            # if sp.contents is not None, save xaxis labels
#            sp.host().xaxis.set_visible(False)
#        else:
#            sp.host().xaxis.set_visible(True)
# later on need to override possibly empty axis with saved xaxis labels

    def reorder(self, sps, direction):
        """Reorders selected subplot up or down and updates weighting field."""
        TG = self.parent
        AF = TG.axes_frame
        if len(sps) == 1:
            if direction == 'up':
                inc = -1
            if direction == 'down':
                inc = 1
            sp = sps[0]
            i = sp.index
            if 0 <= i+inc < len(AF.subplots):  # do nothing if moving sp up or down would put it past the first/last index
                AF.weights[i], AF.weights[i+inc] = AF.weights[i+inc], AF.weights[i]
                AF.subplots[i], AF.subplots[i+inc] = AF.subplots[i+inc], AF.subplots[i]
                for i,sp in enumerate(AF.subplots): sp.index = i
                gs = gridspec.GridSpec(len(AF.subplots), 1, height_ratios=AF.weights)
                for i, sp in enumerate(AF.subplots):
                    sp.host().set_position(gs[i].get_position(AF.fig))
                self.cleanup_axes()
                AF.draw()
        else:
            TG.statusBar().showMessage('Select one subplot to reorder')

    def insert_subplot(self, sps):
        """Inserts subplot at top of figure. (Indexed insertion not working)"""
        TG = self.parent
        AF = TG.axes_frame
        nplots = len(AF.subplots)
        if len(sps) != 1:
            index = nplots-1
            TG.statusBar().showMessage('No singular subplot selected. Subplot inserted at end.')
        else:
            index = sps[0].index
        AF.weights.insert(index+1,1)
        gs = gridspec.GridSpec(nplots+1, 1, height_ratios=AF.weights)
        for i, sp in enumerate(AF.subplots):
            if i <= index:
                sp.host().set_position(gs[i].get_position(AF.fig))
            else:
                sp.host().set_position(gs[i+1].get_position(AF.fig))
        ax = AF.fig.add_subplot(gs[index+1])
        AF.subplots.insert(index+1, Subplot_Manager(ax, index=index+1))  # AF.subplots kept in displayed order
        for i,sp in enumerate(AF.subplots): sp.index = i
        self.cleanup_axes()
        self.weightsEdit.setText(str(AF.weights))
        AF.draw()

    def delete_subplot(self, sps):
        """Deletes selected subplot(s) and adds contents back into available tree."""
        TG = self.parent
        if sps:
            AF = TG.axes_frame
            if len(AF.subplots) == 1:
                self.clear_subplot(sps)
            else:
                SF = TG.series_frame
                indices = [sp.index for sp in sps]
                for i in sorted(indices, reverse=True):
                    del AF.weights[i]
                    SF.populate_tree(AF.subplots[i].contents, SF.available)  # add contents back into available tree
                    del AF.current_sps[AF.current_sps.index(AF.subplots[i])]  # remove from selection
                    AF.subplots[i].host().remove()  # remove from figure
                    del AF.subplots[i]  # delete from subplots list
                gs = gridspec.GridSpec(len(AF.subplots), 1, height_ratios=AF.weights)
                for i, sp in enumerate(AF.subplots):
                    sp.index = i
                    sp.host().set_position(gs[i].get_position(AF.fig))
                self.cleanup_axes()
                self.weightsEdit.setText(str(AF.weights))
                AF.draw()
                AF.select_subplot(None, force_select=[])  # clear selelection
        else:
            TG.statusBar().showMessage('Select one or more subplots to delete')

    def clear_subplot(self, sps):
        """Adds selected subplot's contents back into available tree, clears axis."""
        TG = self.parent
        if sps:
            SF = TG.series_frame
            target_tree = SF.available
            SF.plotted.clear()
            for sp in sps:
                SF.populate_tree(sp.contents, target_tree)
                sp.contents = None
                sp.order = [None]
                self.refresh_subplot(sp)
            if len(sps) > 1: TG.statusBar().showMessage('Cleared subplots: {}'.format(sorted([sp.index for sp in sps])))
            else: TG.statusBar().showMessage('Cleared subplot: {}'.format(sps[0].index))
        else:
            TG.statusBar().showMessage('Select one or more subplots to clear')

    def toggle_legend(self, sps):
        """Toggles legend display of selected subplot."""
        if sps:
            if len(sps) == 1:
                sp = sps[0]
                sp.legend = not sp.legend
                self.refresh_subplot(sp)
            else:
                any_legend = any([sp.legend for sp in sps])
                for sp in sps:
                    sp.legend = not any_legend
                    self.refresh_subplot(sp)
        else:
            TG = self.parent
            self.legendToggle.setCheckable(False)
            TG.statusBar().showMessage('Select one or more subplots to toggle legend')


    def color_coordinate(self, sps):
        """Recolors lines and axes in selected subplot to correspond by unit type."""
        if sps:
            if len(sps) == 1:
                sp = sps[0]
                sp.colorCoord = not sp.colorCoord
                self.refresh_subplot(sp)
            else:
                any_coord = any([sp.colorCoord for sp in sps])
                for sp in sps:
                    sp.colorCoord = not any_coord
                    self.refresh_subplot(sp)
        else:
            TG = self.parent
            self.colorCoord.setCheckable(False)
            TG.statusBar().showMessage('Select one or more subplots to toggle color coordination')


    def cycle_subplot(self, sps):
        """Cycles through unit order permutations."""
        if sps:
            for sp in sps:
                perms = [list(p) for p in sorted(itertools.permutations(sp.order))]
                i = perms.index(sp.order)
                sp.order = perms[(i+1)%len(perms)]
                self.refresh_subplot(sp)
        else:
            TG = self.parent
            TG.statusBar().showMessage('Select one or more subplots to cycle unit plotting order')

    def adjust_weights(self):
        """Adjusts subplot vertical aspect ratios based on provided list of weights (or sequence of digits)."""
        TG = self.parent
        AF = TG.axes_frame
        weights = []
        for i in self.weightsEdit.text():  # parse weighting input
            if i.isdigit():
                weights.append(int(i))
            elif i in ', []':  # ignore commas, spaces, and brackets
                continue
            else:
                TG.statusBar().showMessage('Only integer inputs <10 allowed')
                return
        if len(weights) != len(AF.subplots):
            TG.statusBar().showMessage('{} weights provided for figure with {} subplots'.format(len(weights), len(AF.subplots)))
            return
        g = functools.reduce(math.gcd, weights)
        weights = [w//g for w in weights]  # simplify weights by their greatest common denominator (eg [2,2,4] -> [1,1,2])
        self.weightsEdit.setText(str(weights))
        gs = gridspec.GridSpec(len(AF.subplots), 1, height_ratios=weights)
        for i, sp in enumerate(AF.subplots):
            sp.host().set_position(gs[i].get_position(AF.fig))
        AF.draw()

    def rename(self):
        """Renames figure and changes save path to new figure title."""
        TG = self.parent
        AF = TG.axes_frame
        fig_title = re.sub('[\\\\.]', '', self.titleEdit.text())  # get rid of any backslashes or dots
        if not fig_title:
            AF.fig.suptitle('')
            fig_title = 'New_Figure'
        else:
            AF.fig.suptitle(fig_title, fontsize=20)
        input_path = self.pathEdit.text()
        try:
            save_dir = input_path[:input_path.rindex('\\')]  # path string up until last backslash occurrence
        except ValueError:
            save_dir = os.getcwd()
        try:
            ext = input_path[input_path.rindex('.'):]  # path string from last . occurrence to end
        except ValueError:
            ext = '.jpg'  # default to JPG format
        self.pathEdit.setText(save_dir + '\\' + fig_title + ext)
        AF.draw()

    def save_figure(self):
        """Saves figure to displayed directory. If no path or extension is given, defaults are current directory and .jpg."""
        TG = self.parent
        AF = TG.axes_frame
        AF.select_subplot(None, force_select=[])  # force deselect before save (no highlighted axes in saved figure)
        AF.draw()
        plt.savefig(self.pathEdit.text(), dpi=300, format='jpg', transparent=True, bbox_inches='tight')
        TG.statusBar().showMessage('Saved to {}'.format(self.pathEdit.text()))

    def make_patch_spines_invisible(self, ax):
        """see https://matplotlib.org/gallery/ticks_and_spines/multiple_yaxis_with_spines.html"""
        ax.set_frame_on(True)
        ax.patch.set_visible(False)
        for sp in ax.spines.values():
            sp.set_visible(False)

    def refresh_subplot(self, sp, verbose=True):
        """Main plotting function. Auto-generates parasitic axes in specified unit order."""
        TG = self.parent
        AF = TG.axes_frame
        for ax in sp.axes[1:]: ax.remove()  # remove parasitic axes from subplot
        sp.axes = [sp.host()]  # clear parasitic axes from sp.axes
        sp.host().clear()  # clear host axis of data

        color_index = 0
        style_dict = {}
        lines = []
        if sp.contents is not None:
            for name, series_units in sp.contents.items():
                for series, unit in series_units.items():

                    if sp.order[0] is None:
                        sp.order[0] = unit  # if no order given, default to sorted order
                    if unit not in sp.order:
                        sp.order.append(unit)  # new units go at the end of the order
                    ax_index = sp.order.index(unit)  # get index of unit in unit order
                    while len(sp.axes)-1 < ax_index: # extend sp.axes as needed
                        par = sp.host().twinx()
                        sp.axes.append(par)
                    par = sp.axes[ax_index]  # get axis (parasitic or host) at index of unit
                    if sp.colorCoord:
                        if unit not in style_dict:  # keep track of how many series are plotted in each unit
                            style_dict[unit] = 0
                        style_counter = style_dict[unit]
                        style_dict[unit] = style_counter+1
                        try:  # assign color based on unit, black if undefined
                            color = AF.color_dict[unit]
                        except KeyError:
                            color = 'k'
                            print('Unit {} has no assigned color in Axes_Frame.color_dict'.format(unit))
                        style = AF.linestyles[style_counter%len(AF.linestyles)]
                        par.yaxis.label.set_color(color)
                    else:  # set color to rotate through default colormap (otherwise colormap is done per axis, not the whole subplot)
                        color='C'+str(color_index%10)
                        color_index += 1
                        style = None
                        par.yaxis.label.set_color('k')
                    line, = par.plot(TG.data[name][series], color=color, linestyle=style,
                                     marker='o', markersize=TG.dotsize, fillstyle='full', markeredgewidth=TG.dotsize, linewidth=0.75)
                    lines.append(line)
                    try:
                        par.set_ylabel(AF.unit_dict[unit])  # set ylabel to formal unit description
                    except KeyError:
                        par.set_ylabel(unit)  # if not defined in unit_dict, use shorthand
            for i,par in enumerate(sp.axes[1:]):  # offset parasitic axes
                self.make_patch_spines_invisible(par)
                par.spines["right"].set_visible(True)
                par.spines["right"].set_position(("axes", 1+.05*(i)))
            if sp.legend:  # create and offset legend
                if 'i' not in locals(): i = -1
                labels = [line.get_label() for line in lines]
                leg = sp.host().legend(lines, labels, bbox_to_anchor=(1+.05*(i+1), .5), loc="center left")
                for line in leg.get_lines(): line.set_linewidth(2)
        sp.host().grid(b=True, axis='x')
        base_X = AF.subplots[-1].axes[0]
        plt.sca(base_X)
        for sp in AF.subplots:
#            if sp.contents is not None:
            ticks = sp.host().get_xticklabels()
            print(sp.index, ticks)
#                break
#        if 'ticks' in locals():
#            print(ticks)
#            base_X.xaxis.set_visible(True)
#            base_X.set_xticklabels(ticks)
#            plt.xticks(rotation=50, ha='right')
#        else:
#            base_X.xaxis.set_visible(False)
#            for sp in AF.subplots:
#                sp.host().grid(b=False, axis='x')

#        fig_not_empty = not all([sp.contents==None for sp in AF.subplots])
#        base_X.xaxis.set_visible(fig_not_empty)
#        plt.grid(b=fig_not_empty, axis='x')


        AF.draw()


# Run the program!
if 'app' not in locals(): app = QCoreApplication.instance()
if app is None:  # otherwise kernel dies
    app = QApplication(sys.argv)
X = Telemetry_Grapher(data, data_dict)
app.exec_()