# -*- coding: utf-8 -*-
"""
Created on Fri May 17 19:42:42 2019

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

### THE RUN COMMAND IS AT THE BOTTOM. YOU CAN JUST HIT RUN ON THIS SCRIPT.


class Telemetry_Grapher(QMainWindow):
    def __init__(self, groups={}):
        super().__init__()
        self.groups = copy.deepcopy(groups)
        self.path_kwargs = {}
        self.unit_dict = {  # dictionary of supported units
                'Position':['nm','μm','mm','cm','m'],
                'Velocity':['mm/s','cm/s','m/s'],
                'Acceleration':['mm/s^2','m/s^2'],  # check how superscripts are parsed
                'Angle':['deg','rad'],
                'Temperature':['°C','°F','K'],
                'Pressure':['mPa','Pa','kPa','MPa','GPa','mbar','bar','kbar','atm','psi','ksi'],
                'Heat':['mJ','J','kJ'],
                'Voltage':['mV','V','kV','MV'],
                'Current':['mA','A','kA'],
                'Resistance':['mΩ','Ω','kΩ','MΩ'],
                'Force':['mN','N','kN'],
                'Torque':['Nmm','Nm','kNm'],
                'Power':['mW','W','kW'],
                }

        self.unit_clarify = {  # try to map parsed unit through this dict before comparing to TG unit_dict
                'degC':'°C',
                'degF':'°F',
                'C':'°C',
                'F':'°F',
                }

        self.color_dict = {
                'Position':'C0',
                'Velocity':'C1',
                'Acceleration':'C2',
                'Angle':'C3',
                'Temperature':'C4',
                'Pressure':'C5',
                'Heat':'C6',
                'Voltage':'C7',
                'Current':'C8',
                'Resistance':'C9',
                'Force':'b',
                'Torque':'g',
                'Power':'r',
                None:'k'
                }

        self.markers = [  # when color coordination is on, use markers in this order to differentiate series
                'o',
                '+',
                'x',
                'D',
                's',
                '^',
                'v',
                '<',
                '>',
            ]

        self.setWindowTitle('Telemetry Plot Configurator')
        self.setWindowIcon(QIcon('satellite.png'))
        self.statusBar().showMessage('No subplot selected')
        self.manager = QWidget()

        self.docked_FS = QDockWidget("Figure Settings", self)
        self.figure_settings = Figure_Settings(self)
        self.docked_FS.setWidget(self.figure_settings)

        self.docked_CF = QDockWidget("Control Frame", self)
        self.control_frame = Control_Frame(self)
        self.docked_CF.setWidget(self.control_frame)
        self.axes_frame = Axes_Frame(self)
        self.master_frame = QWidget()
        self.master_frame.setLayout(QVBoxLayout())
        self.master_frame.layout().addWidget(self.axes_frame)
        self.setCentralWidget(self.master_frame)
        self.docked_SF = QDockWidget("Series Frame", self)
        self.series_frame = Series_Frame(self)
        self.docked_SF.setWidget(self.series_frame)
        self.addDockWidget(Qt.LeftDockWidgetArea, self.docked_SF)
        self.addDockWidget(Qt.LeftDockWidgetArea, self.docked_CF)
        self.addDockWidget(Qt.RightDockWidgetArea, self.docked_FS)  # Currently under construction
        self.docked_FS.hide()
        self.figure_settings.connect_widgets(container=self.axes_frame)
        self.control_frame.time_filter()

        self.resizeDocks([self.docked_SF], [450], Qt.Horizontal)

        fileMenu = self.menuBar().addMenu('File')
        newAction = QAction('New', self)
        newAction.setShortcut('Ctrl+N')
        newAction.setStatusTip('Open a blank figure')
        newAction.triggered.connect(self.new)
        openAction = QAction('Open', self)
        openAction.setShortcut('Ctrl+O')
        openAction.setStatusTip('Open existing figure')
        openAction.triggered.connect(self.open_fig)
        saveAction = QAction('Save', self)
        saveAction.setShortcut('Ctrl+S')
        saveAction.triggered.connect(self.save_figure)
        exitAction = QAction('Exit', self)
        exitAction.setShortcut('Ctrl+Q')
        exitAction.setStatusTip('Exit application')
        exitAction.triggered.connect(self.close)
        fileMenu.addAction(newAction)
        fileMenu.addAction(openAction)
        fileMenu.addAction(saveAction)
        fileMenu.addAction(exitAction)

        editMenu = self.menuBar().addMenu('Edit')
        undoAction = QAction('Undo', self)
        undoAction.setShortcut('Ctrl+Z')
        undoAction.triggered.connect(self.undo)
        redoAction = QAction('Redo', self)
        redoAction.setShortcut('Ctrl+Y')
        redoAction.triggered.connect(self.redo)
        refreshAction = QAction('Refresh Figure', self)
        refreshAction.setShortcut('Ctrl+R')
        refreshAction.triggered.connect(self.axes_frame.refresh_all)
#        resetAction = QAction('Undo', self)
#        resetAction.setShortcut('Ctrl+Z')  # wrong
#        resetAction.setStatusTip('Undo last action')  #wrong
#        resetAction.triggered.connect(self.undo)  #wrong
        editMenu.addAction(undoAction)
        editMenu.addAction(redoAction)
        editMenu.addAction(refreshAction)
#        editMenu.addAction(resetAction)

        toolsMenu = self.menuBar().addMenu('Tools')
        dataAction = QAction('Manage Data', self)
        dataAction.setShortcut('Ctrl+D')
        dataAction.triggered.connect(self.open_data_manager)
        templateAction = QAction('Import Template', self)
        templateAction.setShortcut('Ctrl+T')
        templateAction.triggered.connect(self.import_template)
        preferencesAction = QAction('Figure Preferences', self)
        preferencesAction.setShortcut('Ctrl+P')
#        preferencesAction.triggered.connect(self.axes_frame.fig_preferences)
        toolsMenu.addAction(dataAction)
        toolsMenu.addAction(templateAction)
        toolsMenu.addAction(preferencesAction)

        viewMenu = self.menuBar().addMenu('View')
        docksAction = QAction('Show/Hide Docks', self)
        docksAction.setShortcut('Ctrl+H')
        docksAction.triggered.connect(self.toggle_docks)
        interactiveAction = QAction('MPL Interactive Mode', self)
        interactiveAction.setShortcut('Ctrl+M')
        interactiveAction.setStatusTip('Toggle Matplotlib\'s interactive mode')
        interactiveAction.triggered.connect(self.toggle_interactive)
        darkAction = QAction('Dark Mode', self)
        darkAction.setShortcut('Ctrl+B')
        darkAction.setStatusTip('Toggle dark user interface')
        darkAction.triggered.connect(self.toggle_dark_mode)
        viewMenu.addAction(docksAction)
        viewMenu.addAction(interactiveAction)
        viewMenu.addAction(darkAction)

        self.showMaximized()
        ### Adding Figure Settings dock to right side currently screws this up
        self.control_frame.setFixedHeight(self.control_frame.height()) #(98 on my screen)
        self.control_frame.setFixedWidth(self.control_frame.width()) #(450 on my screen)

        ### Delete later, just for speed
#        self.open_data_manager()

    def groups_to_contents(self, groups):
        contents = {}
        for group in groups:
            aliases = []
            units = []
            for header in groups[group].series.keys():
                if groups[group].series[header].keep:
                    alias = groups[group].series[header].alias
                    if alias:
                        aliases.append(alias)
                    else:
                        aliases.append(header)
                    units.append(groups[group].series[header].unit)
            contents.update({group: dict(zip(aliases, units))})
        return contents

    def save_figure(self):
        ### Disconnected from button, but still should be connected to menubar action (TBI)
        """Saves figure using PyQt5's file dialog. Default format is .jpg."""
        AF = self.axes_frame
        AF.select_subplot(None, force_select=[])  # force deselect before save (no highlighted axes in saved figure)
        AF.draw()

        ### ONLY JPG WORKS RIGHT NOW. Other functionality coming soon!
        dlg = QFileDialog()
        dlg.setFileMode(QFileDialog.AnyFile)
#        dlg.setConfirmOverwrite(True)
        dlg_output = dlg.getSaveFileName(self, 'Save Figure', os.getcwd(), "JPEG Image (*.jpg);;PNG Image (*.png)")
        plt.savefig(dlg_output[0], dpi=300, format='jpg', transparent=True, bbox_inches='tight')
        TG.statusBar().showMessage('Saved to {}'.format(dlg_output[0]))


    # I could move this and the unit_dicts/clarify dictionaries to DM, and have it read/write from/to a .txt file
    # ^ No, I don't think you can. DM is a QDialog and all its information will be lost when it's closed.
    def get_unit_type(self, unit):
        for e in self.unit_dict:
            if unit in self.unit_dict[e]:
                return e
        return None

    def closeEvent(self, event):
        """Hides any floating QDockWidgets and closes all created figures upon application exit."""
        for dock in [self.docked_CF, self.docked_SF, self.docked_FS]:
            if dock.isFloating(): dock.close()
        plt.close('all')
        event.accept()

    def new(self):
        pass

    def open_fig(self):
        pass

    def undo(self):
        pass

    def redo(self):
        pass

    def refresh_all(self):
        pass

    def open_data_manager(self):
        self.manager = Data_Manager(self)
        self.manager.setModal(True)
        self.manager.show()

    def import_template(self):
        pass

    def toggle_docks(self):
        docks = [self.docked_CF, self.docked_SF, self.docked_FS]
        if any([not dock.isVisible() for dock in docks]):
            for dock in docks: dock.show()
        else:
            for dock in docks: dock.hide()

    def toggle_interactive(self):
        pass

    def toggle_dark_mode(self):
        pass
# Legacy
#    def center(self):
#        qr = self.frameGeometry()
#        cp = QDesktopWidget().availableGeometry().center()
#        qr.moveCenter(cp)
#        self.move(qr.topLeft())

