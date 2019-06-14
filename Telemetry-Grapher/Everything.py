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
import matplotlib.dates as mdates
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec
from matplotlib import colors as mcolors
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas

### THE RUN COMMAND IS AT THE BOTTOM. YOU CAN JUST HIT RUN ON THIS SCRIPT.

# Allows logging of unhandled exceptions
logger = logging.getLogger(__name__)
logging.basicConfig(filename='errors.log', filemode='w', level=logging.DEBUG)

def handle_unhandled_exception(exc_type, exc_value, exc_traceback):
    """Handler for unhandled exceptions that will write to the logs"""
    if issubclass(exc_type, KeyboardInterrupt):
        # call the default excepthook saved at __excepthook__
        sys.__excepthook__(exc_type, exc_value, exc_traceback)
        return
    logger.critical("Unhandled exception", exc_info=(exc_type, exc_value, exc_traceback))

sys.excepthook = handle_unhandled_exception

class Application_Base(QMainWindow):
    """Main application window."""

    def __init__(self, groups={}):
        super().__init__()
        self.groups = copy.deepcopy(groups)
        self.save_dir = os.getcwd()
        self.default_ext = '.jpg'
        self.path_kwargs = {}
        self.auto_parse = True
        self.saved = True

        f = QFile('rc/dark.qss')
        if not f.exists():
            logger().error('Unable to load dark stylesheet, file not found')
            self.dark_qss = ''
        else:
            f.open(QFile.ReadOnly | QFile.Text)
            ts = QTextStream(f)
            self.dark_qss = ts.readAll()
        f = QFile('rc/light.qss')
        if not f.exists():
            logger().error('Unable to load light stylesheet, file not found')
            self.light_qss = ''
        else:
            f.open(QFile.ReadOnly | QFile.Text)
            ts = QTextStream(f)
            self.light_qss = ts.readAll()

        # Read settings from config file
        with open('config.json', 'r', encoding='utf-8') as f:
            startup = json.load(f)
        self.unit_dict = startup['unit_dict']
        self.unit_clarify = startup['unit_clarify']
        self.user_units = startup['user_units']
        self.default_type = startup['default_type']
        self.default_unit = startup['default_unit']
        self.light_rcs = startup['light_rcs']
        self.dark_rcs = startup['dark_rcs']

        self.default_qss = self.light_qss
        self.default_rcs = self.light_rcs
        self.current_rcs = self.default_rcs

        self.setWindowTitle('Telemetry Plot Configurator')
        self.setWindowIcon(QIcon('rc/satellite.png'))
#        self.setWindowIcon(QIcon('rc/toolbar_separator_vertical.png'))
        self.statusBar().showMessage('No subplot selected')
        self.manager = QWidget()

        self.docked_FS = QDockWidget("Figure Settings", self)
        self.docked_FS.setAllowedAreas(Qt.RightDockWidgetArea | Qt.LeftDockWidgetArea)
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
        self.addDockWidget(Qt.RightDockWidgetArea, self.docked_FS)
        self.docked_FS.hide()
        self.figure_settings.connect_widgets(container=self.axes_frame)
#        self.control_frame.time_filter()
        self.filename = self.axes_frame.fig._suptitle.get_text()
        self.resizeDocks([self.docked_SF], [420], Qt.Horizontal)

        fileMenu = self.menuBar().addMenu('File')
        newAction = QAction('New', self)
        newAction.setShortcut('Ctrl+N')
        newAction.setStatusTip('Open a blank figure')
        newAction.triggered.connect(self.new)
        fileMenu.addAction(newAction)

        openAction = QAction('Open', self)
        openAction.setShortcut('Ctrl+O')
        openAction.setStatusTip('Open existing figure')
        openAction.triggered.connect(self.open_fig)
        fileMenu.addAction(openAction)

        saveAction = QAction('Save', self)
        saveAction.setShortcut('Ctrl+S')
        saveAction.triggered.connect(self.save)
        fileMenu.addAction(saveAction)

        saveAction = QAction('Save As', self)
        saveAction.setShortcut('Ctrl+Shift+S')
        saveAction.triggered.connect(self.save_as)
        fileMenu.addAction(saveAction)

        exitAction = QAction('Exit', self)
        exitAction.setShortcut('Ctrl+Q')
        exitAction.setStatusTip('Exit application')
        exitAction.triggered.connect(self.close)
        fileMenu.addAction(exitAction)

        editMenu = self.menuBar().addMenu('Edit')
        undoAction = QAction('Undo', self)
        undoAction.setShortcut('Ctrl+Z')
        undoAction.triggered.connect(self.undo)
        editMenu.addAction(undoAction)

        redoAction = QAction('Redo', self)
        redoAction.setShortcut('Ctrl+Y')
        redoAction.triggered.connect(self.redo)
        editMenu.addAction(redoAction)

        refreshAction = QAction('Refresh Figure', self)
        refreshAction.setShortcut('Ctrl+R')
        refreshAction.triggered.connect(self.axes_frame.refresh_all)
        editMenu.addAction(refreshAction)

#        resetAction = QAction('Undo', self)
#        resetAction.setShortcut('Ctrl+Z')  # wrong
#        resetAction.setStatusTip('Undo last action')  #wrong
#        resetAction.triggered.connect(self.undo)  #wrong
#        editMenu.addAction(resetAction)

        toolsMenu = self.menuBar().addMenu('Tools')
        dataAction = QAction('Manage Data', self)
        dataAction.setShortcut('Ctrl+D')
        dataAction.triggered.connect(self.open_data_manager)
        toolsMenu.addAction(dataAction)

        templateAction = QAction('Import Template', self)
        templateAction.setShortcut('Ctrl+T')
        templateAction.triggered.connect(self.import_template)
        toolsMenu.addAction(templateAction)

        viewMenu = self.menuBar().addMenu('View')
        docksAction = QAction('Show/Hide Docks', self)
        docksAction.setShortcut('Ctrl+H')
        docksAction.triggered.connect(self.toggle_docks)
        viewMenu.addAction(docksAction)

        interactiveAction = QAction('MPL Interactive Mode', self)
        interactiveAction.setShortcut('Ctrl+M')
        interactiveAction.setStatusTip('Toggle Matplotlib\'s interactive mode')
        interactiveAction.triggered.connect(self.toggle_interactive)
        viewMenu.addAction(interactiveAction)

        darkAction = QAction('Dark Mode', self)
        darkAction.setShortcut('Ctrl+B')
        darkAction.setStatusTip('Toggle dark user interface')
        darkAction.triggered.connect(self.toggle_dark_mode)
        viewMenu.addAction(darkAction)

        self.showMaximized()
        ### Adding Figure Settings dock to right side currently screws this up
        self.control_frame.setFixedHeight(self.control_frame.height()) #(98 on my screen)
        self.control_frame.setFixedWidth(self.control_frame.width()) #(450 on my screen)
        self.figure_settings.setFixedWidth(150)
        self.set_app_style(self.default_qss, self.default_rcs)
        self.axes_frame.refresh_all()


        ### Delete later, just for speed
        self.open_data_manager()

    def popup(self, text, title=' ', informative=None, details=None, mode='save', icon=True):
        """Brings up a message box with provided text and returns Ok or Cancel."""
        self.prompt = QMessageBox()
        self.prompt.setWindowIcon(QIcon('rc/satellite.png'))
        self.prompt.setWindowTitle(title)
        if icon: self.prompt.setIcon(QMessageBox.Question)
        self.prompt.setText(text)
        if mode == 'save':
            self.prompt.setStandardButtons(QMessageBox.Discard | QMessageBox.Cancel | QMessageBox.Save)
            self.prompt.button(QMessageBox.Save).setText('Save && Exit')
        elif mode == 'confirm':
            self.prompt.setStandardButtons(QMessageBox.Ok | QMessageBox.Cancel)
        elif mode == 'alert':
            self.prompt.setStandardButtons(QMessageBox.Ok)
        self.prompt.setInformativeText(informative)
        self.prompt.setDetailedText(details)
        self.prompt.show()
        return self.prompt.exec_()

    def groups_to_contents(self, groups):
        """Converts groups database into contents format. See ReadMe."""
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

    def save(self):
        """Quick-save feature.
        Saves current figure to most recent save directory if a file by that name already exists, else defers to explicit Save-As dialog.
        Accessible by Application Base's File menu (or Ctrl+S)."""
        CF = self.control_frame
        AF = self.axes_frame
        FS = self.figure_settings
        CF.rename()
        AF.current_sps = []
        FS.density.setValue(100)
        AF.refresh_all()

        filename = self.filename + self.default_ext
        if filename in os.listdir(self.save_dir):
            plt.savefig(self.save_dir + '\\' + filename, dpi=300, transparent=True, bbox_inches='tight')
#            with open(self.filename + '.pickle', 'wb') as f:
#                pl.dump(AF.fig, f)
            self.statusBar().showMessage('Saved to {}'.format(self.save_dir))
            self.saved = True
        else:
            self.save_as()

    def save_as(self):
        """Explicit Save-As feature.
        Saves current figure using PyQt5's file dialog. Default format is .jpg.
        Accessible by Application Base's File menu (or Ctrl+Shift+S)."""
        CF = self.control_frame
        AF = self.axes_frame
        FS = self.figure_settings
        CF.rename()
        AF.current_sps = []
        FS.density.setValue(100)
        AF.refresh_all()

        dlg = QFileDialog()
        dlg.setFileMode(QFileDialog.AnyFile)
        dlg.setViewMode(QFileDialog.Detail)
        dlg_output = dlg.getSaveFileName(self,
                                         'Save Figure',
                                         self.save_dir + '/' + self.filename,
                                         "JPEG Image (*.jpg);;PNG Image (*.png)")
        if dlg_output[0]:
            savepath = dlg_output[0]
            self.save_dir = savepath[:savepath.rindex('/')]  # store saving directory
            self.default_ext = savepath[savepath.index('.'):]  # store file extension
            plt.savefig(savepath, dpi=300, transparent=True, bbox_inches='tight')
#            with open(self.filename + '.pickle', 'wb') as f:
#                pkl.dump(AF.fig, f)
            self.statusBar().showMessage('Saved to {}'.format(savepath))
            self.saved = True

    def parse_unit(self, header):
        """Returns last instance in header of one or more characters between square brackets."""
        regex = re.compile('\[.+?\]')  # matches any characters between square brackets (but not empty [])
        parsed = None
        for match in re.finditer(regex, header):  # parsed ends up as last match
            parsed = match.group(0)[1:-1]  # unit without the brackets
        return parsed

    def interpret_unit(self, unit):
        """Tries to interpret unit.
        - Find last instance of one or more characters between square brackets -> unit.
        - Run unit through AB.unit_clarify dictionary.
        - Check if unit can be associated with a unit type (see AB.get_unit_type).
        - If so, return unit, otherwise return default unit."""
        if unit:
            if unit in self.unit_clarify:
                unit = self.unit_clarify[unit]
            if self.get_unit_type(unit) != self.default_type:
                return unit
        return self.default_unit

    def get_unit_type(self, unit):
        """Returns unit type of given unit.
        Priority is first given to user-defined units, then base unit types.
        If unit is not recognized in either dictionary, the default unit type is returned."""
        # check user units first
        for e in self.user_units:
            if unit in self.user_units[e]:
                return e
        # if not found, check hard-coded unit_dict
        for e in self.unit_dict:
            if unit in self.unit_dict[e]:
                return e
        # else, return default type
        return self.default_type

    def closeEvent(self, event):
        """Hides any floating QDockWidgets and closes all created figures upon application exit."""

        self.saved = True #??? DELETE THIS OVERRIDE LATER
        if not self.saved:
            result = self.popup('Figure has not been saved. Exit anyway?', title='Exiting Application')
            if result == QMessageBox.Cancel:
                event.ignore()
                return
            elif result == QMessageBox.Save:
                self.save()
        for dock in [self.docked_CF, self.docked_SF, self.docked_FS]:
            if dock.isFloating(): dock.close()
        plt.close('all')
        self.control_frame.titleEdit.editingFinished.disconnect()
        event.accept()

    def new(self):
        logger.error('too many chairs in here.')
        print(self.figure_settings.size())
        pass

    def set_app_style(self, qss, mpl_rcs):
        app = QApplication.instance()
        if app is None:
            raise RuntimeError("No Qt Application found.")
        app.setStyleSheet(qss)
        for k,v in mpl_rcs.items(): plt.rcParams[k] = v
        self.axes_frame.fig.set_facecolor(mpl_rcs['figure.facecolor'])

    def open_fig(self):
        raise Exception
        pass
