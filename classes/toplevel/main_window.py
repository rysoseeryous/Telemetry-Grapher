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
                             QMessageBox, QFileDialog, QVBoxLayout, QAction)
from PyQt5.QtGui import QIcon
from PyQt5.QtCore import Qt, QTextStream, QFile

from .axes_frame import AxesFrame
from .control_panel import ControlPanel
from .series_display import SeriesDisplay
from .figure_settings import FigureSettings
from .mpl_navigation_toolbar import NavToolbar
from ..manager.data_manager import DataManager
from ..internal.contents_dict import ContentsDict

class UI(QMainWindow):
    """Main application window."""

    def __init__(self, logger, groups={}):
        super().__init__()
        self.groups = copy.deepcopy(groups)
        self.fig_dir = os.getcwd()
        self.df_dir = os.getcwd()
        self.path_kwargs = {}
        self.auto_parse = True
        self.saved = True
        self.first_save = True
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
        self.statusBar().showMessage('No subplot selected')

        self.figure_settings = FigureSettings(self, "Figure Settings")
        self.figure_settings.setAllowedAreas(Qt.RightDockWidgetArea |
                                             Qt.LeftDockWidgetArea)


        self.control_panel = ControlPanel(self, "Control Panel")
        self.axes_frame = AxesFrame(self)
        # this may later turn into a tab widget
        self.master_frame = QWidget()
        self.master_frame.setLayout(QVBoxLayout())
        self.master_frame.layout().addWidget(self.axes_frame)
        self.setCentralWidget(self.master_frame)

        self.series_display = SeriesDisplay(self, "Series Display")
        self.addDockWidget(Qt.LeftDockWidgetArea, self.series_display)
        self.addDockWidget(Qt.LeftDockWidgetArea, self.control_panel)
        self.addDockWidget(Qt.RightDockWidgetArea, self.figure_settings)
        self.figure_settings.hide()
        self.figure_settings.connect_widgets(container=self.axes_frame)

        #??? Navigation Toolbar
#        self.nt = NavToolbar(self.axes_frame, self)
#        self.addToolBar(Qt.BottomToolBarArea, self.nt)

#        self.control_panel.time_filter()
        self.filename = self.axes_frame.fig._suptitle.get_text()
        self.resizeDocks([self.series_display], [420], Qt.Horizontal)

        file_menu = self.menuBar().addMenu('File')
        new_action = QAction('New', self)
        new_action.setShortcut('Ctrl+N')
        new_action.setStatusTip('Open a blank figure')
        new_action.triggered.connect(self.new)
        file_menu.addAction(new_action)

        open_action = QAction('Open', self)
        open_action.setShortcut('Ctrl+O')
        open_action.setStatusTip('Open existing figure')
        open_action.triggered.connect(self.open_fig)
        file_menu.addAction(open_action)

        save_action = QAction('Save', self)
        save_action.setShortcut('Ctrl+S')
        save_action.triggered.connect(self.save)
        file_menu.addAction(save_action)

        save_as_action = QAction('Save As', self)
        save_as_action.setShortcut('Ctrl+Shift+S')
        save_as_action.triggered.connect(self.save_as)
        file_menu.addAction(save_as_action)

        exit_action = QAction('Exit', self)
        exit_action.setShortcut('Ctrl+Q')
        exit_action.setStatusTip('Exit application')
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)

        edit_menu = self.menuBar().addMenu('Edit')
        undo_action = QAction('Undo', self)
        undo_action.setShortcut('Ctrl+Z')
        undo_action.triggered.connect(self.undo)
        edit_menu.addAction(undo_action)

        redo_action = QAction('Redo', self)
        redo_action.setShortcut('Ctrl+Y')
        redo_action.triggered.connect(self.redo)
        edit_menu.addAction(redo_action)

        refresh_action = QAction('Refresh Figure', self)
        refresh_action.setShortcut('Ctrl+R')
        refresh_action.triggered.connect(self.axes_frame.refresh_all)
        edit_menu.addAction(refresh_action)

        tools_menu = self.menuBar().addMenu('Tools')
        data_action = QAction('Manage Data', self)
        data_action.setShortcut('Ctrl+D')
        data_action.triggered.connect(self.open_data_manager)
        tools_menu.addAction(data_action)

        template_action = QAction('Import Template', self)
        template_action.setShortcut('Ctrl+T')
        template_action.triggered.connect(self.import_template)
        tools_menu.addAction(template_action)

        view_menu = self.menuBar().addMenu('View')
        docks_action = QAction('Show/Hide Docks', self)
        docks_action.setShortcut('Ctrl+H')
        docks_action.triggered.connect(self.toggle_docks)
        view_menu.addAction(docks_action)

        interactive_action = QAction('MPL Interactive Mode', self)
        interactive_action.setShortcut('Ctrl+M')
        interactive_action.setStatusTip('Toggle Matplotlib interactive mode')
        interactive_action.triggered.connect(self.toggle_interactive)
        view_menu.addAction(interactive_action)

        dark_action = QAction('Dark Mode', self)
        dark_action.setShortcut('Ctrl+B')
        dark_action.setStatusTip('Toggle dark user interface')
        dark_action.triggered.connect(self.toggle_dark_mode)
        view_menu.addAction(dark_action)

        self.showMaximized()
        ### Adding Figure Settings dock to right side currently screws this up
        self.control_panel.setFixedHeight(self.control_panel.height())
        self.control_panel.setFixedWidth(self.control_panel.width())
        self.figure_settings.setFixedWidth(150)
        self.set_app_style(self.default_qss, self.default_rcs)
        self.control_panel.time_filter()

        ### Delete later, just for speed