class Axes_Frame(FigureCanvas):
    """Container for figure with subplots. New Axes_Frame objects are created and when a new Figure tab is created (TBI)."""
    def __init__(self, parent):
        self.parent = parent
        self.fig = plt.figure(constrained_layout=False)  # not working with gridspec in controls frame. Look into later.
        super().__init__(self.fig)
        self.weights = [1]
        FS = self.parent.figure_settings
        left = (1-FS.figWidth.value())/2
        right = 1-left
        bottom = (1-FS.figHeight.value())/2
        top = 1-bottom
        gs = gridspec.GridSpec(1, 1, left=left, right=right, bottom=bottom, top=top)
        ax0 = self.fig.add_subplot(gs[0])
        self.subplots = [Subplot_Manager(parent, ax0, index=0, contents={})]
        self.current_sps = []
        self.available_data = self.parent.groups_to_contents(parent.groups)  # holds all unplotted data (unique to each Axes Frame object, see plans for excel tab implementation)
        self.fig.canvas.mpl_connect('button_press_event', self.select_subplot)
        self.fig.suptitle(parent.control_frame.titleEdit.text(), fontsize=20)
        self.draw()

    def refresh_all(self):
        """Refresh entire figure. To be called by TG menubar action and whenever figure_settings/kwargs is updated."""
        TG = self.parent
        FS = TG.figure_settings
        CF = TG.control_frame
        reselect = [sp.index for sp in self.current_sps]
        for ax in self.fig.axes: ax.remove()

        n = max([len(sp.axes[2:]) for sp in self.subplots])
        legOffset = 0
        for sp in self.subplots:
            if sp.legend and sp.contents:
                legOffset = FS.legendOffset.value()
                break
        left = (1 - FS.figWidth.value())/2
        right = 1 - left - FS.parOffset.value()*n - legOffset
        bottom = (1 - FS.figHeight.value())/2
        top = 1 - bottom
        gs = gridspec.GridSpec(len(self.subplots), 1,
                               height_ratios=self.weights,
                               left=left, right=right, bottom=bottom, top=top,
                               hspace=FS.hspace.value())
        for i, sp in enumerate(self.subplots):
            ax = self.fig.add_subplot(gs[i, 0])
            sp.axes = [ax]
            sp.index = i
            sp.plot()

        self.fig.suptitle(CF.titleEdit.text(), fontsize=FS.titleSize.value())

        CF.cleanup_axes()
        CF.weightsEdit.setText(str(self.weights))
        self.select_subplot(None, force_select=[self.subplots[i] for i in reselect])
        self.draw()

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
            highlight(self.subplots, invert=True)
            self.current_sps = []
            highlight(force_select)
        else:
            if event.inaxes is None:
                highlight(self.subplots, invert=True)
                self.current_sps = []
            else:
#                print('event.inaxes:\t', event.inaxes)
#                print('fig.axes:\t', self.fig.axes)
#                print('subplot hosts:\t', [sp.host() for sp in self.subplots])
#                print(event.inaxes.get_yticks())

                #find out which Subplot_Manager contains event-selected axes
                for sm in self.subplots:
                    if event.inaxes in sm.axes:
                        sp = sm
                        break
#                print(sp)
#                sp = self.subplots[[sp.host() for sp in self.subplots].index(event.inaxes)]
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
            SF.search(SF.searchPlotted, SF.plotted, sp.contents)
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

        title = QLabel('Figure title:')
        self.grid.addWidget(title,0,0)

        self.titleEdit = QLineEdit('New_Figure')
        self.titleEdit.returnPressed.connect(self.rename)
        self.grid.addWidget(self.titleEdit,0,1,1,5)

        weighting = QLabel('Weighting:')
        self.grid.addWidget(weighting,1,0,2,1)

        self.weightsEdit = QLineEdit('[1]')
        self.weightsEdit.returnPressed.connect(self.adjust_weights)
        self.grid.addWidget(self.weightsEdit,1,1,2,2)

        selectStart = QLabel('Start Timestamp')
        self.grid.addWidget(selectStart,3,0,2,1)

        self.selectStart = QLineEdit('2018-12-06 00:00')
        self.selectStart.returnPressed.connect(self.time_filter)
        self.grid.addWidget(self.selectStart,3,1,2,2)

        selectEnd = QLabel('End Timestamp')
        self.grid.addWidget(selectEnd,5,0,2,1)

        self.selectEnd = QLineEdit('2018-12-09 00:00')  # dummy start/end from PHI_HK, default will be None
        self.selectEnd.returnPressed.connect(self.time_filter)
        self.grid.addWidget(self.selectEnd,5,1,2,2)

        self.cycle = QPushButton('Cycle Axes')
        self.cycle.clicked.connect(lambda: self.cycle_subplot(parent.axes_frame.current_sps))
        self.grid.addWidget(self.cycle,1,3,2,1)

        self.legendToggle = QCheckBox('Legend')
        self.legendToggle.clicked.connect(lambda: self.toggle_legend(parent.axes_frame.current_sps))
        self.grid.addWidget(self.legendToggle,3,3,2,1)

        self.colorCoord = QCheckBox('Color by Unit')
        self.colorCoord.clicked.connect(lambda: self.color_coordinate(parent.axes_frame.current_sps))
        self.grid.addWidget(self.colorCoord,5,3,2,1)

        self.insert = QPushButton('Insert')
        self.insert.clicked.connect(lambda: self.insert_subplot(parent.axes_frame.current_sps))
        self.grid.addWidget(self.insert,1,4,2,1)

        self.delete = QPushButton('Delete')
        self.delete.clicked.connect(lambda: self.delete_subplot(parent.axes_frame.current_sps))
        self.grid.addWidget(self.delete,3,4,2,1)

        self.clear = QPushButton('Clear')
        self.clear.clicked.connect(lambda: self.clear_subplot(parent.axes_frame.current_sps))
        self.grid.addWidget(self.clear,5,4,2,1)

        self.reorderUp = QPushButton()
        self.reorderUp.setIcon(self.style().standardIcon(getattr(QStyle, 'SP_TitleBarShadeButton')))
        self.reorderUp.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.reorderUp.clicked.connect(lambda: self.reorder(parent.axes_frame.current_sps, 'up'))
        self.grid.addWidget(self.reorderUp,1,5,3,1)

        self.reorderDown = QPushButton()
        self.reorderDown.setIcon(self.style().standardIcon(getattr(QStyle, 'SP_TitleBarUnshadeButton')))
        self.reorderDown.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.reorderDown.clicked.connect(lambda: self.reorder(parent.axes_frame.current_sps, 'down'))
        self.grid.addWidget(self.reorderDown,4,5,3,1)

        self.setLayout(self.grid)

        col_weights = [.01, .01, .01, 1, 1, .01]
        for i,cw in enumerate(col_weights):
            self.grid.setColumnStretch(i,cw)

    def cleanup_axes(self):
        AF = self.parent.axes_frame
        FS = self.parent.figure_settings
        for sp in AF.subplots[:-1]:  # set all xaxes invisible
            sp.host().tick_params(axis='x', which='major', labelbottom=False)
            for ax in sp.axes: ax.tick_params(axis='y', labelsize=FS.tickSize.value())
            # if FS.majorX.isChecked():
            sp.host().grid(b=True, axis='x')
        base_X = AF.subplots[-1].host()
        base_X.grid(b=True, axis='x')
        plt.sca(base_X)
        plt.xticks(rotation=FS.tickRot.value(), ha='right', fontsize=FS.tickSize.value())
        plt.yticks(fontsize=FS.tickSize.value())


    def time_filter(self):
        self.start = pd.to_datetime(self.selectStart.text())
        self.end = pd.to_datetime(self.selectEnd.text())
        if not self.start: self.start = min([self.groups[name].data.index[0] for name in self.groups.keys()])
        if not self.end: self.end = max([self.groups[name].data.index[-1] for name in self.groups.keys()])

        # doch you do need them because they're strings (I think) (dunno if it'll stay that way)
        self.timespan = pd.to_datetime(self.end)-pd.to_datetime(self.start)  # shouldn't need to use pd.to_datetime here, self.start/end should already be datetimes at this point
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
        self.parent.axes_frame.refresh_all()

    def reorder(self, sps, direction):
        """Reorders selected subplot up or down and updates weighting field."""
        TG = self.parent
        AF = TG.axes_frame
        FS = TG.figure_settings
        if len(sps) == 1:
            if direction == 'up':
                inc = -1
            if direction == 'down':
                inc = 1
            sp = sps[0]
            i = sp.index
            j = i+inc
            if 0 <= j < len(AF.subplots):  # do nothing if moving sp up or down would put it past the first/last index
                AF.weights[i], AF.weights[j] = AF.weights[j], AF.weights[i]
                AF.subplots[i], AF.subplots[j] = AF.subplots[j], AF.subplots[i]
                AF.refresh_all()
        else:
            TG.statusBar().showMessage('Select one subplot to reorder')


    def insert_subplot(self, sps):
        """Inserts subplot at top of figure. (Indexed insertion not working)"""
        TG = self.parent
        AF = TG.axes_frame

        # Determine index at which to insert blank subplot
        if len(sps) != 1:
            index = len(AF.subplots)-1
            TG.statusBar().showMessage('No singular subplot selected. Subplot inserted at end.')
        else:
            index = sps[0].index

        # Insert blank Subplot_Manager at position below index (I feel like I shouldn't have to explicitly assign default arguments here, but hey)
        AF.subplots.insert(index+1, Subplot_Manager(TG, [None], order=[None], contents={}, index=None, legend=False, colorCoord=False))
        AF.weights.insert(index+1, 1)
        AF.refresh_all()


    def delete_subplot(self, sps):
        """Deletes selected subplot(s) and adds contents back into available tree."""
        TG = self.parent
        if sps:
            AF = TG.axes_frame
            if len(AF.subplots) == 1:
                self.clear_subplot(sps)
            else:
                # Delete entries at selected indices from weights, current selection, and Subplot_Managers
                SF = TG.series_frame
                indices = [sp.index for sp in sps]

                for i in sorted(indices, reverse=True):
                    AF.available_data = SF.add_to_contents(AF.available_data, AF.subplots[i].contents)
                    SF.populate_tree(AF.available_data, SF.available)  # add contents back into available tree
                    del AF.weights[i]
                    del AF.subplots[i]
                AF.current_sps = []  # deselect everything
                AF.refresh_all()
        else:
            TG.statusBar().showMessage('Select one or more subplots to delete')


    def clear_subplot(self, sps):
        """Adds selected subplot's contents back into available tree, clears axis."""
        TG = self.parent
        if sps:
            AF = TG.axes_frame
            SF = TG.series_frame
            SF.plotted.clear()
            for sp in sps:
                AF.available_data = SF.add_to_contents(AF.available_data, sp.contents)
                SF.populate_tree(AF.available_data, SF.available)
                SF.search(SF.searchAvailable, SF.available, AF.available_data)
                sp.contents = {}
                sp.order = [None]
            AF.refresh_all()