#        print(self.figure_settings.unit_table.size())
#        print(self.figure_settings.majorXgrid.isChecked())
#        pass
#        AF = self.axes_frame
#        dlg_output = QFileDialog.getOpenFileName(self,
#                                                  "Open Saved Figure",
#                                                  self.save_dir,
#                                                  "(*.pickle)")
#        if dlg_output[0]:
#            fig = pkl.load(open(dlg_output[0], 'rb'))
#            _ = plt.figure()
#            manager = _.canvas.manager
#            manager.canvas.figure = fig
#            AF.fig.set_canvas(manager.canvas)
#            print(fig)
#            for ax in fig.axes:
#                print(ax)
#                print(ax.lines)
#                print(ax.get_legend())
#                h, l = ax.get_legend_handles_labels()
#                print(h)
#                print(l)
#            AF.fig.show()
#            AF.draw()

    def undo(self):
        pass

    def redo(self):
        pass

    def open_data_manager(self):
        """Opens Data Manager dialog.
        Accessible through Application Base's Tools menu (or Ctrl+D)."""
        self.statusBar().showMessage('Opening Data Manager')
        self.manager = Data_Manager(self)
        self.manager.setModal(True)
        self.manager.show()

    def import_template(self):
        pass

    def toggle_docks(self):
        """Toggles visibility of dock widgets.
        Accessible through Application Base's View menu (or Ctrl+H)."""
        docks = [self.docked_CF, self.docked_SF, self.docked_FS]
        if any([not dock.isVisible() for dock in docks]):
            for dock in docks: dock.show()
        else:
            for dock in docks: dock.hide()

    def toggle_interactive(self):
        pass

    def toggle_dark_mode(self):
        if self.current_rcs == self.light_rcs:
            qss = self.dark_qss
            self.current_rcs = self.dark_rcs
        else:
            qss = self.light_qss
            self.current_rcs = self.light_rcs
        self.set_app_style(qss, self.current_rcs)
        default_color = self.current_rcs['axes.labelcolor']
        self.figure_settings.color_dict[None] = default_color
        self.figure_settings.color_dict[''] = default_color
        self.axes_frame.refresh_all()
# Legacy
#    def center(self):
#        qr = self.frameGeometry()
#        cp = QDesktopWidget().availableGeometry().center()
#        qr.moveCenter(cp)
#        self.move(qr.topLeft())


class Axes_Frame(FigureCanvas):
    """Central widget in Application Base main window."""

    def __init__(self, parent):
        self.parent = parent
        AB = self.parent
        CF = AB.control_frame
        FS = AB.figure_settings
        self.fig = plt.figure(constrained_layout=False)  # not working with gridspec in controls frame. Look into later.
        super().__init__(self.fig)
        self.weights = [1]
        left = FS.leftPad.value()
        right = 1 - FS.rightPad.value()
        bottom = FS.lowerPad.value()
        top = 1 - FS.upperPad.value()
        gs = gridspec.GridSpec(1, 1, left=left, right=right, bottom=bottom, top=top)
        ax0 = self.fig.add_subplot(gs[0])
        ax0.tick_params(axis='x', labelbottom=False, bottom=False)
        self.subplots = [Subplot_Manager(parent, ax0, index=0, contents={})]
        self.current_sps = []
        self.available_data = AB.groups_to_contents(AB.groups)  # holds all unplotted data (unique to each Axes Frame object, see plans for excel tab implementation)
        self.fig.canvas.mpl_connect('button_press_event', self.select_subplot)
        self.fig.suptitle(CF.titleEdit.text(), fontsize=FS.titleSize.value())
        self.draw()

    def refresh_all(self):
        """Refreshes entire figure.
        Called when:
            - Any value in Figure Settings is updated
            - Subplots are modified in any way
            - User manually calls it via Application Base's Edit menu (Ctrl+R)"""