#        self.open_data_manager()

    def popup(self, text, title=' ',
              informative=None, details=None,
              mode='save'):
        """Brings up a message box and returns Ok or Cancel."""
        prompt = QMessageBox()
        prompt.setWindowIcon(QIcon('rc/satellite.png'))
        prompt.setWindowTitle(title)
        prompt.setText(text)
        if mode == 'save':
            prompt.setIcon(QMessageBox.Question)
            prompt.setStandardButtons(QMessageBox.Discard |
                                      QMessageBox.Cancel |
                                      QMessageBox.Save)
            prompt.button(QMessageBox.Save).setText('Save && Exit')
        elif mode == 'confirm':
            prompt.setIcon(QMessageBox.Warning)
            prompt.setStandardButtons(QMessageBox.Ok |
                                      QMessageBox.Cancel)
        elif mode == 'alert':
            prompt.setIcon(QMessageBox.Information)
            prompt.setStandardButtons(QMessageBox.Ok)
        prompt.setInformativeText(informative)
        prompt.setDetailedText(details)
        prompt.show()
        self.dlg = prompt
        return self.dlg.exec_()

    def groups_to_contents(self, groups):
        """Converts groups database into contents format. See ReadMe."""
        contents = ContentsDict()
        for group in groups:
            aliases = []
            for s in groups[group].kept():
                if s.alias:
                    aliases.append(s.alias)
                else:
                    aliases.append(s.header)
            contents.update({group: aliases})
        return contents

    def prep_fig(self):
        cp = self.control_panel
        af = self.axes_frame
        fs = self.figure_settings
        cp.rename()
        af.current_sps = []
        fs.density.setValue(100)
        af.refresh_all()

    def save(self):
        """Quick-save feature.
        Saves current figure to most recent save directory
        if a file by that name already exists,
        else defers to explicit Save-As dialog.
        Accessible by Telemetry Grapher's File menu (or Ctrl+S)."""

        filename = self.filename + '.jpg'
        if self.first_save or filename not in os.listdir(self.fig_dir):
            self.save_as()
        else:
            self.prep_fig()
            plt.savefig(self.fig_dir + '\\' + filename,
                        dpi=300, transparent=True, bbox_inches='tight')
#            with open(self.filename + '.pickle', 'wb') as f:
#                pl.dump(af.fig, f)
            self.statusBar().showMessage('Saved to {}'.format(self.fig_dir))
            self.saved = True

    def save_as(self):
        """Explicit Save-As feature.
        Saves current figure using PyQt5's file dialog.
        Default format is .jpg.
        Accessible by Telemetry Grapher's File menu (or Ctrl+Shift+S)."""
        self.prep_fig()

        dlg = QFileDialog()
        dlg.setFileMode(QFileDialog.AnyFile)
        dlg.setViewMode(QFileDialog.Detail)
        dlg_out = dlg.getSaveFileName(self, 'Save Figure',
                                      self.fig_dir + '/' + self.filename,
                                      'JPEG Image (*.jpg)')#;;PNG Image (*.png)
        if dlg_out[0]:
            savepath = dlg_out[0]
            # store saving directory
            self.fig_dir = os.path.dirname(savepath)
            plt.savefig(savepath,
                        dpi=300, transparent=True, bbox_inches='tight')
#            with open(self.filename + '.pickle', 'wb') as f:
#                pkl.dump(af.fig, f)
            self.statusBar().showMessage('Saved to {}'.format(savepath))
            self.saved = True
            self.first_save = False

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
        for dock in [self.control_panel,
                     self.series_display,
                     self.figure_settings]:
            if dock.isFloating(): dock.close()
        plt.close('all')
        self.control_panel.title_edit.editingFinished.disconnect()
        event.accept()

    def new(self):
        self.logger.error('too many chairs in here.')
        print(self.control_panel.size())
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
#        af = self.axes_frame
#        dlg_output = QFileDialog.getOpenFileName(self,
#                                                  "Open Saved Figure",
#                                                  self.fig_dir,
#                                                  "(*.pickle)")
#        if dlg_output[0]:
#            fig = pkl.load(open(dlg_output[0], 'rb'))
#            _ = plt.figure()
#            manager = _.canvas.manager
#            manager.canvas.figure = fig
#            af.fig.set_canvas(manager.canvas)
#            print(fig)
#            for ax in fig.axes:
#                print(ax)
#                print(ax.lines)
#                print(ax.get_legend())
#                h, l = ax.get_legend_handles_labels()
#                print(h)
#                print(l)
#            af.fig.show()
#            af.draw()

    def undo(self):
        pass

    def redo(self):
        pass

    def open_data_manager(self):
        """Opens Data Manager dialog.
        Accessible through Telemetry Grapher's Tools menu (or Ctrl+D)."""
        self.statusBar().showMessage('Opening Data Manager')
        self.dlg = DataManager(self)
        self.dlg.setWindowFlags(Qt.Window)
        self.dlg.setModal(True)
        self.dlg.show()

    def import_template(self):
        pass

    def toggle_docks(self):
        """Toggles visibility of dock widgets.
        Accessible through Telemetry Grapher's View menu (or Ctrl+H)."""
        docks = [self.control_panel, self.series_display, self.figure_settings]
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