#            if len(sps) > 1: TG.statusBar().showMessage('Cleared subplots: {}'.format(sorted([sp.index for sp in sps])))
#            else: TG.statusBar().showMessage('Cleared subplot: {}'.format(sps[0].index))
        else:
            TG.statusBar().showMessage('Select one or more subplots to clear')


    def toggle_legend(self, sps):
        """Toggles legend display of selected subplot."""
        TG = self.parent
        if sps:
            AF = TG.axes_frame
            if len(sps) == 1:
                sp = sps[0]
                sp.legend = not sp.legend
            else:
                any_legend = any([sp.legend for sp in sps])
                for sp in sps:
                    sp.legend = not any_legend
            AF.refresh_all()
        else:
            self.legendToggle.setCheckable(False)
            TG.statusBar().showMessage('Select one or more subplots to toggle legend')


    def color_coordinate(self, sps):
        """Recolors lines and axes in selected subplot to correspond by unit type."""
        TG = self.parent
        if sps:
            AF = TG.axes_frame
            if len(sps) == 1:
                sp = sps[0]
                sp.colorCoord = not sp.colorCoord
            else:
                any_coord = any([sp.colorCoord for sp in sps])
                for sp in sps:
                    sp.colorCoord = not any_coord
            AF.refresh_all()
        else:

            self.colorCoord.setCheckable(False)
            TG.statusBar().showMessage('Select one or more subplots to toggle color coordination')


    def cycle_subplot(self, sps):
        """Cycles through unit order permutations."""
        TG = self.parent
        if sps:
            AF = TG.axes_frame
            for sp in sps:
                perms = [list(p) for p in sorted(itertools.permutations(sp.order))]
                i = perms.index(sp.order)
                sp.order = perms[(i+1)%len(perms)]
            AF.refresh_all()
        else:
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
        AF.weights = weights
        AF.refresh_all()

    def rename(self):
        """Renames figure and changes save path to new figure title."""
        TG = self.parent
        AF = TG.axes_frame
        FS = TG.figure_settings
        fig_title = re.sub('[\\\\.]', '', self.titleEdit.text())  # get rid of any backslashes or dots
        if not fig_title:
            AF.fig.suptitle('')
            fig_title = 'New_Figure'
        else:
            AF.fig.suptitle(fig_title, fontsize=FS.titleSize.value())
#        input_path = self.pathEdit.text()
#        try:
#            save_dir = input_path[:input_path.rindex('\\')]  # path string up until last backslash occurrence
#        except ValueError:
#            save_dir = os.getcwd()
#        try:
#            ext = input_path[input_path.rindex('.'):]  # path string from last . occurrence to end
#        except ValueError:
#            ext = '.jpg'  # default to JPG format
#        self.pathEdit.setText(save_dir + '\\' + fig_title + ext)
        AF.draw()

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
        self.available.setSelectionMode(QTreeWidget.ExtendedSelection)
        self.available.setSortingEnabled(True)
        self.available.setHeaderLabels(["Available Series", "Unit"])
        self.available.setColumnCount(ncols)
        self.plotted = QTreeWidget(w)
        self.plotted.setSelectionMode(QTreeWidget.ExtendedSelection)
        self.plotted.setSortingEnabled(True)
        self.plotted.setHeaderLabels(["Plotted Series", "Unit"])
        self.available.setColumnCount(ncols)
        self.add = QPushButton('Add')
        self.add.clicked.connect(lambda: self.transfer('Add'))
        self.remove = QPushButton('Remove')
        self.remove.clicked.connect(lambda: self.transfer('Remove'))
        self.searchAvailable = QLineEdit()
        self.searchAvailable.setPlaceholderText('Search')
        self.searchAvailable.textChanged.connect(lambda: self.search(self.searchAvailable, self.available, self.parent.axes_frame.available_data))
        self.searchPlotted = QLineEdit()
        self.searchPlotted.setPlaceholderText('Search')
        self.searchPlotted.textChanged.connect(lambda: self.search(self.searchPlotted, self.plotted, self.get_sp_contents()))

        grid.addWidget(self.searchAvailable, 0, 0)
        grid.addWidget(self.searchPlotted, 0, 1)
        grid.addWidget(self.available, 1, 0)
        grid.addWidget(self.plotted, 1, 1)
        grid.addWidget(self.add, 2, 0)
        grid.addWidget(self.remove, 2, 1)
        self.setLayout(grid)

        self.populate_tree(parent.axes_frame.available_data, self.available)
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

#    def read_tree(self, tree):
#        """Reads tree into standard contents format {name: {headers:units}}."""
#        level0s = [tree.topLevelItem(i) for i in range(tree.topLevelItemCount())]
#        if level0s:
#            groups = [n.text(0) for n in level0s]
#            headers = [[level0.child(i).text(0) for i in range(level0.childCount())] for level0 in level0s]
#            units = [[level0.child(i).text(1) for i in range(level0.childCount())] for level0 in level0s]
#            contents = {}
#            for n,s,u in zip(groups, headers, units):
#                contents[n] = dict(zip(s,u))
#        else:
#            contents = {}
#        return contents

    def add_to_contents(self, contents, to_add):
        for group, headers_units in to_add.items():
            if group in contents:
                for header, unit in headers_units.items():
                    contents[group].update({header:unit})
            else:
                contents.update({group: headers_units})
        return contents
#        for group in to_add():
#            if group in contents:
#                for header in to_add[group].series:
#                    contents[group].series.update({header: to_add[group].series})
#            else:
#                contents.update({group: to_add[group]})
#        return contents


    def remove_from_contents(self, contents, to_remove):
        for group, headers_units in to_remove.items():
            if group in contents:
                for header, unit in headers_units.items():
                    del contents[group][header]
                if not contents[group]:
                    del contents[group]
        return contents
#        for group in to_remove:
#            if group in contents:
#                for header in to_remove[group].series:
#                    del contents[group].series[header]
#                if not contents[group].series:  # delete any groups with empty series dict
#                    del contents[group]
#        return contents

    def populate_tree(self, contents, target_tree):
        """Clears target_tree and repopulates with contents"""
        # populate tree with contents
        target_tree.clear()
        if contents:
            for group, headers_units in contents.items():
                level0 = QTreeWidgetItem([group])
                target_tree.addTopLevelItem(level0)
                for header, unit in headers_units.items():  # add series/units to their corresponding level0 entry
                    level1 = QTreeWidgetItem([header, unit])
                    level0.addChild(level1)
                level0.setExpanded(True)
            target_tree.resizeColumnToContents(0)

            self.cleanup()

#        """Adds contents to target_tree with no repeats and sorts. Manages available/plotted datasets."""

#        if contents:
#            target_level0 = [target_tree.topLevelItem(i) for i in range(target_tree.topLevelItemCount())]
#            target_names = [n.text(0) for n in target_level0]
#            for name, headers_units in contents.items():
#                if name in target_names:  # if dataframe already exists in target_tree, get its level0 entry
#                    i = target_names.index(name)
#                    level0 = target_level0[i]
#                else:  # if not, create it and add it
#                    level0 = QTreeWidgetItem([name])
#                    target_tree.addTopLevelItem(level0)
#                for series, unit in headers_units.items():  # add series/units to their corresponding level0 entry
#                    level1 = QTreeWidgetItem([series, unit])
#                    level0.addChild(level1)
#                level0.setExpanded(True)
#            target_tree.resizeColumnToContents(0)
#
#            self.cleanup()

    def update_subplot_contents(self, sp, contents):
        """Updates selected subplots' contents and order."""
        all_units = []
        for headers_units in contents.values():
            all_units.extend(headers_units.values())
        sp.order = [u for u in sp.order if u in all_units]
        if not sp.order: sp.order = [None]
        sp.contents = copy.deepcopy(contents)
        # Deep copy seems like it should be unnecessary but it prevents sp.contents from being carried over between instances.
        # Can probably remove at full rollout. See also deep copies of data and data_dict in Figure Window __init__()
        # Probably takes a lot of memory

    def transfer(self, caller):
        """Swaps series or entire dataframe references from available to plotted or vice versa."""
        TG = self.parent
        AF = TG.axes_frame
        selected_sps = AF.current_sps
        if not selected_sps:
            TG.statusBar().showMessage('Select a subplot to add or remove series')
        elif len(selected_sps) > 1:
            TG.statusBar().showMessage('Series can only be added to one subplot')
        else:
            sp = selected_sps[0]
            if caller == 'Add':
                sourceTree = self.available
                availableFunc = self.remove_from_contents
                plottedFunc = self.add_to_contents
            if caller == 'Remove':
                sourceTree = self.plotted
                availableFunc = self.add_to_contents
                plottedFunc = self.remove_from_contents

            selected = sourceTree.selectedItems()
            if selected:
                # Read contents from selected items
                contents = {}
                if all(item.parent() is None for item in selected):  # if only level0 items in selection
                    for item in selected:
                        children = [item.child(i) for i in range(item.childCount())]
                        for child in children: item.removeChild(child)
                        group = item.text(0)
                        headers = [child.text(0) for child in children]
                        units = [child.text(1) for child in children]
                        contents = self.add_to_contents(contents, {group: dict(zip(headers, units))})
                else:
                    for item in selected:
                        if item.parent():  # if selected item is level1 (ignore if level0)
                            parent = item.parent()
                            i = parent.indexOfChild(item)
                            child = parent.takeChild(i)
                            group = parent.text(0)
                            header = child.text(0)
                            unit = child.text(1)
                            contents = self.add_to_contents(contents, {group: {header:unit}})
                # Add/remove contents from sp
                self.update_subplot_contents(sp, plottedFunc(sp.contents, contents))
                # Refresh sp
                sp.plot()
                AF.refresh_all()
                # Transfer contents to/from available_data
                AF.available_data = availableFunc(AF.available_data, contents)
                # Populate both trees with un-search-filtered data
                self.populate_tree(AF.available_data, self.available)
                self.populate_tree(sp.contents, self.plotted)
                self.cleanup()
                # Reapply search filters
                self.search(self.searchAvailable, self.available, AF.available_data)
                self.search(self.searchPlotted, self.plotted, sp.contents)
            else:
                TG.statusBar().showMessage('No series selected')

    def get_sp_contents(self):
        TG = self.parent
        AF = TG.axes_frame
        if len(AF.current_sps) == 1:
            contents = AF.current_sps[0].contents
        else:
            contents = {}
        return contents

    def search(self, search_bar, tree, data_set):
        """Displays only series in tree which match input to search_bar (case insensitive)"""
        user_input = re.compile(search_bar.text(), re.IGNORECASE)
        matches = {}
        if data_set:
            for group, headers_units in data_set.items():
                for header, unit in headers_units.items():
                    if user_input.search(header):
                        matches = self.add_to_contents(matches, {group: {header:unit}})
            self.populate_tree(matches, tree)
#            self.cleanup()

#        level0s = [tree.topLevelItem(i) for i in range(tree.topLevelItemCount())]
#        if level0s:
#            names = [n.text(0) for n in level0s]
#            series = [[level0.child(i).text(0) for i in range(level0.childCount()) if user_input.search(level0.child(i).text(0))] for level0 in level0s]
#            units = [[level0.child(i).text(1) for i in range(level0.childCount()) if user_input.search(level0.child(i).text(0))] for level0 in level0s]
#            contents = {}
#            for n,s,u in zip(names, series, units):
#                contents[n] = dict(zip(s,u))
#            tree.clear()
#            self.populate_tree(contents, tree)
#            self.cleanup()