#        print(inspect.stack())
        AB = self.parent
        FS = AB.figure_settings
        CF = AB.control_frame
        reselect = [sp.index for sp in self.current_sps]
        for ax in self.fig.axes: ax.remove()

        n = max([len(sp.axes[2:]) for sp in self.subplots])
        # If any subplot has a legend, treat it like another secondary axis
        for sp in self.subplots:
            if sp.legend and sp.contents:
                n += 1
                break

        left = FS.leftPad.value()
        right = 1 - FS.rightPad.value() - FS.parOffset.value()*n
        bottom = FS.lowerPad.value()
        top = 1 - FS.upperPad.value()
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
        g = functools.reduce(math.gcd, self.weights)
        self.weights = [w//g for w in self.weights]  # simplify weights by their greatest common denominator (eg [2,2,4] -> [1,1,2])
        CF.weightsEdit.setText(str(self.weights))

        try:
            self.select_subplot(None, force_select=[self.subplots[i] for i in reselect])
        except IndexError:  # happens when you try to delete all the plots, some issue with instance attribute current_sps not updating when you set it to []
            pass
            # select_subplot calls self.draw(), don't need to do it again
        AB.saved = False

    def select_subplot(self, event, force_select=None):
        """Highlights clicked-on subplot and displays subplot contents in plotted tree.
        Shift and Ctrl clicking supported.
        Click within figure but outside subplots to deselect axis and clear plotted tree.
        Provide force_select=X to programmatically select subplots in list X (wrapped by Subplot_Manager object)."""
        AB = self.parent
        CF = AB.control_frame
        SF = AB.series_frame
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
                #find out which Subplot_Manager contains event-selected axes
                for sm in self.subplots:
                    if event.inaxes in sm.axes:
                        sp = sm
                        break
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
            AB.statusBar().showMessage('Selected subplot: {}'.format(sp.index))
        else:
            SF.plotted.clear()
            if self.current_sps:
                CF.legendToggle.setChecked(any([sp.legend for sp in self.current_sps]))
                CF.colorCoord.setChecked(any([sp.colorCoord for sp in self.current_sps]))
                AB.statusBar().showMessage('Selected subplots: {}'.format(sorted([sp.index for sp in self.current_sps])))
            else:
                CF.legendToggle.setChecked(False)
                CF.colorCoord.setChecked(False)
                AB.statusBar().showMessage('No subplot selected')
        self.draw()


class Control_Frame(QWidget):
    """Contains all buttons for controlling subplot organization."""

    def __init__(self, parent):
        super().__init__()
        self.parent = parent
        grid = QGridLayout()
        self.title_edited = False
        self.weights_edited = False

        title = QLabel('Title:')
        grid.addWidget(title,0,0)

        self.titleEdit = QLineEdit('New_Figure')
        self.titleEdit.editingFinished.connect(self.rename)
        self.titleEdit.textEdited.connect(self.tte)
        grid.addWidget(self.titleEdit,0,1,1,5)

        weighting = QLabel('Weights:')
        grid.addWidget(weighting,1,0,2,1)

        self.weightsEdit = QLineEdit('[1]')
        self.weightsEdit.editingFinished.connect(self.adjust_weights)
        self.titleEdit.textEdited.connect(self.wte)
        grid.addWidget(self.weightsEdit,1,1,2,2)

        selectStart = QLabel('Start:')
        grid.addWidget(selectStart,3,0,2,1)

        self.selectStart = QDateTimeEdit()
        self.selectStart.setDisplayFormat('yyyy-MM-dd hh:mm:ss')
        self.selectStart.dateTimeChanged.connect(self.time_filter)
        grid.addWidget(self.selectStart,3,1,2,1)

        self.minTS = QPushButton('Min')
        self.minTS.setFixedWidth(30)
        self.minTS.clicked.connect(self.set_start_min)
        grid.addWidget(self.minTS,3,2,2,1)

        selectEnd = QLabel('End:')
        grid.addWidget(selectEnd,5,0,2,1)

        self.selectEnd = QDateTimeEdit(QDate.currentDate())
        self.selectEnd.setDisplayFormat('yyyy-MM-dd hh:mm:ss')
        self.selectEnd.dateTimeChanged.connect(self.time_filter)
        grid.addWidget(self.selectEnd,5,1,2,1)

        self.maxTS = QPushButton('Max')
        self.maxTS.setFixedWidth(30)
        self.maxTS.clicked.connect(self.set_end_max)
        grid.addWidget(self.maxTS,5,2,2,1)

        self.cycle = QPushButton('Cycle Axes')
        self.cycle.clicked.connect(lambda: self.cycle_subplot(parent.axes_frame.current_sps))
        grid.addWidget(self.cycle,1,3,2,1)

        self.legendToggle = QCheckBox('Legend')
        self.legendToggle.clicked.connect(lambda: self.toggle_legend(parent.axes_frame.current_sps))
        grid.addWidget(self.legendToggle,3,3,2,1)

        self.colorCoord = QCheckBox('Color by Unit')
        self.colorCoord.clicked.connect(lambda: self.color_coordinate(parent.axes_frame.current_sps))
        grid.addWidget(self.colorCoord,5,3,2,1)

        self.insert = QPushButton('Insert')
        self.insert.clicked.connect(lambda: self.insert_subplot(parent.axes_frame.current_sps))
        grid.addWidget(self.insert,1,4,2,1)

        self.delete = QPushButton('Delete')
        self.delete.clicked.connect(lambda: self.delete_subplot(parent.axes_frame.current_sps))
        grid.addWidget(self.delete,3,4,2,1)

        self.clear = QPushButton('Clear')
        self.clear.clicked.connect(lambda: self.clear_subplot(parent.axes_frame.current_sps))
        grid.addWidget(self.clear,5,4,2,1)

        self.reorderUp = QPushButton()
        self.reorderUp.setIcon(self.style().standardIcon(getattr(QStyle, 'SP_TitleBarShadeButton')))
        self.reorderUp.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.reorderUp.clicked.connect(lambda: self.reorder(parent.axes_frame.current_sps, 'up'))
        grid.addWidget(self.reorderUp,1,5,3,1)

        self.reorderDown = QPushButton()
        self.reorderDown.setIcon(self.style().standardIcon(getattr(QStyle, 'SP_TitleBarUnshadeButton')))
        self.reorderDown.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.reorderDown.clicked.connect(lambda: self.reorder(parent.axes_frame.current_sps, 'down'))
        grid.addWidget(self.reorderDown,4,5,3,1)

        col_weights = [.01, .01, .01, 1, 1, .01]
        for i,cw in enumerate(col_weights):
            grid.setColumnStretch(i,cw)
        self.setLayout(grid)

    def wte(self):
        self.weights_edited = True

    def tte(self):
        self.title_edited = True

    def cleanup_axes(self):
        """Manages axes ticks, tick labels, and gridlines for the whole figure."""
        AB = self.parent
        AF = AB.axes_frame
        FS = AB.figure_settings

        for i, sp in enumerate(AF.subplots):
            # All subplots
            self.toggle_grid(sp)
            for ax in sp.axes:
                ax.tick_params(axis='y', labelsize=FS.tickSize.value())

            # Lowest subplot
            if i == len(AF.subplots)-1:  # Bottom-most subplot only
                # Tell the host axes' xaxis it's plotting dates
                sp.host().xaxis_date()
                # Give focus to host axes
                plt.sca(sp.host())
                if not sp.contents:  # maybe in the future: go through subplots, find one with contents, use its xaxis ticks/labels as base xaxis ticks/labels (quality of life)
                    # If subplot is empty, don't show xaxis ticks
                    sp.host().tick_params(axis='x', labelbottom=False, bottom=False)
                else:
                    # Otherwise, set host axes' xaxis major formatter, locator, and minor locator
                    sp.host().tick_params(axis='x', labelbottom=True, bottom=True)
                    plt.xticks(rotation=FS.tickRot.value(), ha='right', fontsize=FS.tickSize.value())
                plt.yticks(fontsize=FS.tickSize.value())

            # All other subplots
            else:
                sp.host().tick_params(axis='x', which='major', labelbottom=False)


    def toggle_grid(self, sp):
        """Controls whether X/Y, major/minor gridlines are displayed in subplot sp."""
        AB = self.parent
        FS = AB.figure_settings
        linestyles = ['-', '--', ':', '-.']

        if FS.majorXgrid.isChecked():
            sp.host().xaxis.grid(which='major')
        if FS.minorXgrid.isChecked():
            sp.host().minorticks_on()
#            sp.host().tick_params(axis='x', which='minor', bottom=True)
            sp.host().xaxis.grid(which='minor')
        if FS.majorYgrid.isChecked():
            for i, ax in enumerate(sp.axes):
                ax.yaxis.grid(which='major', linestyle=linestyles[i%len(linestyles)])
        if FS.minorYgrid.isChecked():
            for i, ax in enumerate(sp.axes):
                ax.minorticks_on()  # turns both x and y on, don't know how to only get it on one axis
#                ax.tick_params(axis='y', which='minor')
                ax.yaxis.grid(b=True, which='minor', linestyle=linestyles[i%len(linestyles)])

    def cap_start_end(self):
        """Limits the figure start and end datetimes by the extent of the loaded data."""
        AB = self.parent
        try:
            data_start = min([AB.groups[name].data.index[0] for name in AB.groups.keys()])
            self.start = max([data_start, self.start])
            data_end = max([AB.groups[name].data.index[-1] for name in AB.groups.keys()])
            self.end = min([data_end, self.end])

            self.selectStart.setMinimumDateTime(data_start)
            self.selectStart.setMaximumDateTime(self.end)
            self.selectEnd.setMaximumDateTime(data_end)
            self.selectEnd.setMinimumDateTime(self.start)
        except ValueError:
            self.selectStart.setMinimumDateTime(dt.datetime.strptime('2000-01-01 00:00:00', '%Y-%m-%d  %H:%M:%S'))
            self.selectStart.setMaximumDateTime(self.end)
            self.selectEnd.setMaximumDateTime(QDateTime.currentDateTime())
            self.selectEnd.setMinimumDateTime(self.start)
        return self.start, self.end

    def set_start_min(self):
        self.selectStart.setDateTime(self.selectStart.minimumDateTime())

    def set_end_max(self):
        self.selectEnd.setDateTime(self.selectEnd.maximumDateTime())

    def time_filter(self):
        """Determines timestamp format and major/minor x-axis locators based on the plotted timespan."""
        AB = self.parent
        AF = AB.axes_frame
        self.start = self.selectStart.dateTime().toPyDateTime()
        self.end = self.selectEnd.dateTime().toPyDateTime()
        self.start, self.end = self.cap_start_end()
        self.timespan = self.end - self.start

        if self.timespan >= dt.timedelta(days=4):
            self.dateformat = mdates.DateFormatter('%d %b %Y')
            self.major_locator = mdates.DayLocator()
            self.minor_locator = mdates.HourLocator(interval=12)
        elif self.timespan >= dt.timedelta(days=2) and self.timespan < dt.timedelta(days=4):
            self.dateformat = mdates.DateFormatter('%d/%b %H:%M')
            self.major_locator = mdates.DayLocator()
            self.minor_locator = mdates.HourLocator(interval=12)
        else:
            self.dateformat = mdates.DateFormatter('%d %b %Y %H:%M dalla dalla biyul yall')
            self.major_locator = mdates.HourLocator(interval=2)
            self.minor_locator = mdates.HourLocator(interval=1)
        for sp in AF.subplots:
            for ax in sp.axes:
                ax.xaxis.set_major_formatter(self.dateformat)
                ax.xaxis.set_major_locator(self.major_locator)
                ax.xaxis.set_minor_locator(self.minor_locator)
        AF.refresh_all()

    def reorder(self, sps, direction):
        """Reorders selected subplot up or down."""
        AB = self.parent
        AF = AB.axes_frame
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
                AF.current_sps = [AF.subplots[i]]
                AF.refresh_all()
        else:
            AB.statusBar().showMessage('Select one subplot to reorder')

    def insert_subplot(self, sps):
        """Inserts blank subplot below selected subplot."""
        AB = self.parent
        AF = AB.axes_frame

        # Determine index at which to insert blank subplot
        if len(sps) != 1:
            index = len(AF.subplots)-1
#            AB.statusBar().showMessage('No singular subplot selected. Subplot inserted at end.')
        else:
            index = sps[0].index

        # Insert blank Subplot_Manager at position below index (I feel like I shouldn't have to explicitly assign default arguments here, but hey)
        AF.subplots.insert(index+1, Subplot_Manager(AB, [None], order=[None], contents={}, index=None, legend=False, colorCoord=False))
        AF.weights.insert(index+1, 1)
        AF.refresh_all()

    def delete_subplot(self, sps):
        """Deletes selected subplot(s) and adds contents back into available tree."""
        AB = self.parent
        if sps:
            AF = AB.axes_frame
            SF = AB.series_frame
            indices = [sp.index for sp in sps]
            for i in reversed(indices):
                if len(AF.subplots) == 1:
                    self.clear_subplot(sps)
                else:
                # Delete entries at selected indices from weights, current selection, and Subplot_Managers
                    AF.available_data = SF.add_to_contents(AF.available_data, AF.subplots[i].contents)
                    SF.populate_tree(AF.available_data, SF.available)  # add contents back into available tree
                    del AF.weights[i]
                    del AF.subplots[i]
            AF.current_sps = []  # deselect everything
            AF.refresh_all()
        else:
            AB.statusBar().showMessage('Select one or more subplots to delete')

    def clear_subplot(self, sps):
        """Adds selected subplot's contents back into available tree, clears axis."""
        AB = self.parent
        if sps:
            AF = AB.axes_frame
            SF = AB.series_frame
            SF.plotted.clear()
            for sp in sps:
                AF.available_data = SF.add_to_contents(AF.available_data, sp.contents)
                SF.populate_tree(AF.available_data, SF.available)
                SF.search(SF.searchAvailable, SF.available, AF.available_data)
                sp.contents = {}
                sp.order = [None]
                sp.plot(skeleton=True)
            AF.refresh_all()
#            if len(sps) > 1: AB.statusBar().showMessage('Cleared subplots: {}'.format(sorted([sp.index for sp in sps])))
#            else: AB.statusBar().showMessage('Cleared subplot: {}'.format(sps[0].index))
        else:
            AB.statusBar().showMessage('Select one or more subplots to clear')

    def toggle_legend(self, sps):
        """Toggles legend display of selected subplot(s)."""
        AB = self.parent
        if sps:
            AF = AB.axes_frame
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
            AB.statusBar().showMessage('Select one or more subplots to toggle legend')

    def color_coordinate(self, sps):
        """Coordinates color of lines and axis labels in selected subplot(s) by unit type."""
        AB = self.parent
        if sps:
            AF = AB.axes_frame
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
            AB.statusBar().showMessage('Select one or more subplots to toggle color coordination')

    def cycle_subplot(self, sps):
        """Cycles through unit order permutations of selected subplot(s)."""
        AB = self.parent
        if sps:
            AF = AB.axes_frame
            for sp in sps:
                perms = [list(p) for p in sorted(itertools.permutations(sp.order))]
                i = perms.index(sp.order)
                sp.order = perms[(i+1)%len(perms)]
            AF.refresh_all()
        else:
            AB.statusBar().showMessage('Select one or more subplots to cycle unit plotting order')

    def adjust_weights(self):
        """Adjusts subplot vertical aspect ratios based on provided list of weights or sequence of digits."""
        if self.weights_edited:
            AB = self.parent
            AF = AB.axes_frame
            weights = []
            for i in self.weightsEdit.text():  # parse weighting input
                if i.isdigit():
                    weights.append(int(i))
                elif i in ', []':  # ignore commas, spaces, and brackets
                    continue
                else:
                    AB.statusBar().showMessage('Only integer inputs <10 allowed')
                    return
            if len(weights) != len(AF.subplots):
                AB.statusBar().showMessage('Figure has {} subplots but {} weights were provided'.format(len(AF.subplots), len(weights)))
                return
            AF.weights = weights
            AF.refresh_all()
            self.weights_edited = False

    def rename(self):
        """Renames figure."""
        if self.title_edited:
            AB = self.parent
            AF = AB.axes_frame
            FS = AB.figure_settings
            fig_title = re.sub('[\\\\.]', '', self.titleEdit.text())  # get rid of any backslashes or dots
            if not fig_title:
                AF.fig.suptitle('')
                fig_title = 'New_Figure'
            else:
                AF.fig.suptitle(fig_title, fontsize=FS.titleSize.value())
                AB.filename = fig_title
            AF.draw()
            AB.saved = False
            self.title_edited = False


class Series_Frame(QWidget):
    """Displays hierarchical string references to imported data groups/aliases.
    Available tree shows series which have not yet been plotted.
    Plotted tree shows contents of selected subplot."""

    def __init__(self, parent):
        super().__init__()
        self.parent = parent
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
        """Sorts both trees and deletes any group references that contain no series."""
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
        """Returns contents dictionary extended by items in to_add."""
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
        """Returns contents dictionary without items in to_remove."""
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
        """Swaps series or entire group references from available to plotted or vice versa."""
        AB = self.parent
        AF = AB.axes_frame
        selected_sps = AF.current_sps
        if not selected_sps:
            AB.statusBar().showMessage('Select a subplot to add or remove series')
        elif len(selected_sps) > 1:
            AB.statusBar().showMessage('Series can only be added to one subplot')
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
#                sp.axes = [sp.host()]
                sp.plot(skeleton=True)
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
                AB.statusBar().showMessage('No series selected')

    def get_sp_contents(self):
        """Returns contents of selected subplot if exactly one is selected, otherwise returns an empty dictionary."""
        AB = self.parent
        AF = AB.axes_frame
        if len(AF.current_sps) == 1:
            contents = AF.current_sps[0].contents
        else:
            contents = {}
        return contents

    def search(self, search_bar, tree, data_set):
        """Displays series in tree which match input to search_bar (case insensitive)"""
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
    """Associates unit type with color."""

    def __init__(self, parent, color, unit_type):
        super(QColorButton, self).__init__()
        self.setFixedSize(20,20)
        self.parent = parent
        self.color = color
        self.setStyleSheet("background-color:{};".format(color))
        self.unit_type = unit_type


class Figure_Settings(QWidget):
    """Contains options for controlling figure size and appearance."""

    def __init__(self, parent, saved=None):
        super().__init__()
        self.parent = parent
        AB = self.parent
#        mpl.rc('font', family='serif')  # controllable later maybe
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
# Read saved values from .txt file?

        vbox = QVBoxLayout()

        figureGroup= QGroupBox('Figure Dimensions')
        figureGroup.setAlignment(Qt.AlignHCenter)
        form = QFormLayout()
        self.upperPad = QDoubleSpinBox()
        self.upperPad.setRange(0, 0.5)
        self.upperPad.setSingleStep(.01)
        self.upperPad.setValue(0.07)
        form.addRow('Upper Pad',self.upperPad)
        self.lowerPad = QDoubleSpinBox()
        self.lowerPad.setRange(0, 0.5)
        self.lowerPad.setSingleStep(.01)
        self.lowerPad.setValue(0.08)
        form.addRow('Lower Pad',self.lowerPad)
        self.leftPad = QDoubleSpinBox()
        self.leftPad.setRange(0, 0.5)
        self.leftPad.setSingleStep(.01)
        self.leftPad.setValue(0.05)
        form.addRow('Left Pad',self.leftPad)
        self.rightPad = QDoubleSpinBox()
        self.rightPad.setRange(0, 0.5)
        self.rightPad.setSingleStep(.01)
        self.rightPad.setValue(0.05)
        form.addRow('Right Pad',self.rightPad)
        self.hspace = QDoubleSpinBox()
        self.hspace.setRange(0, 1)
        self.hspace.setSingleStep(.01)
        self.hspace.setValue(.05)
        form.addRow('Spacing',self.hspace)
        self.parOffset = QDoubleSpinBox()
        self.parOffset.setRange(0, 1)
        self.parOffset.setDecimals(3)
        self.parOffset.setSingleStep(.005)
        self.parOffset.setValue(.05)
        form.addRow('Axis Offset',self.parOffset)
        figureGroup.setLayout(form)
        vbox.addWidget(figureGroup)


        gridGroup = QGroupBox('Grid Settings')
        gridGroup.setAlignment(Qt.AlignHCenter)
        grid = QGridLayout()
        self.majorXgrid = QCheckBox('Major X')
        grid.addWidget(self.majorXgrid, 0, 0)
        self.minorXgrid = QCheckBox('Minor X')
        grid.addWidget(self.minorXgrid, 0, 1)
        self.majorYgrid = QCheckBox('Major Y')
        grid.addWidget(self.majorYgrid, 1, 0)
        self.minorYgrid = QCheckBox('Minor Y')
        grid.addWidget(self.minorYgrid, 1, 1)
        gridGroup.setLayout(grid)
        vbox.addWidget(gridGroup)

        plotGroup = QGroupBox('Plot Settings')
        plotGroup.setAlignment(Qt.AlignHCenter)
        grid = QGridLayout()
        self.line = QRadioButton('Line')
        grid.addWidget(self.line, 0, 0)
        self.scatter = QRadioButton('Scatter')
        self.scatter.setChecked(True)
        grid.addWidget(self.scatter, 0, 1)
        grid.addWidget(QLabel('Marker Size'), 1, 0)
        self.dotsize = QDoubleSpinBox()
        self.dotsize.setRange(0, 5)
        self.dotsize.setSingleStep(.1)
        self.dotsize.setValue(0.5)
        grid.addWidget(self.dotsize, 1, 1)
        grid.addWidget(QLabel('Plot Density'), 2, 0)
        self.density = QSpinBox()
        self.density.setRange(0, 100)
        self.density.setSingleStep(5)
        self.density.setValue(100)
        self.density.setSuffix('%')
        grid.addWidget(self.density, 2, 1)
        plotGroup.setLayout(grid)
        vbox.addWidget(plotGroup)

        textGroup = QGroupBox('Text Settings')
        textGroup.setAlignment(Qt.AlignHCenter)
        form = QFormLayout()
        self.titleSize = QSpinBox()
        self.titleSize.setRange(0, 60)
        self.titleSize.setValue(30)
        form.addRow('Title', self.titleSize)
        self.labelSize = QSpinBox()
        self.labelSize.setRange(0, 30)
        self.labelSize.setValue(12)
        form.addRow('Axis Labels', self.labelSize)
        self.tickSize = QSpinBox()
        self.tickSize.setRange(0, 20)
        self.tickSize.setValue(10)
        form.addRow('Tick Size', self.tickSize)
        self.tickRot = QSpinBox()
        self.tickRot.setRange(0, 90)
        self.tickRot.setValue(45)
        form.addRow('Tick Rotation', self.tickRot)
        textGroup.setLayout(form)
        vbox.addWidget(textGroup)

        self.unit_table = QTableWidget()
        self.unit_table.setFixedWidth(123)
        self.unit_table.setColumnCount(2)
        self.unit_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        self.unit_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeToContents)
        self.unit_table.horizontalHeader().hide()
        self.unit_table.verticalHeader().hide()
        self.unit_table.verticalHeader().setDefaultSectionSize(self.unit_table.verticalHeader().minimumSectionSize())
        self.unit_table.verticalHeader().setSectionResizeMode(QHeaderView.Fixed)
        self.unit_table.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        vbox.addWidget(self.unit_table)
        self.setLayout(vbox)

        self.dlg = QColorDialog()
        self.dlg.setWindowIcon(QIcon('rc/satellite.png'))
        default_color = AB.current_rcs['axes.labelcolor']
        self.color_dict = {None:default_color, '':default_color}
        self.update_unit_table()

    def update_unit_table(self):
        """Updates table associating unit types with colors."""
        AB = self.parent
        all_units = {**AB.unit_dict, **AB.user_units}
        self.unit_table.setRowCount(len(all_units))
        for i, unit_type in enumerate(all_units):
            if unit_type not in self.color_dict:
                self.color_dict.update({unit_type:'C'+str(i%10)})
        for i, unit_type in enumerate(all_units):
            self.dlg.setCustomColor(i, QColor(mcolors.to_hex(self.color_dict[unit_type])))
        for i, unit_type in enumerate(all_units):
            self.unit_table.setItem(i, 0, QTableWidgetItem(unit_type))
            colorButton = QColorButton(self, mcolors.to_hex(self.color_dict[unit_type]), unit_type)
            colorButton.clicked.connect(self.pick_color)
            _widget = QWidget()
            _layout = QHBoxLayout(_widget)
            _layout.addWidget(colorButton)
            _layout.setAlignment(Qt.AlignCenter)
            _layout.setContentsMargins(0,0,0,0)
            self.unit_table.setCellWidget(i, 1, _widget)

    def connect_widgets(self, container):
        """Connects widgets to refresh_all() in Axes Frame.
        Called by Application Base after Axes Frame has been instantiated."""
        widgets = [
                self.upperPad,
                self.lowerPad,
                self.leftPad,
                self.rightPad,
                self.hspace,
                self.parOffset,
                self.dotsize,
                self.titleSize,
                self.labelSize,
                self.tickSize,
                self.tickRot,
                self.density,
                ]
        for w in widgets:
            w.valueChanged.connect(container.refresh_all)

        widgets = [
                self.majorXgrid,
                self.minorXgrid,
                self.majorYgrid,
                self.minorYgrid,
                self.line,
                self.scatter,
                ]
        for w in widgets:
            w.toggled.connect(container.refresh_all)

    def pick_color(self):
        """Opens a color picker dialog and assigns it to the associated unit type."""
        colorButton = QObject.sender(self)
        unit_type = colorButton.unit_type
        if colorButton.color:
            self.dlg.setCurrentColor(QColor(colorButton.color))

        if self.dlg.exec_():
            colorButton.color = self.dlg.currentColor().name()
            colorButton.setStyleSheet("background-color:{};".format(colorButton.color))
            self.color_dict[unit_type] = colorButton.color
            AB = self.parent
            AF = AB.axes_frame
            AF.refresh_all()


