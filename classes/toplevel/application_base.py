# -*- coding: utf-8 -*-
"""
Created on Thu Jun 13 15:40:50 2019

@author: seery
"""
import os
import re
import copy
import json
import matplotlib.pyplot as plt
from PyQt5.QtWidgets import (QApplication, QWidget, QMainWindow,
                             QMessageBox, QDockWidget, QFileDialog,
                             QVBoxLayout, QAction)
from PyQt5.QtGui import QIcon
from PyQt5.QtCore import Qt, QTextStream, QFile

from .axes_frame import Axes_Frame
from .control_frame import Control_Frame
from .series_frame import Series_Frame
from .figure_settings import Figure_Settings
from ..manager.data_manager import Data_Manager

class Application_Base(QMainWindow):
    """Main application window."""

    def __init__(self, logger, groups={}):
        super().__init__()
        self.groups = copy.deepcopy(groups)
        self.save_dir = os.getcwd()
        self.default_ext = '.jpg'
        self.path_kwargs = {}
        self.auto_parse = True
        self.saved = True
        self.logger = logger

        f = QFile('rc/dark.qss')
        if not f.exists():
            self.logger.error('Unable to load dark stylesheet,'
                              '\"{}\" not found'.format(f.fileName()))
            self.dark_qss = ''
        else:
            f.open(QFile.ReadOnly | QFile.Text)
            ts = QTextStream(f)
            self.dark_qss = ts.readAll()
        f = QFile('rc/light.qss')
        if not f.exists():
            self.logger.error('Unable to load light stylesheet,'
                              '\"{}\" not found'.format(f.fileName()))
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
        self.docked_FS.setAllowedAreas(Qt.RightDockWidgetArea |
                                       Qt.LeftDockWidgetArea)
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
        interactiveAction.setStatusTip('Toggle Matplotlib interactive mode')
        interactiveAction.triggered.connect(self.toggle_interactive)
        viewMenu.addAction(interactiveAction)

        darkAction = QAction('Dark Mode', self)
        darkAction.setShortcut('Ctrl+B')
        darkAction.setStatusTip('Toggle dark user interface')
        darkAction.triggered.connect(self.toggle_dark_mode)
        viewMenu.addAction(darkAction)

        self.showMaximized()
        ### Adding Figure Settings dock to right side currently screws this up
        self.control_frame.setFixedHeight(self.control_frame.height())
        self.control_frame.setFixedWidth(self.control_frame.width())
        self.figure_settings.setFixedWidth(150)
        self.set_app_style(self.default_qss, self.default_rcs)
        self.control_frame.time_filter()

        ### Delete later, just for speed
#        self.open_data_manager()

    def popup(self, text, title=' ',
              informative=None, details=None,
              mode='save', icon=True):
        """Brings up a message box and returns Ok or Cancel."""
        self.prompt = QMessageBox()
        self.prompt.setWindowIcon(QIcon('rc/satellite.png'))
        self.prompt.setWindowTitle(title)
        if icon: self.prompt.setIcon(QMessageBox.Question)
        self.prompt.setText(text)
        if mode == 'save':
            self.prompt.setStandardButtons(QMessageBox.Discard |
                                           QMessageBox.Cancel |
                                           QMessageBox.Save)
            self.prompt.button(QMessageBox.Save).setText('Save && Exit')
        elif mode == 'confirm':
            self.prompt.setStandardButtons(QMessageBox.Ok |
                                           QMessageBox.Cancel)
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
            for header in groups[group].series.keys():
                if groups[group].series[header].keep:
                    alias = groups[group].series[header].alias
                    if alias:
                        aliases.append(alias)
                    else:
                        aliases.append(header)
            contents.update({group: aliases})
        return contents

    def save(self):
        """Quick-save feature.
        Saves current figure to most recent save directory
        if a file by that name already exists,
        else defers to explicit Save-As dialog.
        Accessible by Telemetry Grapher's File menu (or Ctrl+S)."""
        CF = self.control_frame
        AF = self.axes_frame
        FS = self.figure_settings
        CF.rename()
        AF.current_sps = []
        FS.density.setValue(100)
        AF.refresh_all()

        filename = self.filename + self.default_ext
        if filename in os.listdir(self.save_dir):
            plt.savefig(self.save_dir + '\\' + filename,
                        dpi=300, transparent=True, bbox_inches='tight')
#            with open(self.filename + '.pickle', 'wb') as f:
#                pl.dump(AF.fig, f)
            self.statusBar().showMessage('Saved to {}'.format(self.save_dir))
            self.saved = True
        else:
            self.save_as()

    def save_as(self):
        """Explicit Save-As feature.
        Saves current figure using PyQt5's file dialog.
        Default format is .jpg.
        Accessible by Telemetry Grapher's File menu (or Ctrl+Shift+S)."""
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
        dlg_out = dlg.getSaveFileName(self, 'Save Figure',
                                      self.save_dir + '/' + self.filename,
                                      "JPEG Image (*.jpg);;PNG Image (*.png)")
        if dlg_out[0]:
            savepath = dlg_out[0]
            # store saving directory
            self.save_dir = savepath[:savepath.rindex('/')]
            # store file extension
            self.default_ext = savepath[savepath.index('.'):]
            plt.savefig(savepath,
                        dpi=300, transparent=True, bbox_inches='tight')
#            with open(self.filename + '.pickle', 'wb') as f:
#                pkl.dump(AF.fig, f)
            self.statusBar().showMessage('Saved to {}'.format(savepath))
            self.saved = True

    def parse_unit(self, header):
        """Parses unit information from header.
        Returns characters between last instance of square brackets."""
        # matches any characters between square brackets
        regex = re.compile('\[[^\[]*?\]')
        parsed = ''
        for match in re.finditer(regex, header):  # as last match
            parsed = match.group(0)[1:-1]  # strip brackets
        return parsed

    def interpret_unit(self, unit):
        """Tries to interpret unit.
        - Run unit through self.unit_clarify dictionary.
        - Check if unit can be associated with a unit type.
        - If so, return unit, otherwise return default unit.
        - Boolean indicates whether or not the unit could be interpreted."""
        if unit:
            if unit in self.unit_clarify:
                unit = self.unit_clarify[unit]
            if self.get_unit_type(unit) != self.default_type:
                return unit, True
        return self.default_unit, False

    def get_unit_type(self, unit):
        """Returns unit type of given unit.
        Priority is first given to user-defined units, then base unit types.
        If unit is not recognized in either dictionary,
        then the default unit type is returned."""
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
        """Called when application is about to exit.
        If close event accepted,
        - hide any floating dockwidgets
        - close all created figures"""
        self.saved = True  # CONVENIENCE OVERRIDE, DELETE LATER #???

        if not self.saved:
            result = self.popup('Figure has not been saved. Exit anyway?',
                                title='Exiting Application')
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
        self.logger.error('too many chairs in here.')
        print(self.control_frame.size())
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
        Accessible through Telemetry Grapher's Tools menu (or Ctrl+D)."""
        self.statusBar().showMessage('Opening Data Manager')
        self.manager = Data_Manager(self)
        self.manager.setModal(True)
        self.manager.show()

    def import_template(self):
        pass

    def toggle_docks(self):
        """Toggles visibility of dock widgets.
        Accessible through Telemetry Grapher's View menu (or Ctrl+H)."""
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