class QColorButton(QPushButton):
        def __init__(self, parent, color, unit_type):
            super(QColorButton, self).__init__()
            self.parent = parent
            self.color = color
            self.setStyleSheet("background-color:{};".format(color))
            self.unit_type = unit_type


class Figure_Settings(QWidget):
    def __init__(self, parent, saved=None):
        super().__init__()
        self.parent = parent
        TG = self.parent

        mpl.rc('font', family='serif')  # controlable later maybe
        # Read saved values from .txt file

        grid = QGridLayout()

        figBounds = QLabel('Figure Dimensions')
        figBounds.setAlignment(Qt.AlignCenter)
        figHeight = QLabel('Height')
        self.figHeight = QDoubleSpinBox()
        self.figHeight.setRange(0, 1)
        self.figHeight.setSingleStep(.01)
        self.figHeight.setValue(.90)
        figWidth = QLabel('Width')
        self.figWidth = QDoubleSpinBox()
        self.figWidth.setRange(0, 1)
        self.figWidth.setSingleStep(.01)
        self.figWidth.setValue(.90)
        hspace = QLabel('V Offset')
        self.hspace = QDoubleSpinBox()
        self.hspace.setRange(0, 1)
        self.hspace.setSingleStep(.01)
        self.hspace.setValue(.05)
        parOffset = QLabel('H Offset')
        self.parOffset = QDoubleSpinBox()
        self.parOffset.setRange(0, 1)
        self.parOffset.setSingleStep(.01)
        self.parOffset.setValue(.05)
        legendOffset = QLabel('Legend Offset')
        self.legendOffset = QDoubleSpinBox()
        self.legendOffset.setRange(0, 1)
        self.legendOffset.setSingleStep(.01)
        self.legendOffset.setValue(.1)

        gridToggles = QLabel('Grid Settings')
        gridToggles.setAlignment(Qt.AlignCenter)
        self.majorXgrid = QCheckBox('Major X')
        self.minorXgrid = QCheckBox('Minor X')
        self.majorYgrid = QCheckBox('Major Y')
        self.minorYgrid = QCheckBox('Minor Y')

        textSettings = QLabel('Text Settings')
        textSettings.setAlignment(Qt.AlignCenter)
        titleSize = QLabel('Title')
        self.titleSize = QSpinBox()
        self.titleSize.setRange(0, 60)
        self.titleSize.setValue(20)
        labelSize = QLabel('Axis Labels')
        self.labelSize = QSpinBox()
        self.labelSize.setRange(0, 60)
        self.labelSize.setValue(12)
        tickSize = QLabel('Tick Size')
        self.tickSize = QSpinBox()
        self.tickSize.setRange(0, 20)
        self.tickSize.setValue(10)
        tickRot = QLabel('Tick Rotation')
        self.tickRot = QSpinBox()
        self.tickRot.setRange(0, 90)
        self.tickRot.setValue(50)

        self.dlg = QColorDialog()
        for i, unit_type in enumerate(TG.unit_dict):
            self.dlg.setCustomColor(i, QColor(mcolors.to_hex(TG.color_dict[unit_type])))

        self.unit_table = QTableWidget()
        self.unit_table.setColumnCount(2)
        self.unit_table.setRowCount(len(TG.unit_dict))

        for i, unit_type in enumerate(TG.unit_dict):
            self.unit_table.setItem(i, 0, QTableWidgetItem(unit_type))
            colorButton = QColorButton(self, mcolors.to_hex(TG.color_dict[unit_type]), unit_type)
            colorButton.clicked.connect(self.pick_color)
            self.unit_table.setCellWidget(i, 1, colorButton)

        widgets = [
                figBounds,
                figHeight,
                self.figHeight,
                figWidth,
                self.figWidth,
                hspace,
                self.hspace,
                parOffset,
                self.parOffset,
                legendOffset,
                self.legendOffset,

                gridToggles,
                self.majorXgrid,
                self.minorXgrid,
                self.majorYgrid,
                self.minorYgrid,

                textSettings,
                titleSize,
                self.titleSize,
                labelSize,
                self.labelSize,
                tickSize,
                self.tickSize,
                tickRot,
                self.tickRot,

                self.unit_table,
                ]

        positions = [
                (4,0,1,2),  # Figure Dimensions
                (5,0,1,1),
                (5,1,1,1),
                (6,0,1,1),
                (6,1,1,1),
                (7,0,1,1),
                (7,1,1,1),
                (8,0,1,1),
                (8,1,1,1),
                (9,0,1,1),
                (9,1,1,1),

                (11,0,1,2),  # Grid Settings
                (12,0,1,1),
                (12,1,1,1),
                (13,0,1,1),
                (13,1,1,1),

                (15,0,1,2),  # Text Settings
                (16,0,1,1),
                (16,1,1,1),
                (17,0,1,1),
                (17,1,1,1),
                (18,0,1,1),
                (18,1,1,1),
                (19,0,1,1),
                (19,1,1,1),

                (21,0,1,2),  # Color Palette
                ]

        for w, p in zip(widgets, positions):
            grid.addWidget(w, *p)
        self.setLayout(grid)

    def connect_widgets(self, container):
        widgets = [
                self.figHeight,
                self.figWidth,
                self.hspace,
                self.parOffset,
                self.legendOffset,

                self.majorXgrid,
                self.minorXgrid,
                self.majorYgrid,
                self.minorYgrid,

                self.titleSize,
                self.labelSize,
                self.tickSize,
                self.tickRot,

                self.unit_table,
                ]
        for w in widgets[0:5]:
            w.valueChanged.connect(container.refresh_all)
        for w in widgets[9:13]:
            w.valueChanged.connect(container.refresh_all)

    def pick_color(self):
        colorButton = QObject.sender(self)
        unit_type = colorButton.unit_type
        if colorButton.color:
            self.dlg.setCurrentColor(QColor(colorButton.color))

        if self.dlg.exec_():
            colorButton.color = self.dlg.currentColor().name()
            colorButton.setStyleSheet("background-color:{};".format(colorButton.color))
            self.color_dict[unit_type] = colorButton.color

class Data_Manager(QDialog):
    def __init__(self, parent):
        super().__init__()
        self.parent = parent
        self.setWindowTitle('Data Manager')
        self.setWindowIcon(QIcon('satellite.png'))

        self.groups = copy.deepcopy(parent.groups)  # copy so that if you can still discard changes
        self.group_reassign = {name:[] for name in self.groups}  # for renaming groups
#        print(self.group_reassign)
        self.modified = False

        self.resize(1000,500)
        self.grid = QGridLayout()
        self.tabBase = QTabWidget()
        self.tabBase.setStyleSheet("QTabBar::tab {height: 30px; width: 300px} QTabWidget::tab-bar {alignment:center;}")
        self.tabBase.currentChanged.connect(self.refresh_tab)
        self.save = QPushButton('Save')
        self.save.setDefault(True)
        self.save.clicked.connect(self.save_changes)
        self.cancel = QPushButton('Cancel')
        self.cancel.clicked.connect(self.close)  # AttributeError: 'bool' object has no attribute 'accept' -> from event.accept()
        msgLog = QLabel('Message Log:')
        self.messageLog = QTextEdit()
        self.messageLog.setReadOnly(True)
        self.messageLog.setText('Ready')

        self.grid.addWidget(self.tabBase,0,0,1,3)
        self.grid.addWidget(msgLog,1,0)
        self.grid.addWidget(self.messageLog,1,1,2,1)
        self.grid.addWidget(self.save,1,2)
        self.grid.addWidget(self.cancel,2,2)
        self.grid.setColumnStretch(1,100)
        #self.messageLog.resize(self.messageLog.width(),100)

        self.setLayout(self.grid)
        self.import_tab = Import_Tab(self)
        self.dataframes_tab = DataFrames_Tab(self)
        self.configure_tab = Configure_Tab(self)
        self.tabBase.addTab(self.import_tab, 'Import')
        self.tabBase.addTab(self.configure_tab, 'Configure')
        self.tabBase.addTab(self.dataframes_tab, 'DataFrames')

    def keyPressEvent(self, event):
        """Close application from escape key.

        results in QMessageBox dialog from closeEvent, good but how/why?
        """
        if event.key() == Qt.Key_Escape:
            self.close()

    def refresh_tab(self, tab_index):
        if self.tabBase.currentIndex() == 1:  # hard coded - this will break if I ever rearrange the tabs. But I think that's ok.
            # Configure Tab
            self.configure_tab.display_header_info()
        elif self.tabBase.currentIndex() == 2:
            # DataFrames Tab
            self.dataframes_tab.display_dataframe()

    def popup(self, text, informative=None, details=None, buttons=2):
        """Brings up a message box with provided text and returns Ok or Cancel."""
        self.prompt = QMessageBox()
        self.prompt.setWindowTitle("HEY.")
        self.prompt.setIcon(QMessageBox.Question)
        self.prompt.setText(text)
        if buttons == 2:
            self.prompt.setStandardButtons(QMessageBox.Ok | QMessageBox.Cancel)
        elif buttons == 1:
            self.prompt.setStandardButtons(QMessageBox.Ok)
        self.prompt.setInformativeText(informative)
        self.prompt.setDetailedText(details)
        self.prompt.show()
        return self.prompt.exec_()

    def feedback(self, message, mode='line'):
        """Adds message to message log as one line. Set overwrite=True to overwrite the last line in the log."""
        if mode == 'line':
            self.messageLog.setText(self.messageLog.toPlainText() + '\n' + message)
        elif mode == 'append':
            self.messageLog.setText(self.messageLog.toPlainText() + message)
        elif mode == 'overwrite':
            current_text = self.messageLog.toPlainText()
            self.messageLog.setText(current_text[:current_text.rfind('\n')+1] + message)
        self.messageLog.verticalScrollBar().setValue(self.messageLog.verticalScrollBar().maximum())

    def save_changes(self):
        if self.modified:
            TG = self.parent
            SF = TG.series_frame
            ### Eventually, loop this through all open axes frames (excel tab implementation)
            AF = TG.axes_frame
            TG.groups = self.groups

            # Get new alias/unit information from self.groups
            new_contents = TG.groups_to_contents(self.groups)

            # Rename/delete groups in subplots first
            for sp in AF.subplots:
                for group in copy.deepcopy(tuple(sp.contents.keys())):
#                    print('MW group: ',group)
                    if group not in new_contents:  # if not recognized
#                        print('group_reassign: ',self.group_reassign)
                        if group in self.group_reassign:  # check if it's been renamed
                            new_name = self.group_reassign[group][-1]
                            sp.contents[new_name] = sp.contents[group]  # if so, take the most recent renaming
                        del sp.contents[group]  # scrap the old one