class Data_Manager(QDialog):
    """Manages the importing of data and configuration of data groups."""

    def __init__(self, parent):
        super().__init__()
        self.parent = parent
        self.setWindowTitle('Data Manager')
        self.setWindowIcon(QIcon('rc/satellite.png'))

        self.groups = copy.deepcopy(parent.groups)  # copy so that if you can still discard changes
        self.group_reassign = {name:[name] for name in self.groups}  # for renaming groups
#        print(self.group_reassign)

        self.modified = False

        self.resize(1000,500)
        grid = QGridLayout()
        self.tabBase = QTabWidget()
#        self.tabBase.setStyleSheet("QTabBar::tab {height: 30px; width: 300px} QTabWidget::tab-bar {alignment:center;}")
        grid.addWidget(self.tabBase,0,0,1,3)

        msgLog = QLabel('Message Log:')
        grid.addWidget(msgLog,1,0)

        self.messageLog = QTextEdit()
        self.messageLog.setReadOnly(True)
#        self.messageLog.setText('Ready')
        grid.addWidget(self.messageLog,1,1,2,1)

        self.save = QPushButton('Save')
        self.save.setDefault(True)
        self.save.clicked.connect(self.save_changes)
        grid.addWidget(self.save,1,2)

        self.cancel = QPushButton('Cancel')
        self.cancel.clicked.connect(self.close)
        grid.addWidget(self.cancel,2,2)

        grid.setColumnStretch(1,100)
        self.setLayout(grid)

#        self.import_tab = Import_Tab(self)
        self.groups_tab = Groups_Tab(self)
        self.configure_tab = Configure_Tab(self)
        self.groups_tab.search_dir()

#        self.tabBase.addTab(self.import_tab, 'Import Settings')
        self.tabBase.addTab(self.groups_tab, 'File Grouping')
        self.tabBase.addTab(self.configure_tab, 'Series Configuration')

    def keyPressEvent(self, event):
        """Close dialog from escape key."""
        if event.key() == Qt.Key_Escape:
            self.close()

    def feedback(self, message, mode='line'):
        """Adds message to message log as one line.
        Set mode=overwrite to overwrite the last line in the log.
        Set mode=append to append the last line in the log."""
        if self.messageLog.toPlainText():
            if mode == 'line':
                self.messageLog.setText(self.messageLog.toPlainText() + '\n' + message)
            elif mode == 'append':
                self.messageLog.setText(self.messageLog.toPlainText() + message)
            elif mode == 'overwrite':
                current_text = self.messageLog.toPlainText()
                self.messageLog.setText(current_text[:current_text.rfind('\n')+1] + message)
        else:
            self.messageLog.setText(message)
        self.messageLog.verticalScrollBar().setValue(self.messageLog.verticalScrollBar().maximum())

    def save_changes(self):
        """Saves groups created in Data Manager dialog to Application Base main window.
        Maps existing data to new data within subplots and in available tree, saving the user the trouble of repopulating the subplots every time a change is made."""
        if self.modified:
            AB = self.parent
            SF = AB.series_frame
            CF = AB.control_frame
            AF = AB.axes_frame

            # Get new alias/unit information from self.groups
            new_contents = AB.groups_to_contents(self.groups)

            # Rename/delete groups in subplots first
            for sp in AF.subplots:
                for group_name in copy.copy(tuple(sp.contents.keys())):
                    # Try to reassign group name
                    if group_name in self.group_reassign:
                        new_name = self.group_reassign[group_name][-1] # get new name
                        new_series = self.groups[new_name].series

                        aliases = copy.copy(tuple(sp.contents[group_name].keys()))
                        for alias in aliases:
                            del sp.contents[group_name][alias]  # delete the alias entry first in case alias == new_alias

                            try:
                                header = AB.groups[group_name].alias_dict[alias]  # get original header of each alias in sp.contents
                            except KeyError:  # if original header being used as alias (because no alias was assigned)
                                header = alias
                            if header in new_series and new_series[header].keep:
                                new_alias = new_series[header].alias
                                if not new_alias:
                                    unit = new_series[header].unit
                                    new_alias = re.sub('\[{}\]'.format(unit), '', header).strip()
                                sp.contents[group_name][new_alias] = new_series[header].unit
                                del new_contents[new_name][new_alias]
                            if not new_contents[new_name]: del new_contents[new_name]

                        transfer = sp.contents[group_name] # transfer contents from old to new
                        del sp.contents[group_name] # scrap the old
                        sp.contents[new_name] = transfer  # transfer variable because if you do a 1:1 assignment it will get deleted right away if the group wasn't renamed!
                    else:
                        del sp.contents[group_name] # scrap it because it doesn't exist in new_contents
                SF.update_subplot_contents(sp, sp.contents)  # hopefully will take care of the ghost unit problem
            AB.groups = self.groups
            CF.time_filter()  # calls AF.refresh_all()
            #reset group_reassign
            self.group_reassign = {name:[name] for name in self.groups}
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
        """Asks user to confirm exit if changes have been made and not saved."""
        AB = self.parent
        if self.modified:
            choice = AB.popup('Discard changes?', title='Exiting Data Manager')
            if choice == QMessageBox.Cancel:
                event.ignore()
                return
            elif choice == QMessageBox.Save:
                self.save_changes()
        QApplication.clipboard().clear()
        event.accept()


class Groups_Tab(QWidget):
    """Allows the user to organize source files into groups and import them as compiled DataFrames."""

    def __init__(self, parent):
        super().__init__()
        self.parent = parent
        DM = self.parent
        self.importsettings = QWidget()

        self.path_dict = {}
        self.df_preview = {}
        self.dir = os.getcwd()

        vbox = QVBoxLayout()
        hbox = QHBoxLayout()
        self.browse = QPushButton()
        self.browse.setIcon(self.style().standardIcon(getattr(QStyle, 'SP_DialogOpenButton')))
        self.browse.clicked.connect(self.browse_dialog)
        hbox.addWidget(self.browse)
        self.directory = QLineEdit(self.dir)
        self.directory.returnPressed.connect(self.search_dir)
        hbox.addWidget(self.directory)
        vbox.addLayout(hbox)

        grid = QGridLayout()

        self.fileSearch = QLineEdit()
        self.fileSearch.setPlaceholderText('Search')
        self.fileSearch.textChanged.connect(self.filter_files)
        self.fileSearch.setFocus(True)
        grid.addWidget(self.fileSearch, 0, 0)

        self.groupName = QLineEdit('Test')  # delete initial text later #!!!
        self.groupName.setPlaceholderText('Group Name')
        self.groupName.returnPressed.connect(self.import_group)
        grid.addWidget(self.groupName, 0, 1)

        self.importGroup = QPushButton('Import Group')
        self.importGroup.clicked.connect(self.import_group)
        self.importGroup.setDefault(True)
        grid.addWidget(self.importGroup, 0, 2)

        foundFilesLabel = QLabel('Found Files')
        grid.addWidget(foundFilesLabel, 1, 0)

        groupFilesLabel = QLabel('Files in Group')
        grid.addWidget(groupFilesLabel, 1, 1)

        importedGroupsLabel = QLabel('Imported Groups')
        grid.addWidget(importedGroupsLabel, 1, 2)

        self.foundFiles = QListWidget()
        self.foundFiles.setSelectionMode(QListWidget.ExtendedSelection)
        grid.addWidget(self.foundFiles, 2, 0)

        self.groupFiles = QListWidget()
        self.groupFiles.setSelectionMode(QListWidget.ExtendedSelection)
        grid.addWidget(self.groupFiles, 2, 1)

        self.importedGroups = QListWidget()
        self.importedGroups.addItems(DM.groups.keys())
        self.importedGroups.itemDoubleClicked.connect(self.rename_group)
        grid.addWidget(self.importedGroups, 2, 2)

        self.add = QPushButton('Add to Group')
        self.add.clicked.connect(lambda: self.toggle_file_active('Add'))
        grid.addWidget(self.add, 3, 0)

        self.remove = QPushButton('Remove from Group')
        self.remove.clicked.connect(lambda: self.toggle_file_active('Remove'))
        grid.addWidget(self.remove, 3, 1)

        self.deleteGroup = QPushButton('Delete Group')
        self.deleteGroup.clicked.connect(self.delete_group)
        grid.addWidget(self.deleteGroup, 3, 2)

        vbox.addLayout(grid)
        self.setLayout(vbox)

    def interpret_data(self, path, read_func=pd.read_csv):
        dtf = 'Infer'
        r, c = self.parse_df_origin(path, read_func)
        skiprows = None
        return dtf, r, c, skiprows

    def search_dir(self):
        """Searches current directory and displays found files.
        Newly found files are given an entry with default values in a dictionary associating filepaths and reading kwargs."""
        path = self.directory.text()
        self.dir = path
        self.loaded_files, new_path_dict_entries = self.gather_files(path)
        self.path_dict.update(new_path_dict_entries)
        self.fileSearch.setText('')
        self.foundFiles.clear()
        self.foundFiles.addItems(self.loaded_files)

    def browse_dialog(self):
        """Opens a file dialog to select a working directory and displays found files."""
        path = str(QFileDialog.getExistingDirectory(self, "Select Directory"))
        if path:
            self.directory.setText(path)
            self.search_dir()

    def gather_files(self, path):
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

    def filter_files(self):
        """Displays files in found files list which match searchbar input."""
        DM = self.parent
        pattern = re.compile(self.fileSearch.text(), re.IGNORECASE)
        matches = [item for item in DM.groups_tab.loaded_files if re.search(pattern,item)]
        self.foundFiles.clear()
        self.foundFiles.addItems(matches)

    def toggle_file_active(self, caller):
        """Transfers file to or from group file list."""
        DM = self.parent
        if caller == 'Add':
            for file in self.foundFiles.selectedItems():
                if file.text() in [self.groupFiles.item(i).text() for i in range(self.groupFiles.count())]:
                    DM.feedback('{} already added'.format(file.text()))
                else:
                    self.groupFiles.addItem(file.text())
        elif caller == 'Remove':
            for file in self.groupFiles.selectedItems():
                self.groupFiles.takeItem(self.groupFiles.row(file))

    def rename_group(self, item):
        """Renames imported group.
        Keeps track of past renaming operations so Data Manager's save changes can identify existing groups as having been renamed.
        Accessible by double clicking on an imported group."""
        DM = self.parent
        try:
            group_name = item.text()
            new_name, ok = QInputDialog.getText(self, 'Rename Group "{}"'.format(group_name), 'New group name:', QLineEdit.Normal, group_name)
            if ok and new_name != group_name:
                if new_name in DM.groups:
                    DM.feedback('Group "{}" already exists. Please choose a different name.'.format(new_name))
                else:
                    # Create new entry in DM.groups with new_name, give it old group's info, scrap the old one
                    DM.groups[new_name] = DM.groups[group_name]
                    del DM.groups[group_name]
                    # Append new name list of renames
                    # DM.group_reassign looks like {AB name: [AB name, rename1, rename2... DM name]}
                    for name in DM.group_reassign:
                        if group_name == DM.group_reassign[name][-1]:
                            DM.group_reassign[name].append(new_name)
                            break
                    i = self.importedGroups.row(item)
                    self.importedGroups.takeItem(i)
                    self.importedGroups.insertItem(i, QListWidgetItem(new_name))
                    i = DM.configure_tab.selectGroup.findText(group_name)
                    DM.configure_tab.selectGroup.blockSignals(True)
                    DM.configure_tab.selectGroup.removeItem(DM.configure_tab.selectGroup.findText(group_name))
                    DM.configure_tab.selectGroup.blockSignals(False)
                    DM.configure_tab.selectGroup.insertItem(i, new_name)
                    DM.modified = True
        except IndexError as e:
            print(e)

    def parse_df_origin(self, path, read_func, nrows=20):
        """Tries to identify the cell at which the header row and index column intersect.
        - Loop through the first 20 rows of each column.
        - If cell can be parsed as a datetime, return coordinates of cell directly above.
        - If no cells can be parsed, return Nones."""
        n = 1
        while n <= nrows:  # avoid asking for more rows than there are
            try:
                df = read_func(path, nrows=n, header=None, encoding='latin1')
                n += 1
            except IndexError:
                if 'df' not in locals(): df = pd.DataFrame()
                break

        for c in range(len(df.columns)):
            for r in range(len(df.index)):
                try:
                    ts0 = pd.to_datetime(df.iloc[r, c], infer_datetime_format=True)
                    if ts0 is not pd.NaT:
                        if not r:  # if first row is parseable, inconclusive
                            r = None
                        else:  # else return cell above first parseable cell
                            r = r-1
                        return r, c
                except ValueError:
                    pass
        return None, 0

    def floatify(self, data):
        """Strips data down to float.
        - Try to return data as float.
        - If not possible, try to interpret data as quasi-boolean and return 1.0 or 0.0.
        - If not quasi-boolean, scrub away everything but numbers, minus signs, and decimals and return as float.
        - Return NaN if all other attempts fail."""
        try:
            return float(data)  # try returning data as float as-is. Should speed things up.
        except (ValueError, TypeError):
            if str(data).lower() in ('on','true','yes','enabled'): return 1.0
            if str(data).lower() in ('off','false','no','disabled'): return 0.0
            try:
                scrubbed = re.sub(',', '.', str(data))  # allow for German-style decimals (1,2 -> 1.2 but 1,2, -> 1.2. will still fail appropriately)
                scrubbed = re.sub('[^0-9-.]', '', scrubbed)
                return float(scrubbed)
            except ValueError:
                return np.nan

    def combine_files(self, pathlist):
        DM = self.parent
        AB = DM.parent
        dflist = []
        counter = 1
        for path in pathlist:
            mode = 'line' if counter == 1 else 'overwrite'
            DM.feedback('Reading files into group "{}": ({}/{})... '.format(self.groupName.text(), counter, len(pathlist)), mode=mode)
            DM.messageLog.repaint()
            counter += 1

            # Get parse kwargs associated with file
            path_kwargs = {'encoding':'latin1'}  # just load the dang file as-is
            path_kwargs.update(AB.path_kwargs[path])

            #this is kinda sloppy
            del path_kwargs['format']  # because it gets used somewhere else but comes from the same dictionary
            if AB.path_kwargs[path]['format'].lower() == 'infer':  #??? this will be changed from infer to a parsed format
                dtf = None
            else:
                dtf = AB.path_kwargs[path]['format']