#                print('sp.contents: ',sp.contents)

            # Rename/delete series in subplots
            for sp in AF.subplots:
                for group in sp.contents:
                    aliases = copy.deepcopy(tuple(sp.contents[group].keys()))  # define loop elements first so it doesn't change size during iteration
#                    print('aliases: ', aliases)
                    new_series = self.groups[group].series
#                    print('new series: ',new_series.keys())
                    for alias in aliases:
                        del sp.contents[group][alias]  # scrap old alias entry (no matter what)
#                        print('sp.contents after del: ', sp.contents)
#                        print('\ncurrent alias_dict: ',self.parent.groups[group].alias_dict)
                        try:
                            header = self.parent.groups[group].alias_dict[alias]  # get original header of each alias in sp.contents
                        except KeyError:  # if original header being used as alias (because no alias was assigned)
                            header = alias
#                        print('alias: header  ->  ', alias,': ',header)
                        if header in new_series and new_series[header].keep:  # if original header recognized in new groups
                            new_alias = new_series[header].alias
                            if not new_alias: new_alias = header
#                            print('new alias: ',new_alias)
                            sp.contents[group][new_alias] = new_series[header].unit  # make new entry with new_alias
                            del new_contents[group][new_alias]
#                            print('sp.contents after replace: ',sp.contents)
                              # delete the entry in new_contents so we can just dump the rest into AF.available_data
                        if not new_contents[group]: del new_contents[group]  # scrap any now-empty groups
#                        print('new contents after replace: ',new_contents)
                sp.plot()
            AF.draw()

            # Dump everything else into AF.available_data
            AF.available_data = new_contents
            SF.available.clear()
            SF.search(SF.searchAvailable, SF.available, AF.available_data)

            sp = AF.current_sps
            if len(sp) == 1:
                SF.plotted.clear()
                SF.search(SF.searchPlotted, SF.plotted, sp[0].contents)
            self.feedback('Saved data to main window.')
            self.modified = False


    def closeEvent(self, event):
        if self.modified:
            if self.popup('Discard changes?') == QMessageBox.Cancel:
                event.ignore()
            else:
                QApplication.clipboard().clear()
                event.accept()
        else:
            QApplication.clipboard().clear()
            event.accept()

class Import_Tab(QWidget):
    def __init__(self, parent):
        super().__init__()
        self.parent = parent
        self.grid = QGridLayout()
        self.path_dict = {}
        self.dir = os.getcwd()
        self.auto_parse = True

#        self.dir = r'C:\Users\seery\Documents\German (the person)\PHI_data_housekeeping\CSV'  # delete later, just for quicker access

#        dirLabel = QLabel('Directory:')
        self.browse = QPushButton()
        self.browse.setIcon(self.style().standardIcon(getattr(QStyle, 'SP_DialogOpenButton')))
        self.browse.clicked.connect(self.browse_dialog)
        self.directory = QLineEdit(self.dir)
        self.directory.returnPressed.connect(self.search_dir)
        self.fileSearch = QLineEdit()
        self.fileSearch.setPlaceholderText('Search')
        self.fileSearch.textChanged.connect(self.filter_files)
        self.fileSearch.setFocus(True)
        self.groupName = QLineEdit('Test')  # delete initial text later
        self.groupName.setPlaceholderText('Group Name')
        self.autoParseCheck = QCheckBox('Automatically parse units from headers')
        self.autoParseCheck.setChecked(True)
        self.autoParseCheck.stateChanged.connect(self.toggle_auto_parse)
        foundFilesLabel = QLabel('Found Files')
        groupFilesLabel = QLabel('Files in Group')
        importedGroupsLabel = QLabel('Imported Groups')
        self.foundFiles = QListWidget()
        self.foundFiles.setSelectionMode(QListWidget.ExtendedSelection)
        self.groupFiles = QListWidget()
        self.groupFiles.setSelectionMode(QListWidget.ExtendedSelection)
        self.importedGroups = QListWidget()
        self.importedGroups.addItems(self.parent.groups.keys())
        self.add = QPushButton('Add to Group')
        self.add.clicked.connect(lambda: self.toggle_file_active('Add'))
        self.remove = QPushButton('Remove from Group')
        self.remove.clicked.connect(lambda: self.toggle_file_active('Remove'))
        self.editGroup = QPushButton('Rename Group')
        self.editGroup.clicked.connect(self.rename_group)
        self.importSettings = QPushButton('Import Settings')
        self.importSettings.clicked.connect(self.open_import_settings)
        self.importGroup = QPushButton('Import Group')
        self.importGroup.clicked.connect(self.import_group)
        self.deleteGroup = QPushButton('Delete Group')
        self.deleteGroup.clicked.connect(self.delete_group)


        #row_weights = [1, 1, 1, 1, 1, 1]
        #for i,rw in enumerate(row_weights):
        #    self.import_tab.grid.setRowStretch(i,rw)
        #col_weights = [1, 1, 1, 1, 1, 1]
        #for i,cw in enumerate(col_weights):
        #    self.import_tab.grid.setColumnStretch(i,cw)

        widgets = [
#                dirLabel,
                self.browse,
                self.directory,
                self.fileSearch,
                self.groupName,
                self.autoParseCheck,
                foundFilesLabel,
                groupFilesLabel,
                importedGroupsLabel,
                self.foundFiles,
                self.groupFiles,
                self.importedGroups,
                self.add,
                self.remove,
                self.editGroup,
                self.importSettings,
                self.importGroup,
                self.deleteGroup,
                ]
        positions = [
                (0,0,1,1),
                (0,1,1,3),
#                (0,3,1,1),
                (1,1,1,1),
                (1,2,1,1),
                (1,3,1,1),
                (2,1,1,1),
                (2,2,1,1),
                (2,3,1,1),
                (3,1,1,1),
                (3,2,1,1),
                (3,3,1,1),
                (4,1,1,1),
                (4,2,1,1),
                (4,3,1,1),
                (5,1,1,1),
                (5,2,1,1),
                (5,3,1,1),
                ]

        for w, p in zip(widgets, positions):
            self.grid.addWidget(w, *p)
        self.setLayout(self.grid)
        self.search_dir()


    def toggle_auto_parse(self):
        self.auto_parse = self.autoParseCheck.isChecked()

    def search_dir(self):

        def gather_files(path):
            """Returns list of file names in directory path which match types in filetypes.
            Excludes temporary files.
            Does not search subfolders.
            Also returns dictionary associating files to their source paths."""
            found_files = []
            path_dict = {}
            filetypes = re.compile(r'(csv|zip|txt|xls|xlsx)$')
            exclude = re.compile(r'^~\$')
            for file in os.listdir(path):
                if re.search(filetypes, file) and not re.search(exclude, file):
                    found_files.append(file)
                    path_dict[file] = os.path.join(path, file)
            return found_files, path_dict

        path = self.directory.text()
        self.dir = path
        self.loaded_files, new_path_dict_entries = gather_files(path)
        self.path_dict.update(new_path_dict_entries)
        self.fileSearch.setText('')
        self.foundFiles.clear()
        self.foundFiles.addItems(self.loaded_files)
        TG = self.parent.parent
        for file in self.path_dict:
            if file not in TG.path_kwargs:
                TG.path_kwargs[self.path_dict[file]] = {'header':'Auto', 'index_col':'Auto', 'skiprows':None}

    def browse_dialog(self):
        path = str(QFileDialog.getExistingDirectory(self, "Select Directory"))
        self.directory.setText(path)
        self.search_dir()

    def filter_files(self):
        pattern = re.compile(self.fileSearch.text(), re.IGNORECASE)
        matches = [item for item in self.loaded_files if re.search(pattern,item)]
        self.foundFiles.clear()
        self.foundFiles.addItems(matches)

    def toggle_file_active(self, caller):
        if caller == 'Add':
            for file in self.foundFiles.selectedItems():
                if file.text() in [self.groupFiles.item(i).text() for i in range(self.groupFiles.count())]:
                    DM.feedback('{} already added.\n'.format(file.text()))
                else:
                    self.groupFiles.addItem(file.text())
        elif caller == 'Remove':
            for file in self.groupFiles.selectedItems():
                self.groupFiles.takeItem(self.groupFiles.row(file))

    def rename_group(self):
        DM = self.parent
        try:
            item = self.importedGroups.selectedItems()[0]
            group = item.text()
            new_name, ok = QInputDialog.getText(self, 'Rename Group \"{}\"'.format(group), 'New group name:')
            if ok:
                DM.groups[new_name] = DM.groups[group]
                del DM.groups[group]
                for name in DM.group_reassign:
                    if group == name or group in DM.group_reassign[name]:
                        DM.group_reassign[name].append(new_name)
                        break
                i = self.importedGroups.row(item)
                self.importedGroups.takeItem(i)
                self.importedGroups.insertItem(i, QListWidgetItem(new_name))
                i = DM.dataframes_tab.selectGroup.findText(group)
                DM.dataframes_tab.selectGroup.removeItem(i)
                DM.dataframes_tab.selectGroup.insertItem(i, new_name)
                i = DM.configure_tab.selectGroup.findText(group)
                DM.configure_tab.selectGroup.removeItem(DM.configure_tab.selectGroup.findText(group))
                DM.configure_tab.selectGroup.insertItem(i, new_name)
                DM.modified = True
        except IndexError:
            pass

    def open_import_settings(self):
        self.settingsDialog = Import_Settings(self)
        self.settingsDialog.setModal(True)
        self.settingsDialog.show()

    def parse_df_origin(self, path, read_func):
        """Searches through first 10 rows for the first datetime and returns the cell above it as label origin."""
        nrows = 10
        n = 1
        while n <= nrows:  # avoid asking for more rows than there are
            try:
                df = read_func(path, nrows=n, header=None)
                n += 1
            except IndexError:
                if 'df' not in locals(): df = pd.DataFrame()
                break

        for c in range(len(df.columns)):
            for r in range(len(df.index)):
                try:
                    ts0 = pd.to_datetime(df.iloc[r,c], infer_datetime_format=True)
                    if ts0 is not pd.NaT:
                        if not r:  # if first row is parseable, inconclusive
                            r = None
                        else:  # else return cell above first parseable cell
                            r = r-1
                        return df, r, c
                except ValueError:
                    pass
        return df, None, None

    def import_group(self):

        def floatify(data):
            """Strip everything but numbers, minus signs, and decimals, and returns data as a float. Returns NaN if not possible. Try to convert booleans to 1/0."""
            if str(data).lower() in ('on','true','yes','enabled'): return 1.0
            if str(data).lower() in ('off','false','no','disabled'): return 0.0
            try:
                scrubbed = re.sub('[^0-9-.]', '', str(data))
                scrubbed = re.sub(',', '.', scrubbed)  # allow for German-style decimals (1,2 -> 1.2 but 1,2 -> 1.2. will still fail appropriately)
                return float(scrubbed)
            except ValueError:
                return np.nan

        def parse_unit(header):
            regex = re.compile('(\[|\()([a-z]|[A-Z])*(\]|\))')  # matches [letters] or (letters) anywhere in header
            parsed = None
            for parsed in re.finditer(regex, header):  # parsed ends up as last match
                pass
            if parsed:
                parsed = parsed.group(0)[1:-1]  # return parsed unit without the brackets
                if parsed in DM.parent.unit_clarify:
                    parsed = DM.parent.unit_clarify[parsed]
                if DM.parent.get_unit_type(parsed) is not None:
                    return parsed
            return None

        def combine_files(pathlist):
            dflist = []
            counter = 1
            for path in pathlist:
                mode = 'line' if counter == 1 else 'overwrite'
                DM.feedback('Reading files into group \"{}\": ({}/{}) ... '.format(self.groupName.text(), counter, len(pathlist)), mode=mode)
                DM.messageLog.repaint()
                counter += 1

                # Get parse kwargs associated with file
                kwargs = {}
                parse_kwargs = TG.path_kwargs[path]
                kwargs.update(parse_kwargs)
                if path.endswith('xls') or path.endswith('xlsx'):
                    read_func = pd.read_excel
                elif path.endswith('csv') or path.endswith('zip'):
                    read_func = pd.read_csv
                    kwargs.update({'encoding':'ISO-8859-1', 'sep':',', 'engine':'python'})

                # Take header_row and index_col as intersecting cell above first parseable datetime
                warnings.filterwarnings('ignore')  # to ignore UserWarning: Discarding nonzero nanoseconds in conversion
                _, kwargs['header'], kwargs['index_col'] = self.parse_df_origin(path, read_func)

                # Override header_row and index_col if not set to 'Auto'
                if parse_kwargs['header'] != 'Auto': kwargs['header'] = parse_kwargs['header']
                if parse_kwargs['index_col'] != 'Auto': kwargs['index_col'] = parse_kwargs['index_col']
                kwargs['skiprows'] = parse_kwargs['skiprows']

                try:
                    if kwargs['header'] is None: raise ValueError('Auto parser could not find a header row. Check import settings.')  # don't let the user try to read a file with no header row
                    if kwargs['index_col'] is None: raise ValueError('Auto parser could not find an index column. Check import settings.')  # don't let the user try to read a file without declaring an index column
                    data = read_func(path, **kwargs)
                    data.index.names = ['Timestamp']
                    data.index = pd.to_datetime(data.index, infer_datetime_format=True)
                    if any(ts == pd.NaT for ts in data.index): raise ValueError('Timestamps could not be parsed from given index column. Check import settings.')
                    dflist.append(data)
                except ValueError as e:
                    for file in self.path_dict:
                        if self.path_dict[file] == path: source = file
                    if 'source' not in locals(): source = path
                    DM.feedback('File "\{}\" threw an error: {}'.format(source, e))
                    return pd.DataFrame()
                TG.path_kwargs[path].update(kwargs)

            DM.feedback('Done', mode='append')
            df = pd.concat(dflist, axis=0, sort=False)
            df = df.applymap(floatify)
            return df.sort_index()

        ### Beginning of actions
        DM = self.parent
        TG = DM.parent
        group = self.groupName.text()
        loaded_groups = [self.importedGroups.item(i).text() for i in range(self.importedGroups.count())]

        # Use case filtering
        if group == '':
            DM.feedback('Group name cannot be empty.')
            return
        elif group in loaded_groups:
            if DM.popup('Group \"{}\" already exists. Overwrite?'.format(group)) == QMessageBox.Ok:
                self.importedGroups.takeItem(loaded_groups.index(group))
            else:
                return
        source_files = [self.groupFiles.item(i).text() for i in range(self.groupFiles.count())]  #read groupfiles listview
        if not source_files:
            DM.feedback('Group cannot have 0 associated files.')
            return
        source_paths = [self.path_dict[file] for file in source_files]  #path_dict is quasi global, appended gather_files (therefore, navigating to a different directory should not disconnect files from paths)
        df = combine_files(source_paths)#, header_row=0, ts_col='PacketTime', dtf='%Y-%m-%d %H:%M:%S.%f')  # These kwargs are specific to PHI_HK

        if not df.empty:
            DM.groups[group] = Group(df, source_files, source_paths)  # this is writing to Data_Manager's version, not TG's
            self.importedGroups.addItem(group)

            # Try to auto parse units
            parse_error_log = []
            if self.auto_parse:
                for header in DM.groups[group].series:
                    parsed = parse_unit(header)
                    DM.groups[group].series[header].unit = parsed
                    if parsed is None:
                        parse_error_log.append(header)  # parse_error_log formerly associated headers with their source files, but this has been removed because you can just look at the data in the DataFrames tab to figure out what the unit should be in the event of parse failure
            if parse_error_log:
                report = ''
                for header in parse_error_log:
                    report += header+'\n'
                DM.popup('Unit Parse Failure',
                         informative='Unable to parse units from the following headers. See Configure tab to manually assign units.',
                         details=report,
                         buttons=1)

            # Update other tabs but don't trigger table filling
            for combo in [DM.dataframes_tab.selectGroup, DM.configure_tab.selectGroup]:
                combo.blockSignals(True)
                combo.addItem(group)
                combo.blockSignals(False)

            self.groupFiles.clear()
            self.groupName.setText('')
            DM.modified = True


    def delete_group(self):
        DM = self.parent
        try:
            item = self.importedGroups.selectedItems()[0]
            group = item.text()
            if DM.popup('Delete group \"{}\"?'.format(group)) == QMessageBox.Ok:
                self.importedGroups.takeItem(self.importedGroups.row(item))
                del DM.groups[group]
                if group in DM.group_reassign: del DM.group_reassign[group]
                DM.dataframes_tab.selectGroup.removeItem(DM.dataframes_tab.selectGroup.findText(group))
                DM.configure_tab.selectGroup.removeItem(DM.configure_tab.selectGroup.findText(group))
        except IndexError:
            pass
        DM.modified = True  # ok if you make one and then delete it, it still thinks something's changed but WHATEVER


class Configure_Tab(QWidget):
    def __init__(self, parent):
        super().__init__()
        self.parent = parent
        self.grid = QGridLayout()


        self.selectGroup = QComboBox()
        self.selectGroup.addItems(self.parent.groups.keys())
        self.selectGroup.currentIndexChanged.connect(self.display_header_info)
        self.grid.addWidget(self.selectGroup,0,0)

        self.settings = QPushButton('Unit Settings')
        self.settings.clicked.connect(self.open_settings)
        self.grid.addWidget(self.settings,1,0)

        self.hideRows = QCheckBox('Hide Unused Headers')
        self.hideRows.setChecked(True)
        self.hideRows.stateChanged.connect(self.display_header_info)
        self.grid.addWidget(self.hideRows,2,0)

        self.start = QLabel()
        self.grid.addWidget(self.start,3,0)

        self.end = QLabel()
        self.grid.addWidget(self.end,4,0)

        self.total_span = QLabel()
        self.grid.addWidget(self.total_span,5,0)

        self.sampling_rate = QLabel()
        self.grid.addWidget(self.sampling_rate,6,0)

        self.headerTable = QTableWidget()
        self.headerTable.setColumnCount(6)
        self.headerTable.setHorizontalHeaderLabels(['Keep','Original Header','Alias','Unit Type','Unit','Scale'])
        self.headerTable.horizontalHeader().setSectionResizeMode(0,QHeaderView.ResizeToContents)
        self.headerTable.horizontalHeader().setSectionResizeMode(1,QHeaderView.Stretch)
        self.headerTable.horizontalHeader().setSectionResizeMode(2,QHeaderView.Stretch)
        self.headerTable.horizontalHeader().setSectionResizeMode(3,QHeaderView.Fixed)
        self.headerTable.horizontalHeader().setSectionResizeMode(4,QHeaderView.Fixed)
        self.headerTable.horizontalHeader().setSectionResizeMode(5,QHeaderView.ResizeToContents)
        self.headerTable.verticalHeader().setSectionResizeMode(QHeaderView.Fixed)
        self.grid.addWidget(self.headerTable,0,1,8,1)

        row_weights = [1, 1, 1, 1, 1, 1, 1, 100]
        for i,rw in enumerate(row_weights):
            self.grid.setRowStretch(i,rw)
        col_weights = [1, 100]
        for i,cw in enumerate(col_weights):
            self.grid.setColumnStretch(i,cw)
        self.setLayout(self.grid)

        if self.selectGroup.currentText():
            self.display_header_info()
            self.parent.modified = False

    def days_hours_minutes(self, timedelta):
            return timedelta.days, timedelta.seconds//3600, (timedelta.seconds//60)%60

    def df_span_info(self, df):
        start = min(df.index)
        end = max(df.index)
        totalspan = self.days_hours_minutes(end - start)
        timeinterval = 0; i = 1
        while timeinterval == 0:
            timeinterval = (df.index[i]-df.index[i-1]).total_seconds()
            i += 1
        return start, end, totalspan, timeinterval

    def display_header_info(self):
        try:
            self.headerTable.cellChanged.disconnect(self.update_alias_scale)
        except TypeError:
            pass
        TG = self.parent.parent
        DM = self.parent
        selected = self.selectGroup.currentText()
        if selected:
            group = DM.groups[selected]
            df = group.data
            start, end, total_span, sampling_rate = self.df_span_info(df)
            self.start.setText('Data Start:\n    {}'.format(start.strftime('%Y-%m-%d  %H:%M:%S')))
            self.end.setText('Data End:\n    {}'.format(end.strftime('%Y-%m-%d  %H:%M:%S')))
            self.total_span.setText('Total Span:\n    {} days\n    {} hours\n    {} minutes'.format(*total_span))
            self.sampling_rate.setText('Sampling Rate:\n    {}s'.format(sampling_rate))

            if self.hideRows.isChecked():
                nKeep = 0
                for header in group.series:
                    if group.series[header].keep: nKeep += 1
            else:
                nKeep = len(group.series)
            self.headerTable.setRowCount(nKeep)

            i = 0
            for header in group.series:
                keep = group.series[header].keep
                if self.hideRows.isChecked():
                    if not keep: continue
                alias = group.series[header].alias
                unit = group.series[header].unit
                unit_type = TG.get_unit_type(unit)

                keep_check = QCheckBox()
                keep_check.setChecked(keep)
                keep_check.setProperty("row", i)
                keep_check.stateChanged.connect(self.update_keep)
                self.headerTable.setCellWidget(i, 0, keep_check)

                self.headerTable.setItem(i, 1, QTableWidgetItem(header))