#            if path.endswith('xls') or path.endswith('xlsx'):
#                read_func = pd.read_excel
##                    path_kwargs.update({'sheet_name':None})  # read all sheets
#            elif path.endswith('csv') or path.endswith('zip'):
#                read_func = pd.read_csv

            try:
                # Sunrise Test.csv: 2009-06-06 14:49:01.000
                # dtf = %Y-%m-%d %H:%M:%S.%f

                start = dt.datetime.now()
                data = pd.read_csv(path, **path_kwargs)
                data.index.names = ['Timestamp']
                data.columns = data.columns.map(str)  # convert headers to strings
                data.index = pd.to_datetime(data.index, infer_datetime_format=True, format=dtf)
                end = dt.datetime.now()
                print(dtf, end-start)
                if any(ts == pd.NaT for ts in data.index): raise ValueError('Timestamps could not be parsed from given index column. Check import settings.')

                dflist.append(data)
            except ValueError as e:
                for file in DM.groups_tab.path_dict:
                    if DM.groups_tab.path_dict[file] == path: source = file
                if 'source' not in locals(): source = path
                DM.feedback('Failed', mode='append')
                DM.feedback('File "{}" threw an error: {}'.format(source, e))
                return pd.DataFrame()
            AB.path_kwargs[path].update(path_kwargs)

        df = pd.concat(dflist, axis=0, sort=False)
        DM.feedback('Scrubbing data... ', mode='append')
        DM.messageLog.repaint()
        df = df.applymap(self.floatify)
        DM.feedback('Done', mode='append')
        return df.sort_index()

    def import_group(self):
        DM = self.parent
        AB = DM.parent
        group_name = self.groupName.text()
        loaded_groups = [self.importedGroups.item(i).text() for i in range(self.importedGroups.count())]

        # Use case filtering
        if group_name == '':
            DM.feedback('Group name cannot be empty.')
            return
        elif group_name in loaded_groups:
            if AB.popup('Group "{}" already exists. Overwrite?'.format(group_name), title='Importing Group', mode='confirm') == QMessageBox.Ok:
                self.importedGroups.takeItem(loaded_groups.index(group_name))
                #??? If group_name is a renaming of a previously loaded group, is that bad?
            else:
                return
        source_files = [self.groupFiles.item(i).text() for i in range(self.groupFiles.count())]  #read groupfiles listview
        if not source_files:
            DM.feedback('Group cannot have 0 associated files.')
            return

        if self.verify_import_settings(source_files):#result == QDialog.Accepted:
            source_paths = [self.path_dict[file] for file in source_files]  #path_dict is quasi global, appended gather_files (therefore, navigating to a different directory should not disconnect files from paths)
            df = self.combine_files(source_paths)#, header_row=0, ts_col='PacketTime', dtf='%Y-%m-%d %H:%M:%S.%f')  # These kwargs are specific to PHI_HK

            if not df.empty:
                DM.groups[group_name] = Group(df, source_files, source_paths)  # this is writing to Data_Manager's version, not AB's
                self.importedGroups.addItem(group_name)

                # Try to auto parse units
                if AB.auto_parse: self.parse_group_units([group_name])

                DM.configure_tab.selectGroup.addItem(group_name)  # -> this emits a signal to call CT's display_header_info function
                self.groupFiles.clear()
                self.groupName.setText('')
                DM.modified = True
        else:
            DM.feedback('Import canceled.', mode='append')

    def verify_import_settings(self, source_files):
        DM = self.parent
        AB = DM.parent
        counter = 1
        for file in source_files:
            mode = 'line' if counter == 1 else 'overwrite'
            DM.feedback('Loading previews: ({}/{})... '.format(counter, len(source_files)), mode=mode)
            DM.messageLog.repaint()
            counter += 1

            if file not in AB.path_kwargs:
                if file.endswith('xls') or file.endswith('xlsx'):
                    read_func = pd.read_excel
                elif file.endswith('csv') or file.endswith('zip'):
                    read_func = pd.read_csv

                path = self.path_dict[file]

                # Read first column and take its length so you can read head and tail later without loading the whole DF into memory
                shownRows = 20
                n = len(read_func(path, usecols=[0], header=None, encoding='latin1').index)

                if n > shownRows:
                    upper_df = read_func(path, nrows=shownRows//2, header=None, encoding='latin1')
                    lower_df = read_func(path, skiprows=range(n-shownRows//2), header=None, encoding='latin1')
                    ellipses = pd.DataFrame(['...']*len(upper_df.columns),
                                            index=upper_df.columns,
                                            columns=['...']).T
                    shown_df = upper_df.append(ellipses).append(lower_df)
                else:
                    shown_df = read_func(path, header=None, encoding='latin1')
                self.df_preview[path] = shown_df
                dtf, r, c, skiprows = self.interpret_data(path, read_func)
                AB.path_kwargs[self.path_dict[file]] = {'format':dtf, 'header':r, 'index_col':c, 'skiprows':skiprows}
        DM.feedback('Verify import settings... ', mode='append')
        DM.messageLog.repaint()
        self.importsettings = Import_Settings(self, source_files)
        self.importsettings.setModal(True)
        return self.importsettings.exec()

    def parse_group_units(self, group_names, update=False):
        DM = self.parent
        AB = DM.parent
        report = ''
        for group_name in group_names:
            group = DM.groups[group_name]
            for header in group.series:
                if not group.series[header].keep: continue
                header = str(header)
                parsed = AB.parse_unit(header)
                unit = AB.interpret_unit(parsed)
                group.series[header].unit = unit
                group.series[header].unit_type = AB.get_unit_type(unit)
                if not unit:
                    report += header + '\n'
                else:
                    alias = re.sub('\[{}\]'.format(parsed), '', header).strip()
                    group.series[header].alias = alias
                    group.alias_dict[alias] = header
            if update:
                DM.configure_tab.populate_headerTable(group)
        if report:
            AB.popup('Some units not assigned.',
                     title='Unit Parse Error Log',
                     informative='You can assign units manually under Series Configuration, leave them blank, or adjust unit settings and reparse.',
                     details=report,
                     icon=False,
                     mode='alert')

    def delete_group(self):
        DM = self.parent
        AB = DM.parent
        try:
            item = self.importedGroups.selectedItems()[0]
            group_name = item.text()
            if AB.popup('Delete group "{}"?'.format(group_name), mode='confirm') == QMessageBox.Ok:
                self.importedGroups.takeItem(self.importedGroups.row(item))
                del DM.groups[group_name]

                # delete the corresponding entry in group_reassign (if it exists)
                for name in DM.group_reassign:
                    if group_name == DM.group_reassign[name][-1]:
                        del DM.group_reassign[name]
                        DM.modified = True  # only modified if the deleted group was loaded into AB
                        break
                DM.configure_tab.selectGroup.removeItem(DM.configure_tab.selectGroup.findText(group_name))
        except IndexError as e:
            print(e)


class Import_Settings(QDialog):

    def __init__(self, parent, group_files):
        super().__init__()
        self.parent = parent
        self.setWindowTitle('Review Import Settings')
        self.setWindowIcon(QIcon('rc/satellite.png'))
        GT = self.parent
        DM = GT.parent
        AB = DM.parent
        self.resize(1000,500)
        self.group_files = group_files
        vbox = QVBoxLayout()
        splitter = QSplitter(Qt.Vertical)

        self.kwargTable = QTableWidget()
        self.kwargTable.verticalHeader().setDefaultSectionSize(self.kwargTable.verticalHeader().minimumSectionSize())
        self.kwargTable.verticalHeader().setSectionResizeMode(QHeaderView.Fixed)
        self.kwargTable.setRowCount(len(self.group_files))
        self.kwargTable.setColumnCount(5)
        self.kwargTable.setHorizontalHeaderLabels(['File', 'Datetime Format', 'Header Row', 'Index Column', 'Skip Rows'])
        self.kwargTable.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        self.kwargTable.horizontalHeader().setSectionResizeMode(1, QHeaderView.Fixed)
        self.kwargTable.horizontalHeader().setSectionResizeMode(2, QHeaderView.Fixed)
        self.kwargTable.horizontalHeader().setSectionResizeMode(3, QHeaderView.Fixed)
        self.kwargTable.horizontalHeader().setSectionResizeMode(4, QHeaderView.Fixed)
        self.kwargTable.itemSelectionChanged.connect(self.preview_df)
        self.kwargTable.cellChanged.connect(self.update_path_kwargs)
        splitter.addWidget(self.kwargTable)

        self.previewTable = QTableView()
        self.previewTable.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.previewTable.verticalHeader().setDefaultSectionSize(self.previewTable.verticalHeader().minimumSectionSize())
        self.previewTable.verticalHeader().hide()
        splitter.addWidget(self.previewTable)

        self.buttonBox = QDialogButtonBox()
        self.autoDetect = QPushButton('Auto-Detect')
        self.autoDetect.clicked.connect(self.auto_detect)
        self.buttonBox.addButton(self.autoDetect, QDialogButtonBox.ResetRole)
        self.buttonBox.setStandardButtons(QDialogButtonBox.Reset | QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        self.buttonBox.accepted.connect(self.accept)
        self.buttonBox.accepted.connect(self.apply_kwargs)
#        self.buttonBox.button(QDialogButtonBox.Ok).setAutoDefault(True)
        self.buttonBox.rejected.connect(self.reject)
        self.buttonBox.button(QDialogButtonBox.Reset).clicked.connect(self.reset)
        self.feedback = QLabel()
        layout = self.buttonBox.layout()
        layout.insertWidget(2, self.feedback)
        self.buttonBox.setLayout(layout)

        vbox.addWidget(splitter)
        vbox.addWidget(self.buttonBox)
        self.setLayout(vbox)

        self.original_kwargs = copy.deepcopy(AB.path_kwargs)
        self.current_kwargs = copy.deepcopy(self.original_kwargs)
        for i, file in enumerate(self.group_files):
            kwargs = self.current_kwargs[GT.path_dict[file]]
            self.kwargTable.setItem(i, 0, QTableWidgetItem(file))
            self.kwargTable.item(i, 0).setFlags(Qt.ItemIsSelectable)
            self.update_row_kwargs(i, kwargs)
        self.kwargTable.setCurrentCell(0, 1)

    def update_row_kwargs(self, row, kwargs):
        self.kwargTable.setItem(row, 1, QTableWidgetItem(str(kwargs['format'])))
        self.kwargTable.setItem(row, 2, QTableWidgetItem(str(kwargs['header'])))
        self.kwargTable.setItem(row, 3, QTableWidgetItem(str(kwargs['index_col'])))
        self.kwargTable.setItem(row, 4, QTableWidgetItem(str(kwargs['skiprows'])))

    def auto_detect(self):
        GT = self.parent
        selection = self.kwargTable.selectedIndexes()
        rows = set(sorted(index.row() for index in selection))
        for row in rows:
            file = self.kwargTable.item(row, 0).text()
            path = GT.path_dict[file]
            dtf, r, c, skiprows = GT.interpret_data(path)
            kwargs = {'format':dtf, 'header':r, 'index_col':c, 'skiprows':skiprows}
            self.update_row_kwargs(row, kwargs)

    def reset(self):
        GT = self.parent
        for i, file in enumerate(self.group_files):
            kwargs = self.original_kwargs[GT.path_dict[file]]
            self.kwargTable.setItem(i, 0, QTableWidgetItem(file))
            self.kwargTable.item(i, 0).setFlags(Qt.ItemIsSelectable)
            self.update_row_kwargs(i, kwargs)

    def update_path_kwargs(self, row, column):
        GT = self.parent
        pick_kwargs = {1:'format', 2:'header', 3:'index_col', 4:'skiprows'}
        if column not in pick_kwargs: return
        kwarg = pick_kwargs[column]
        file = self.kwargTable.item(row, 0).text()
        path = GT.path_dict[file]
        text = self.kwargTable.item(row, column).text().strip()

        ### input permissions
        # NO INPUT CONTROL ON FORMAT FIELD, SO YOU BETTER KNOW WHAT YOU'RE DOING
        self.kwargTable.blockSignals(True)
        if kwarg == 'format':
            value = text
        elif kwarg == 'header':
            if not text or text.lower() == 'none':
                value = None
            else:
                try:
                    value = int(text)
                except ValueError:
                    self.feedback.setText('Header row must be declared as an integer less than 9 or left undefined.')
                    self.kwargTable.setItem(row, column, QTableWidgetItem(str(self.current_kwargs[path][kwarg])))
                    self.kwargTable.blockSignals(False)
        elif kwarg == 'index_col':
            try:
                value = int(text)
            except ValueError:
                self.feedback.setText('Index column must be identified as an integer.')
                self.kwargTable.setItem(row, column, QTableWidgetItem(str(self.current_kwargs[path][kwarg])))
                self.kwargTable.blockSignals(False)
                return
        elif kwarg == 'skiprows':
            if text.lower() == 'none':
                value = []
            else:
                value = []
                for i in text:
                    if i.isdigit() and int(i) not in value:
                        value.append(int(i))
                    elif i in ', []':  # ignore commas, spaces, and brackets
                        continue
                    else:
                        self.feedback.setText('Only list of integers from 0-9 or "None" allowed.')
                        self.kwargTable.setItem(row, column, QTableWidgetItem(str(self.current_kwargs[path][kwarg])))
                        self.kwargTable.blockSignals(False)
                        return
                value = sorted(value)
            if not value: value = None

        self.feedback.setText('')
        self.kwargTable.setItem(row, column, QTableWidgetItem(str(value)))
        self.kwargTable.blockSignals(False)
        self.current_kwargs[path][kwarg] = value
        self.preview_df()

    def preview_df(self):
        GT = self.parent
        selection = self.kwargTable.selectedIndexes()
        if selection:
            rows = sorted(index.row() for index in selection)
            if all(x==rows[0] for x in rows):  # can only preview one row at a time.
                # Populate preview table with preview of selected
                row = selection[0].row()
                file = self.kwargTable.item(row, 0).text()
                path = GT.path_dict[file]
                shown_df = GT.df_preview[path]
                self.model = PandasModel(shown_df)
                self.proxy = QSortFilterProxyModel()
                self.proxy.setSourceModel(self.model)
                self.previewTable.setModel(self.proxy)
                self.previewTable.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeToContents)

                # Highlight selected rows/columns according to parse_kwargs
                header = self.current_kwargs[path]['header']
                index_col = self.current_kwargs[path]['index_col']
                skiprows = self.current_kwargs[path]['skiprows']

#                if skiprows == 'None': skiprows = None

                if index_col is not None:
                    for r in range(len(shown_df.index)):
                        self.model.setData(self.model.index(r,int(index_col)), QBrush(QColor.fromRgb(255, 170, 0)), Qt.BackgroundRole)
                if skiprows is not None:
                    for r in skiprows:
                        for c in range(len(shown_df.columns)):
                            self.model.setData(self.model.index(r,c), QBrush(Qt.darkGray), Qt.BackgroundRole)
                if header is not None:
                    for r in range(int(header)):
                        for c in range(len(shown_df.columns)):
                            self.model.setData(self.model.index(r,c), QBrush(Qt.darkGray), Qt.BackgroundRole)
                    for c in range(len(shown_df.columns)):
                        self.model.setData(self.model.index(int(header),c), QBrush(QColor.fromRgb(0, 170, 255)), Qt.BackgroundRole)
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

        # Close dialog from escape key.
        if event.key() == Qt.Key_Escape:
            self.close()

    def apply_kwargs(self):
        GT = self.parent
        DM = GT.parent
        AB = DM.parent
        # read current kwargs into AB.path_kwargs
        for file in self.group_files:
            path = GT.path_dict[file]
            if self.current_kwargs[path]['skiprows']:
                self.current_kwargs[path]['skiprows'] = [i for i in self.current_kwargs[path]['skiprows'] if i > self.current_kwargs[path]['header']]
            for kwarg in ('format', 'header', 'index_col', 'skiprows'):
                AB.path_kwargs[path][kwarg] = self.current_kwargs[path][kwarg]


class Configure_Tab(QWidget):

    def __init__(self, parent):
        super().__init__()
        self.parent = parent
        DM = self.parent
        AB = DM.parent
        buttonBox = QGridLayout()
        tableBox = QVBoxLayout(spacing=0)
        grid = QHBoxLayout()

        self.selectGroup = QComboBox()
        self.selectGroup.addItems(AB.groups.keys())
        self.selectGroup.currentIndexChanged.connect(self.display_header_info)
        buttonBox.addWidget(self.selectGroup, 0, 0, 1, 2)

        self.export = QPushButton('Export DataFrame')
        self.export.clicked.connect(self.export_data)
        buttonBox.addWidget(self.export, 1, 0, 1, 2)

        self.settings = QPushButton('Unit Settings')
        self.settings.clicked.connect(self.open_settings)
        buttonBox.addWidget(self.settings, 2, 0, 1, 2)

        self.reparse = QPushButton('Reparse Units')
        self.reparse.clicked.connect(self.reparse_units)
        buttonBox.addWidget(self.reparse, 3, 0, 1, 2)

        self.hideUnused = QCheckBox('Hide Unused Headers')
        self.hideUnused.setChecked(True)
        self.hideUnused.stateChanged.connect(self.display_header_info)
        buttonBox.addWidget(self.hideUnused, 4, 0, 1, 2)

        self.summary = QLabel()
        buttonBox.addWidget(self.summary, 5, 0, 1, 2)

        self.headerTable = QTableWidget()
        self.headerTable.setRowCount(6)
        self.headerTable.horizontalHeader().sectionResized.connect(self.sync_col_width)
        self.headerTable.horizontalHeader().setFixedHeight(23)
        self.headerTable.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.headerTable.setVerticalHeaderLabels(['Keep','Scale','Original Header','Alias','Unit Type','Unit'])
        self.headerTable.verticalHeader().setFixedWidth(146)
        self.headerTable.verticalHeader().setDefaultSectionSize(23)
        self.headerTable.verticalHeader().setSectionResizeMode(QHeaderView.Fixed)
        self.headerTable.setFixedHeight(163)
        tableBox.addWidget(self.headerTable)

        self.dfTable = QTableView()
        self.dfTable.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.dfTable.horizontalHeader().hide()
        self.dfTable.horizontalScrollBar().valueChanged.connect(self.sync_scroll)
        self.dfTable.verticalHeader().setDefaultSectionSize(self.dfTable.verticalHeader().minimumSectionSize())
        self.dfTable.verticalHeader().setSectionResizeMode(QHeaderView.Fixed)
        self.dfTable.verticalHeader().setFixedWidth(146)
        tableBox.addWidget(self.dfTable)

        grid.addLayout(buttonBox)
        grid.addLayout(tableBox)
        self.setLayout(grid)

        if self.selectGroup.currentText():
            self.display_header_info()
            self.parent.modified = False

    def reparse_units(self):
        DM = self.parent
        group_name = self.selectGroup.currentText()
        DM.groups_tab.parse_group_units([group_name], update=True)

    def export_data(self):
        """Generate an Excel file for selected group, with only kept columns and aliases with units in square brackets."""
        DM = self.parent
        AB = DM.parent

        group_name = self.selectGroup.currentText()
        if group_name:
            savepath = str(QFileDialog.getExistingDirectory(self, "Save DataFrame as CSV"))
            if savepath:
                AB.save_dir = savepath  # store saving directory
                group = DM.groups[group_name]
                aliases = {}
                for header in group.series:
                    if group.series[header].keep:
                        alias = group.series[header].alias
                        unit = group.series[header].unit
                        if not alias:
                            alias = re.sub('\[{}\]'.format(unit), '', header).strip()
                        aliases[header] = ('{} [{}]'.format(alias, unit))
                df = group.data.loc[:, list(aliases.keys())]
                df.rename(columns=aliases, inplace=True)

                filename = savepath + '/' + group_name + '.csv'
                DM.feedback('Exporting DataFrame to {}... '.format(savepath))
                DM.messageLog.repaint()
                try:
                    with open(filename, 'w') as f:
                        df.to_csv(f, encoding='utf-8-sig')
                    DM.feedback('Done', mode='append')
                except PermissionError:
                    DM.feedback('Failed', mode='append')
                    DM.feedback('Permission denied. File {} is already open or is read-only.'.format(group_name + '.csv'))

    def sync_scroll(self, idx):
        self.headerTable.horizontalScrollBar().setValue(idx)

    def sync_col_width(self, col, old_size, new_size):
        self.dfTable.horizontalHeader().resizeSection(col, new_size)

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
        return df.shape, start, end, totalspan, timeinterval

    def populate_headerTable(self, group):
        DM = self.parent
        AB = DM.parent
        i = 0
        for header in group.series:
            keep = group.series[header].keep
            if self.hideUnused.isChecked():
                if not keep: continue
            alias = group.series[header].alias
            unit = group.series[header].unit
            unit_type = group.series[header].unit_type

            keep_check = QCheckBox()
            keep_check.setChecked(keep)
            keep_check.setProperty("col", i)
            keep_check.stateChanged.connect(self.update_keep)
            _widget = QWidget()
            _layout = QHBoxLayout(_widget)
            _layout.addWidget(keep_check)
            _layout.setAlignment(Qt.AlignCenter)
            _layout.setContentsMargins(0,0,0,0)
            self.headerTable.setCellWidget(0, i, _widget)

            self.headerTable.setItem(1, i, QTableWidgetItem(str(group.series[header].scale)))

            item = QTableWidgetItem(header)
            item.setFlags(Qt.ItemIsSelectable)
            self.headerTable.setItem(2, i, item)

            self.headerTable.setItem(3, i, QTableWidgetItem(alias))

            type_combo = QComboBox()
            if AB.default_type: type_combo.addItem(AB.default_type)
            type_combo.addItem(None)
            type_combo.addItems(list(AB.user_units.keys()))
            type_combo.addItems(list(AB.unit_dict.keys()))
            type_combo.setCurrentText(unit_type)
            type_combo.setProperty("col", i)
            type_combo.currentIndexChanged.connect(self.update_unit_combo)
            self.headerTable.setCellWidget(4, i, type_combo)

            unit_combo = QComboBox()
            if unit_type is not None:
                if unit_type in AB.user_units:
                    unit_combo.addItems(list(AB.user_units[unit_type]))
                elif unit_type in AB.unit_dict:
                    unit_combo.addItems(list(AB.unit_dict[unit_type]))
                else:
                    if AB.default_unit: unit_combo.addItem(AB.default_unit)
            else:
                if AB.default_unit: unit_combo.addItem(AB.default_unit)

            unit_combo.setCurrentText(unit)
            unit_combo.setProperty("col", i)
            unit_combo.currentIndexChanged.connect(self.update_series_unit)
            self.headerTable.setCellWidget(5, i, unit_combo)
            i += 1

    def populate_dfTable(self, group, df):
        shownRows = 20
        if len(df.index) > shownRows:
            upper_df = df.head(shownRows//2)
            lower_df = df.tail(shownRows//2)
            if self.hideUnused.isChecked():
                upper_df = upper_df.loc[:, [header for header in group.series if group.series[header].keep]]
                lower_df = lower_df.loc[:, [header for header in group.series if group.series[header].keep]]

            ellipses = pd.DataFrame(['...']*len(upper_df.columns),
                                    index=upper_df.columns,
                                    columns=['...']).T
            shown_df = upper_df.append(ellipses).append(lower_df)
        else:
            if self.hideUnused.isChecked():
                shown_df = df.loc[:, [header for header in group.series if group.series[header].keep]]
            else:
                shown_df = df
        shown_df.index = [ts.strftime('%Y-%m-%d  %H:%M:%S') if hasattr(ts, 'strftime') else '...' for ts in shown_df.index]

        self.model = PandasModel(shown_df)
        self.proxy = QSortFilterProxyModel()
        self.proxy.setSourceModel(self.model)
        self.dfTable.setModel(self.proxy)
        self.headerTable.setColumnCount(len(shown_df.columns))

    def summarize_data(self, df):
        shape, start, end, total_span, sampling_rate = self.df_span_info(df)
        self.summary.setText("""
Full Shape:
    {} rows
    {} columns

Data Start:
    {}

Data End:
    {}

Total Span:
    {} days
    {} hours
    {} minutes

Sampling Rate:
    {}s
""".format(*shape, start.strftime('%Y-%m-%d  %H:%M:%S'), end.strftime('%Y-%m-%d  %H:%M:%S'), *total_span, sampling_rate))

    def display_header_info(self):
        try:
            self.headerTable.cellChanged.disconnect(self.update_alias_scale)
        except TypeError:
            pass
        DM = self.parent
        group_name = self.selectGroup.currentText()
        if group_name:
            group = DM.groups[group_name]
            df = group.data
            self.summarize_data(df)
            self.populate_dfTable(group, df)
            self.headerTable.setRowCount(6)
            self.headerTable.setVerticalHeaderLabels(['Keep','Scale','Original Header','Alias','Unit Type','Unit'])
            self.populate_headerTable(group)
        else:
            self.headerTable.clear()
            self.headerTable.setRowCount(0)
            self.headerTable.setColumnCount(0)
            if hasattr(self, 'proxy'): self.proxy.deleteLater()
        self.headerTable.cellChanged.connect(self.update_alias_scale)

    def update_alias_scale(self, row, column):
        """Updates the alias and scaling factor of series when one of those two fields is edited"""
        DM = self.parent
        group = DM.groups[self.selectGroup.currentText()]
        header = self.headerTable.item(2, column).text()
        if row == 3:
            alias = self.headerTable.item(3, column).text().strip()  # remove any trailing/leading whitespace

            def remove_key_by_value(dictionary, value):
                for key in dictionary:
                    if dictionary[key] == value:
                        del dictionary[key]
                        break

            if alias and alias != group.series[header].alias:
                if alias in group.alias_dict:
                    DM.feedback('Alias "{}" is already in use. Please choose a different alias.'.format(alias))
                    self.headerTable.blockSignals(True)
                    self.headerTable.setItem(3, column, QTableWidgetItem(group.series[header].alias))
                    self.headerTable.blockSignals(False)
                    return
                if alias in group.data.columns:
                    DM.feedback('Alias "{}" is the name of an original header. Please choose a different alias.'.format(alias))
                    self.headerTable.blockSignals(True)
                    self.headerTable.setItem(3, column, QTableWidgetItem(group.series[header].alias))
                    self.headerTable.blockSignals(False)
                    return
                group.series[header].alias = alias
                remove_key_by_value(group.alias_dict, header)
                group.alias_dict[alias] = header
            else:
                group.series[header].alias = ''
                remove_key_by_value(group.alias_dict, header)
            DM.modified = True
        elif row == 1:
            scale = self.headerTable.item(1, column).text()
            try:
                scale = float(scale)
                if scale == 0: raise ValueError
                group.series[header].scale = scale
                DM.modified = True
            except ValueError:
                DM.feedback('"{}" is not a valid scaling factor. Only nonzero real numbers permitted.'.format(scale))
            self.headerTable.blockSignals(True)  # prevents infinite recursion when setItem would call this function again
            self.headerTable.setItem(1, column, QTableWidgetItem(str(group.series[header].scale)))
            self.headerTable.blockSignals(False)

    def update_unit_combo(self):
        DM = self.parent
        AB = DM.parent
        group = DM.groups[self.selectGroup.currentText()]
        type_combo = QObject.sender(self)
        col = type_combo.property("col")
        unit_type = type_combo.currentText()
        header = self.headerTable.item(2, col).text()
        group.series[header].unit_type = unit_type
        unit_combo = self.headerTable.cellWidget(5, col)
        unit_combo.clear()
        if unit_type in AB.user_units:
            unit_combo.addItems(list(AB.user_units[unit_type]))
        elif unit_type in AB.unit_dict:
            unit_combo.addItems(list(AB.unit_dict[unit_type]))
        elif AB.default_unit:
            unit_combo.addItem(AB.default_unit)
        DM.modified = True

    def update_series_unit(self):
        DM = self.parent
        group = DM.groups[self.selectGroup.currentText()]
        unit_combo = QObject.sender(self)
        col = unit_combo.property("col")
        unit = unit_combo.currentText()
        header = self.headerTable.item(2, col).text()
        group.series[header].unit = unit
        DM.modified = True

    def update_keep(self):
        DM = self.parent
        group = DM.groups[self.selectGroup.currentText()]
        keep_check = QObject.sender(self)
        header_columns = [keep_check.property("col")]
        header_columns.extend([item.column() for item in self.headerTable.selectedItems()])
        for c in set(header_columns):
            header = self.headerTable.item(2, c).text()
            group.series[header].keep = keep_check.isChecked()
        self.display_header_info()
        DM.modified = True

    def open_settings(self):
        self.settings_dialog = Unit_Settings(self)
        self.settings_dialog.setModal(True)
        self.settings_dialog.show()


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
        self.setWindowTitle('Unit Settings')
        self.setWindowIcon(QIcon('rc/satellite.png'))
#        self.setFixedSize(200,333)
        CT = self.parent
        DM = CT.parent
        AB = DM.parent

        vbox = QVBoxLayout()

        form = QFormLayout()
        self.autoParseCheck = QCheckBox('Automatically parse units from headers')
        self.autoParseCheck.setChecked(AB.auto_parse)
        self.autoParseCheck.stateChanged.connect(self.toggle_auto_parse)
        form.addRow(self.autoParseCheck)

        self.baseType = QComboBox()
        self.baseType.addItems(list(AB.unit_dict.keys()))
        self.baseType.currentIndexChanged.connect(self.update_pht)
        form.addRow('Base Unit Types', self.baseType)

        self.newType = QLineEdit()
        baseType = self.baseType.currentText()
        self.newType.setPlaceholderText('New '+baseType+' Type')
        self.newType.editingFinished.connect(self.add_user_type)
        form.addRow(self.newType)
        self.userUnits = QComboBox()
        entries = []
        for userType in AB.user_units:
            for baseType in AB.unit_dict:
                if AB.user_units[userType] == AB.unit_dict[baseType]:
                    entries.append('{} ({})'.format(userType, baseType))
                    break
        self.userUnits.addItems(entries)
        self.delete = QPushButton('Delete User Type')
        self.delete.clicked.connect(self.delete_user_type)
        form.addRow(self.delete, self.userUnits)
        self.defaultType = QLineEdit()
        self.defaultType.setPlaceholderText('None')
        if AB.default_type: self.defaultType.setText(AB.default_type)
        form.addRow('Set Default Type', self.defaultType)
        self.defaultUnit = QLineEdit()
        self.defaultUnit.setPlaceholderText('None')
        if AB.default_unit: self.defaultUnit.setText(AB.default_unit)
        form.addRow('Set Default Unit', self.defaultUnit)
        vbox.addLayout(form)

        self.clarified = QTableWidget()
        self.clarified.setColumnCount(2)
        self.clarified.setHorizontalHeaderLabels(['Parsed', 'Interpreted'])
        self.clarified.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.clarified.verticalHeader().hide()
        self.clarified.cellChanged.connect(self.reset_background)
        self.populate_clarified()
        vbox.addWidget(self.clarified)

        hbox = QHBoxLayout()
        self.addRow = QPushButton('Add')
        self.addRow.clicked.connect(self.add_clarified_row)
        self.addRow.setDefault(True)
        hbox.addWidget(self.addRow)
        self.deleteRow = QPushButton('Delete')
        self.deleteRow.clicked.connect(self.delete_clarified_row)
        hbox.addWidget(self.deleteRow )
        vbox.addLayout(hbox)

        self.setLayout(vbox)

    def toggle_auto_parse(self):
        CT = self.parent
        DM = CT.parent
        AB = DM.parent
        AB.auto_parse = self.autoParseCheck.isChecked()

    def update_pht(self):
        baseType = self.baseType.currentText()
        self.newType.setPlaceholderText('New '+baseType+' Type')

    def add_user_type(self):
        CT = self.parent
        DM = CT.parent
        AB = DM.parent
        newType = self.newType.text().strip()
        baseType = self.baseType.currentText()
        all_units = {**AB.unit_dict, **AB.user_units}
        if newType and newType not in all_units:
            AB.user_units.update({newType: AB.unit_dict[baseType]})
            entry = '{} ({})'.format(newType, baseType)
            self.userUnits.addItem(entry)
            self.userUnits.setCurrentText(entry)

    def delete_user_type(self):
        CT = self.parent
        DM = CT.parent
        AB = DM.parent
        entry = self.userUnits.currentText()
        userType = entry[:entry.rindex('(')-1]
        del AB.user_units[userType]
        self.userUnits.removeItem(self.userUnits.currentIndex())

    def populate_clarified(self):
        CT = self.parent
        DM = CT.parent
        AB = DM.parent
        self.clarified.setRowCount(len(AB.unit_clarify))
        for r, key in enumerate(AB.unit_clarify):
            self.clarified.setItem(r, 0, QTableWidgetItem(key))
            key_clar = QComboBox()
            key_clar.addItems([x for unit_list in AB.unit_dict.values() for x in unit_list])
            key_clar.setCurrentText(AB.unit_clarify[key])
            self.clarified.setCellWidget(r, 1, key_clar)

    def add_clarified_row(self):
        CT = self.parent
        DM = CT.parent
        AB = DM.parent
        self.clarified.setRowCount(self.clarified.rowCount()+1)
        key_clar = QComboBox()
        key_clar.addItems([x for unit_list in AB.unit_dict.values() for x in unit_list])
        self.clarified.setCellWidget(self.clarified.rowCount()-1, 1, key_clar)

    def delete_clarified_row(self):
        rows_to_delete = set([item.row() for item in self.clarified.selectedIndexes()])
        for r in sorted(rows_to_delete, reverse=True):
            self.clarified.removeRow(r)

    def reset_background(self, row, column):
        CT = self.parent
        DM = CT.parent
        AB = DM.parent
        if AB.current_rcs == AB.dark_rcs:
            bg = QColor.fromRgb(35, 38, 41)
        else:
            bg = QColor.fromRgb(255, 255, 255)
        self.clarified.item(row, column).setBackground(QBrush(bg))

    def closeEvent(self, event):
        CT = self.parent
        DM = CT.parent
        AB = DM.parent
        keys, values = [], []
        ok = True
        for r in range(self.clarified.rowCount()):
            try:
                key = self.clarified.item(r, 0).text()
                if key.strip():
                    if key not in keys:
                        keys.append(key)
                        values.append(self.clarified.cellWidget(r, 1).currentText())
                    else:
                        self.clarified.blockSignals(True)
                        # have it just select the duplicates instead of highlighting red?
                        self.clarified.item(r, 0).setBackground(QBrush(QColor.fromRgb(255, 50, 50)))
                        self.clarified.blockSignals(False)
                        ok = False
            except AttributeError:
                continue
        if ok:
            AB.unit_clarify = dict(zip(keys,values))
            AB.default_type = self.defaultType.text().strip()
            AB.default_unit = self.defaultUnit.text().strip()
            AB.figure_settings.update_unit_table()

# some strange behavior with this code. Leave out if not necessary. User now needs to explicitly click 'reparse units'.
#            group_name = CT.selectGroup.currentText()
#            if group_name:
#                group = DM.groups[group_name]
#                DM.configure_tab.populate_headerTable(group)

            event.accept()
        else:
            event.ignore()

    def keyPressEvent(self, event):
        """Enables dialog closure by escape key."""
        if event.key() == Qt.Key_Escape:
            self.close()


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
        for spine in ax.spines.values():
            spine.set_visible(False)

    def plot(self, skeleton=False):
        """Main plotting function. Auto-generates parasitic axes in specified unit order."""
        sp = self
        AB = self.parent
        CF = AB.control_frame
        FS = AB.figure_settings
        for ax in sp.axes[1:]: ax.remove()  # remove parasitic axes from subplot
        sp.axes = [sp.host()]  # clear parasitic axes from sp.axes
        sp.host().clear()  # clear host axis of data

        color_index = 0
        style_dict = {}
        lines = []
        labels = []
        if sp.contents is not None:
            for group_name, aliases_units in sp.contents.items():
                group = AB.groups[group_name]
                df = group.data
                subdf = df[(df.index >= CF.start) & (df.index <= CF.end)]  # filter by start/end time
                for alias, unit in aliases_units.items():
                    try:
                        header = group.alias_dict[alias]
                    except KeyError:
                        header = alias
                    unit_type = group.series[header].unit_type
#                    print('alias: ', alias)
#                    print('unit:  ', unit)
#                    print('order: ', sp.order)

                    # Determine which axes to plot on, depending on sp.order
                    # Axes are uniquely identified by combination of unit_type and unit
                    # ie, Position [nm] != Position [km] != Altitude [km] != Altitude [nm]
                    if sp.order[0] is None:
                        sp.order[0] = (unit_type, unit)  # if no order given, default to sorted order
                    if (unit_type, unit) not in sp.order:
                        sp.order.append((unit_type, unit))  # new units go at the end of the order
                    ax_index = sp.order.index((unit_type, unit))  # get index of unit in unit order
                    while len(sp.axes)-1 < ax_index: # extend sp.axes as needed
                        par = sp.host().twinx()
                        sp.axes.append(par)
                    ax = sp.axes[ax_index]  # get axis (parasitic or host) at index of unit

                    # Manage colors and styles
                    if not skeleton:  # turning skeleton on sets up the axes correctly but doesn't plot any data. Helps efficiency in series transfer/clear
                        if sp.colorCoord:
                            if unit_type not in style_dict:  # keep track of how many series are plotted in each unit to cycle through linestyles(/markerstyles TBI)
                                style_dict[unit_type] = 0
                            style_counter = style_dict[unit_type]
                            style_dict[unit_type] = style_counter+1
                            style = FS.markers[style_counter%len(FS.markers)]
                            color = FS.color_dict[unit_type]
                            ax.yaxis.label.set_color(color)
                            ax.tick_params(axis='y', labelcolor=color)
                        else:  # set color to rotate through default colormap (otherwise colormap is done per axis, not the whole subplot)
                            color='C'+str(color_index%10)
                            color_index += 1
                            style = 'o'
                            labelcolor = AB.current_rcs['axes.labelcolor']
                            ax.yaxis.label.set_color(labelcolor)
                            ax.tick_params(axis='y', labelcolor=labelcolor)

                        # Fetch data to plot from references in sp.contents
                        s = subdf[header]
                        n = len(s.index)
                        d = FS.density.value()/100
                        thin = np.linspace(0, n-1, num=int(n*d), dtype=int)
                        s = s.iloc[thin]

                        scale = group.series[header].scale
                        s = s.map(lambda x: x*scale)

                        if FS.scatter.isChecked():
                            line, = ax.plot(s, style, color=color, markersize=FS.dotsize.value(), markeredgewidth=FS.dotsize.value(), linestyle='None')
                        else:
                            line, = ax.plot(s, color=color)
                        lines.append(line)
                        labels.append(alias)
                        # set ylabel to formal unit description
                        if unit_type is not None:
                            if unit:
                                ax.set_ylabel('{} [{}]'.format(unit_type, unit), fontsize=FS.labelSize.value())
                            else:
                                ax.set_ylabel(unit_type, fontsize=FS.labelSize.value())
                        else:
                            if unit:
                                ax.set_ylabel('[{}]'.format(unit), fontsize=FS.labelSize.value())

            offset = FS.parOffset.value()
            for i, par in enumerate(sp.axes[1:]):  # offset parasitic axes
                self.make_patch_spines_invisible(par)
                par.spines["right"].set_visible(True)
                par.spines["right"].set_position(("axes", 1+offset*(i)))

            npars = len(sp.axes[1:])
            if sp.legend and sp.contents:  # create and offset legend
                sp.host().legend(lines, labels,
                       bbox_to_anchor=(1+offset*npars, 0.5),
                       loc="center left", markerscale=10)


class Group():

    def __init__(self, df, source_files, source_paths, density=100):
        self.data = df  # maybe copy needed
        self.series = {key:Series() for key in self.data.columns}
        self.alias_dict = {}
        self.source_files = source_files
        self.source_paths = source_paths
#EG: AB.groups[name].series[header].alias

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

    def __init__(self, alias='', unit=None, unit_type=None, scale=1.0, keep=True):
        self.alias = alias
        self.unit = unit
        self.unit_type = unit_type
        self.scale = scale
        self.keep = keep

    def summarize(self):
        return 'Alias: '+str(self.alias)+'  Unit: '+str(self.unit)+'  Scale: '+str(self.scale)+'  Keep: '+str(self.keep)





### THE ACTUAL RUN COMMAND
if 'app' not in locals():
    app = QCoreApplication.instance()
if app is None:  # otherwise kernel dies
    app = QApplication(sys.argv)
X = Application_Base()#groups=groups)
app.exec_()