#                self.headerTable.item(i, 1).setFlags(Qt.ItemIsSelectable)

                self.headerTable.setItem(i, 2, QTableWidgetItem(alias))

                type_combo = QComboBox()
                type_combo.addItem(None)
                type_combo.addItems(list(TG.unit_dict.keys()))
                type_combo.setCurrentText(unit_type)
                type_combo.setProperty("row", i)
                type_combo.currentIndexChanged.connect(self.update_unit_combo)
                self.headerTable.setCellWidget(i, 3, type_combo)

                unit_combo = QComboBox()
                if unit_type is not None:
                    unit_combo.addItems(list(TG.unit_dict[unit_type]))
                unit_combo.setCurrentText(unit)
                unit_combo.setProperty("row", i)
                unit_combo.currentIndexChanged.connect(self.update_series_unit)
                self.headerTable.setCellWidget(i, 4, unit_combo)

                self.headerTable.setItem(i, 5, QTableWidgetItem(str(group.series[header].scale)))
                i += 1
        else:
            self.headerTable.clear()
            self.headerTable.setRowCount(0)
            self.headerTable.setColumnCount(0)
        self.headerTable.cellChanged.connect(self.update_alias_scale)

    def update_alias_scale(self, row, column):
        """Updates the alias and scaling factor of series when one of those two fields is edited"""
        DM = self.parent
        group = DM.groups[self.selectGroup.currentText()]
        header = self.headerTable.item(row, 1).text()
        if column == 2:
            alias = self.headerTable.item(row, 2).text().strip()  # remove any trailing/leading whitespace
            def remove_key_by_value(dictionary, value):
                for key in dictionary:
                    if dictionary[key] == value:
                        del dictionary[key]
                        break
            if alias:
                if alias in group.alias_dict:
                    DM.feedback('Alias \"{}\" is already in use. Please choose a different alias.'.format(alias))
                    self.headerTable.blockSignals(True)
                    self.headerTable.setItem(row, 2, QTableWidgetItem(group.series[header].alias))
                    self.headerTable.blockSignals(False)
                    return
                if alias in group.data.columns:
                    DM.feedback('Alias \"{}\" is the name of an original header. Please choose a different alias.'.format(alias))
                    self.headerTable.blockSignals(True)
                    self.headerTable.setItem(row, 2, QTableWidgetItem(group.series[header].alias))
                    self.headerTable.blockSignals(False)
                    return
                group.series[header].alias = alias
                remove_key_by_value(group.alias_dict, header)
                group.alias_dict[alias] = header
            else:
                group.series[header].alias = ''
                remove_key_by_value(group.alias_dict, header)
            DM.modified = True
        elif column == 5:
            scale = self.headerTable.item(row, 5).text()
            try:
                scale = float(scale)
                if scale == 0: raise ValueError
                group.series[header].scale = scale
                DM.modified = True
            except ValueError:
                DM.feedback('\"{}\" is not a valid scaling factor. Only nonzero real numbers permitted.'.format(scale))
            self.headerTable.blockSignals(True)  # prevents infinite recursion when setItem would call this function again
            self.headerTable.setItem(row, 5, QTableWidgetItem(str(group.series[header].scale)))
            self.headerTable.blockSignals(False)

    def update_unit_combo(self):
        TG = self.parent.parent
        type_combo = QObject.sender(self)
        row = type_combo.property("row")
        unit_combo = self.headerTable.cellWidget(row, 4)
        unit_type = type_combo.currentText()
        unit_combo.clear()
        try:
            unit_combo.addItems(list(TG.unit_dict[unit_type]))
        except KeyError:
            pass

    def update_series_unit(self):
        DM = self.parent
        group = DM.groups[self.selectGroup.currentText()]
        unit_combo = QObject.sender(self)
        row = unit_combo.property("row")
        unit = unit_combo.currentText()
        header = self.headerTable.item(row, 1).text()
        group.series[header].unit = unit
        DM.modified = True

    def update_keep(self):
        DM = self.parent
        group = DM.groups[self.selectGroup.currentText()]
        keep_check = QObject.sender(self)
        row = keep_check.property("row")
        header = self.headerTable.item(row, 1).text()
        group.series[header].keep = keep_check.isChecked()
        self.display_header_info()
        DM.modified = True

    def open_settings(self):
        self.settings_dialog = Unit_Settings(self)
        self.settings_dialog.setModal(True)
        self.settings_dialog.show()


class DataFrames_Tab(QWidget):
    def __init__(self, parent):
        super().__init__()
        self.parent = parent
        self.grid = QGridLayout()

        self.selectGroup = QComboBox()
        self.selectGroup.addItems(self.parent.groups.keys())
        self.selectGroup.currentIndexChanged.connect(self.display_dataframe)
        self.export = QPushButton('Export DataFrames')
        self.export.clicked.connect(self.export_data)
        self.dfTable = QTableView()
        self.dfTable.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.dfTable.verticalHeader().setDefaultSectionSize(self.dfTable.verticalHeader().minimumSectionSize())
        self.dfTable.verticalHeader().setSectionResizeMode(QHeaderView.Fixed)

        widgets = [
                self.selectGroup,
                self.export,
                self.dfTable,
                ]

        positions = [
                (0,0,1,1),
                (1,0,1,1),
                (0,1,3,1),
                ]

        for w, p in zip(widgets, positions):
            self.grid.addWidget(w, *p)
        self.setLayout(self.grid)

        if self.selectGroup.currentText():
            self.display_dataframe()

    def display_dataframe(self):
        DM = self.parent
        TG = DM.parent
        selected = self.selectGroup.currentText()
        if selected:
            group = DM.groups[selected]
            df = group.data

            # Prepare table to display only headers kept in Configure tab (first 20 lines)
            shown = 20
            kept_df = df.head(shown).loc[:,[header for header in group.series if group.series[header].keep]]
            kept_df.index = kept_df.index.astype('str')
            if len(df.index) > shown:
                ellipses = pd.DataFrame(['...']*len(kept_df.columns),
                                        index=kept_df.columns,
                                        columns=['...']).T
                kept_df = kept_df.append(ellipses)

            # Use Aliases, Type, Unit, as column headers
            kept_df_headers = []
            for header in kept_df.columns:
                alias = group.series[header].alias
                unit = group.series[header].unit
                unit_type = TG.get_unit_type(unit)
                if not alias: alias = header
                if unit:
                    kept_df_headers.append('{}\n{} [{}]'.format(alias, unit_type, unit))
                else:
                    kept_df_headers.append('{}\n(no units)'.format(alias))
            kept_df.columns = kept_df_headers

            # Display kept_df in table
            self.model = PandasModel(kept_df)
            self.proxy = QSortFilterProxyModel()
            self.proxy.setSourceModel(self.model)
            self.dfTable.setModel(self.proxy)
            for i in range(self.model.columnCount()):
                self.dfTable.horizontalHeader().setSectionResizeMode(i, QHeaderView.ResizeToContents)

        else:
            if hasattr(self, 'proxy'): self.proxy.deleteLater()

    def export_data(self):
        """Generate an Excel sheet with kept dataframes, one per sheet/tab"""
        pass

class Import_Settings(QDialog):
    def __init__(self, parent):
        super().__init__()
        self.parent = parent
        TG = self.parent.parent.parent
        self.resize(750,532)
        self.setWindowTitle('File-Specific Import Settings')

        grid = QGridLayout()
        self.kwargTable = QTableWidget()
        self.kwargTable.verticalHeader().setDefaultSectionSize(self.kwargTable.verticalHeader().minimumSectionSize())
        self.kwargTable.verticalHeader().setSectionResizeMode(QHeaderView.Fixed)
        self.previewTable = QTableView()
        self.previewTable.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.previewTable.verticalHeader().setDefaultSectionSize(self.previewTable.verticalHeader().minimumSectionSize())
        self.previewTable.verticalHeader().setSectionResizeMode(QHeaderView.Fixed)
        grid.addWidget(self.kwargTable, 0, 0)
        grid.addWidget(self.previewTable, 1, 0)
        self.setLayout(grid)

        self.kwargTable.setColumnCount(4)
        files = [self.parent.foundFiles.item(i).text() for i in range(self.parent.foundFiles.count())]
        self.kwargTable.setRowCount(len(files))
        self.kwargTable.setHorizontalHeaderLabels(['File', 'Header Row', 'Index Column', 'Skip Rows'])
        for i, file in enumerate(files):
            kwargs = TG.path_kwargs[self.parent.path_dict[file]]
            self.kwargTable.setItem(i, 0, QTableWidgetItem(file))
            self.kwargTable.item(i,0).setFlags(Qt.ItemIsSelectable)
            self.kwargTable.setItem(i, 1, QTableWidgetItem(str(kwargs['header'])))
            self.kwargTable.setItem(i, 2, QTableWidgetItem(str(kwargs['index_col'])))
            self.kwargTable.setItem(i, 3, QTableWidgetItem(str(kwargs['skiprows'])))
        self.kwargTable.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        self.kwargTable.horizontalHeader().setSectionResizeMode(1, QHeaderView.Fixed)
        self.kwargTable.horizontalHeader().setSectionResizeMode(2, QHeaderView.Fixed)
        self.kwargTable.horizontalHeader().setSectionResizeMode(3, QHeaderView.Fixed)
        self.kwargTable.cellChanged.connect(self.update_parse_kwargs)
        self.kwargTable.itemSelectionChanged.connect(self.preview_df)

    def update_parse_kwargs(self, row, column):
        DM = self.parent.parent
        TG = DM.parent
        pick_kwargs = {1:'header', 2:'index_col', 3:'skiprows'}
        kwarg = pick_kwargs[column]
        file = self.kwargTable.item(row, 0).text()
        path = self.parent.path_dict[file]
        text = self.kwargTable.item(row, column).text()

        ### input permissions
        if kwarg == 'skiprows':
            value = []
            for i in text:
                if text == 'None':
                    value = text
                else:
                    if i.isdigit() and i not in value:  # admit only unique digits
                        if int(i) != 0: value.append(int(i))  # silently disallow zero
                    elif i in ', []':  # ignore commas, spaces, and brackets
                        continue
                    else:
                        DM.feedback('Only list of unique nonzero integers or \"None\" allowed.')
                        self.kwargTable.blockSignals(True)
                        self.kwargTable.setItem(row, column, QTableWidgetItem(str(TG.path_kwargs[path][kwarg])))
                        self.kwargTable.blockSignals(False)
                        return
            self.kwargTable.blockSignals(True)
            self.kwargTable.setItem(row, column, QTableWidgetItem(str(value)))
            self.kwargTable.blockSignals(False)
        else:
            if text.isdigit():
                value = int(text)
            elif text.lower() == 'auto':
                value = 'Auto'
            else:
                DM.feedback('Only integers or \"Auto\" allowed.')
                self.kwargTable.blockSignals(True)
                self.kwargTable.setItem(row, column, QTableWidgetItem(str(TG.path_kwargs[path][kwarg])))
                self.kwargTable.blockSignals(False)
                return
        self.kwargTable.blockSignals(True)
        self.kwargTable.setItem(row, column, QTableWidgetItem(str(value)))
        self.kwargTable.blockSignals(False)
        TG.path_kwargs[path][kwarg] = value
        self.preview_df()


    def preview_df(self):
        TG = self.parent.parent.parent
        selection = self.kwargTable.selectedIndexes()
        if selection:
            rows = sorted(index.row() for index in selection)
            if all(x==rows[0] for x in rows):  # can only preview one row at a time.

                # Populate preview table with selected 10x10 df preview
                row = selection[0].row()
                file = self.kwargTable.item(row, 0).text()
                if file.endswith('xls') or file.endswith('xlsx'):
                    read_func = pd.read_excel
                elif file.endswith('csv') or file.endswith('zip'):
                    read_func = pd.read_csv
                path = self.parent.path_dict[file]
                df, r, c = self.parent.parse_df_origin(path, read_func)
                df.columns = [str(i) for i in range(len(df.columns))]
                self.model = PandasModel(df)
                self.proxy = QSortFilterProxyModel()
                self.proxy.setSourceModel(self.model)
                self.previewTable.setModel(self.proxy)

                # Highlight selected rows/columns according to parse_kwargs
                header = TG.path_kwargs[path]['header']
                index_col = TG.path_kwargs[path]['index_col']
                skiprows = TG.path_kwargs[path]['skiprows']

                if index_col == 'Auto': index_col = c
                if header == 'Auto': header = r

                if index_col is not None:
                    for r in range(len(df.index)):
                        self.model.setData(self.model.index(r,int(index_col)), QBrush(QColor.fromRgb(255, 170, 0)), Qt.BackgroundRole)
                if header is not None:
                    for c in range(len(df.columns)):
                        self.model.setData(self.model.index(int(header),c), QBrush(QColor.fromRgb(0, 170, 255)), Qt.BackgroundRole)
                if skiprows is not None:
                    for r in skiprows:
                        for c in range(len(df.columns)):
                            self.model.setData(self.model.index(r,c), QBrush(Qt.darkGray), Qt.BackgroundRole)
            else:
                if hasattr(self, 'proxy'): self.proxy.deleteLater()
        else:
            if hasattr(self, 'proxy'): self.proxy.deleteLater()

    def keyPressEvent(self, event):
        """Enables single row copy to multirow paste, as long as column dimensions are the same, using Ctrl+C/V."""
        if event.matches(QKeySequence.Copy):
            selection = self.kwargTable.selectedIndexes()
            if selection:
                rows = sorted(index.row() for index in selection)
                if all(x==rows[0] for x in rows):  # can only copy one row at a time.
                    columns = sorted(index.column() for index in selection)
                    selection_col_span = columns[-1] - columns[0] + 1
                    table = [[''] * selection_col_span]
                    for index in selection:
                        column = index.column() - columns[0]
                        table[0][column] = index.data()
                    stream = io.StringIO()
                    csv.writer(stream).writerows(table)
                    QApplication.clipboard().setText(stream.getvalue())

        if event.matches(QKeySequence.Paste):
            selection = self.kwargTable.selectedIndexes()
            if selection:
                model = self.kwargTable.model()
                buffer = QApplication.clipboard().text()
                rows = sorted(index.row() for index in selection)
                columns = sorted(index.column() for index in selection)
                selection_col_span = columns[-1] - columns[0] + 1
                reader = csv.reader(io.StringIO(buffer), delimiter='\t')
                arr = [row[0].split(',') for row in reader]
                arr = arr[0]
                if selection_col_span == len(arr):
                    for index in selection:
                        column = index.column() - columns[0]
                        model.setData(model.index(index.row(), index.column()), arr[column])

class PandasModel(QStandardItemModel):
    def __init__(self, data, parent=None):
        QStandardItemModel.__init__(self, parent)
        self._data = data
        for row in data.values.tolist():
            data_row = [QStandardItem(str(x)) for x in row]
            self.appendRow(data_row)
        return

    def rowCount(self, parent=None):
        return len(self._data.values)

    def columnCount(self, parent=None):
        return self._data.columns.size

    def headerData(self, x, orientation, role):
        if orientation == Qt.Horizontal and role == Qt.DisplayRole:
            return self._data.columns[x]
        if orientation == Qt.Vertical and role == Qt.DisplayRole:
            return self._data.index[x]
        return None

class Unit_Settings(QDialog):
    def __init__(self, parent):
        super().__init__()
        self.parent = parent
        TG = self.parent.parent.parent  # sheesh man

        self.set_defaults = {}
#        self.unit_types = [
#                'Position',
#                'Velocity',
#                'Acceleration',
#                'Angle',
#                'Temperature',
#                'Pressure',
#                'Heat',
#                'Voltage',
#                'Current',
#                'Resistance',
#                'Force',
#                'Torque',
#                'Power',
#                ]
        self.grid = QGridLayout()

        units = [u for u in TG.unit_dict.keys() if u is not None]
        for i,u in enumerate(units):
            self.set_defaults[i] = QComboBox()
            self.set_defaults[i].addItems(TG.unit_dict[u])
#            self.set_defaults[i].setCurrentText(TG.unit_defaults[u])
            self.grid.addWidget(QLabel(u), i, 0)
            self.grid.addWidget(self.set_defaults[i], i, 1)

        self.setLayout(self.grid)

class Subplot_Manager():
    """Wrapper around subplot object (host). Keeps track of contents and settings of each subplot."""
    def __init__(self, parent, host, contents={}, order=[None], index=None, legend=False, colorCoord=False):
        self.parent = parent
        self.axes = [host]  # keeps track of parasitic axes
        self.contents = contents # standard contents format: {group: {headers:units}} in the context of display
        self.order = order  # keeps track of preferred unit order
        self.index = index  # convenience attribute
        self.legend = legend  # legend toggle
        self.colorCoord = colorCoord  # color coordination toggle

    def host(self):
        return self.axes[0]

    def make_patch_spines_invisible(self, ax):
        """see https://matplotlib.org/gallery/ticks_and_spines/multiple_yaxis_with_spines.html"""
        ax.set_frame_on(True)
        ax.patch.set_visible(False)
        for sp in ax.spines.values():
            sp.set_visible(False)

    def plot(self, verbose=True):
        """Main plotting function. Auto-generates parasitic axes in specified unit order."""
        sp = self
        TG = self.parent
        CF = TG.control_frame
        FS = TG.figure_settings
        for ax in sp.axes[1:]: ax.remove()  # remove parasitic axes from subplot
        sp.axes = [sp.host()]  # clear parasitic axes from sp.axes
        sp.host().clear()  # clear host axis of data

        color_index = 0
        style_dict = {}
        lines = []
        labels = []
        if sp.contents is not None:
            for group, aliases_units in sp.contents.items():
                df = TG.groups[group].data
                subdf = df[(df.index >= CF.start) & (df.index <= CF.end)]  # filter by start/end time
                for alias, unit in aliases_units.items():

                    # Determine which axes to plot on, depending on sp.order
                    if sp.order[0] is None:
                        sp.order[0] = unit  # if no order given, default to sorted order
                    if unit not in sp.order:
                        sp.order.append(unit)  # new units go at the end of the order
                    ax_index = sp.order.index(unit)  # get index of unit in unit order
                    while len(sp.axes)-1 < ax_index: # extend sp.axes as needed
                        par = sp.host().twinx()
                        sp.axes.append(par)
                    ax = sp.axes[ax_index]  # get axis (parasitic or host) at index of unit

                    # Manage colors and styles
                    unit_type = TG.get_unit_type(unit)
                    if sp.colorCoord:
                        if unit_type not in style_dict:  # keep track of how many series are plotted in each unit to cycle through linestyles(/markerstyles TBI)
                            style_dict[unit_type] = 0
                        style_counter = style_dict[unit_type]
                        style_dict[unit_type] = style_counter+1
                        style = TG.markers[style_counter%len(TG.markers)]
                        color = TG.color_dict[unit_type]
                        ax.yaxis.label.set_color(color)
                    else:  # set color to rotate through default colormap (otherwise colormap is done per axis, not the whole subplot)
                        color='C'+str(color_index%10)
                        color_index += 1
                        style = 'o'
                        ax.yaxis.label.set_color('k')

                    # Fetch data to plot from references in sp.contents
                    try:
                        header = TG.groups[group].alias_dict[alias]
                    except KeyError:
                        header = alias
                    scale = TG.groups[group].series[header].scale
                    data = [x*scale for x in subdf[header]]
                    timestamp = subdf.index
                    line, = ax.plot(timestamp, data,
                                    style, color=color, markersize=CF.dotsize, markeredgewidth=CF.dotsize, linestyle='None')
                    lines.append(line)
                    labels.append(alias)
                    if unit_type is not None:  # if no units, leave axis unlabeled
                        ax.set_ylabel('{} [{}]'.format(unit_type, unit), fontsize=FS.labelSize.value())  # set ylabel to formal unit description

            offset = FS.parOffset.value()
            for i,par in enumerate(sp.axes[1:]):  # offset parasitic axes
                self.make_patch_spines_invisible(par)
                par.spines["right"].set_visible(True)
                par.spines["right"].set_position(("axes", 1+offset*(i)))

            npars = len(sp.axes[1:])
            if sp.legend and sp.contents:  # create and offset legend
                sp.host().legend(lines, labels,
                       bbox_to_anchor=(1+offset*npars, .5),
                       loc="center left", markerscale=10)

class Group():
    def __init__(self, df, source_files, source_paths):
        self.data = df  # maybe copy needed
        self.series = {key:Series() for key in self.data.columns}  # import as 1 to 1 header:alias
        self.alias_dict = {}
        self.source_files = source_files
        self.source_paths = source_paths
#EG: TG.groups[name].series['mySeries'].alias
    def summarize(self):
        print('Source Paths')
        for path in self.source_paths:
            print('\t'+path)
        print('\nHeaders')
        for header in self.series:
            print('\t{}\n\t\t{}'.format(header,self.series[header].summarize()))
        print('\nAssigned Aliases')
        print('\t{}'.format(self.alias_dict))


class Series():
    def __init__(self, alias='', unit=None, scale=1.0, keep=True):
        self.alias = alias
        self.unit = unit
        self.scale = scale
        self.keep = keep

    def summarize(self):
        return 'Alias: '+str(self.alias)+'  Unit: '+str(self.unit)+'  Scale: '+str(self.scale)+'  Keep: '+str(self.keep)





### THE ACTUAL RUN COMMAND
if 'app' not in locals():
    app = QCoreApplication.instance()
if app is None:  # otherwise kernel dies
    app = QApplication(sys.argv)
X = Telemetry_Grapher()#groups=groups)
app.exec_()