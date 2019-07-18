# -*- coding: utf-8 -*-
"""main_window.py - Contains UI class definition."""

# This file is part of Telemetry-Grapher.

# Telemetry-Grapher is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.

# Telemetry-Grapher is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY
# without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.

# You should have received a copy of the GNU General Public License
# along with Telemetry-Grapher. If not, see < https: // www.gnu.org/licenses/>.

__author__ = "Ryan Seery"
__copyright__ = 'Copyright 2019 Max-Planck-Institute for Solar System Research'
__license__ = "GNU General Public License"

import os
import re
import copy
import json
import matplotlib.pyplot as plt

from PyQt5.QtWidgets import (QApplication, QWidget, QMainWindow,
                             QMessageBox, QFileDialog, QVBoxLayout)
from PyQt5.QtGui import QIcon
from PyQt5.QtCore import Qt, QTextStream, QFile

from .axes_frame import AxesFrame
from .series_display import SeriesDisplay
from .figure_settings import FigureSettings
from .menus import FileMenu, EditMenu, ToolsMenu, ViewMenu
from .subplot_toolbar import SubplotToolbar
from .legend_toolbar import LegendToolbar
from .axes_toolbar import AxesToolbar
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
        self.start_mode = startup['start_mode']
        self.highlight = startup['highlight']
        self.af_init = startup['af_init']
        self.filename = self.af_init['title']

        if self.start_mode == 'light':
            self.current_qss = self.light_qss
            self.current_rcs = self.light_rcs
            self.current_icon_path = 'rc/entypo/light'
        elif self.start_mode == 'dark':
            self.current_qss = self.dark_qss
            self.current_rcs = self.dark_rcs
            self.current_icon_path = 'rc/entypo/dark'
        self.mode = self.start_mode

        self.setWindowTitle('Telemetry Plot Configurator')
        self.setWindowIcon(QIcon('rc/satellite.png'))
        self.statusBar().showMessage('No subplot selected')

        self.axes_frame = AxesFrame(self)
        # this may later turn into a tab widget
        self.master_frame = QWidget()
        self.master_frame.setLayout(QVBoxLayout())
        self.master_frame.layout().addWidget(self.axes_frame)
        self.setCentralWidget(self.master_frame)

        self.series_display = SeriesDisplay(self, "Series Display")
        self.figure_settings = FigureSettings(self, "Figure Settings")
        self.figure_settings.setAllowedAreas(Qt.RightDockWidgetArea |
                                             Qt.LeftDockWidgetArea)
        self.addDockWidget(Qt.LeftDockWidgetArea, self.series_display)
        self.addDockWidget(Qt.RightDockWidgetArea, self.figure_settings)
        self.resizeDocks([self.series_display, self.figure_settings],
                         [420, 165],
                         Qt.Horizontal)

        self.file_menu = FileMenu('File', self)
        self.edit_menu = EditMenu('Edit', self)
        self.tools_menu = ToolsMenu('Tools', self)
        self.view_menu = ViewMenu('View', self)
        self.menuBar().addMenu(self.file_menu)
        self.menuBar().addMenu(self.edit_menu)
        self.menuBar().addMenu(self.tools_menu)
        self.menuBar().addMenu(self.view_menu)

        self.subplot_toolbar = SubplotToolbar('Subplot Toolbar', self)
        self.legend_toolbar = LegendToolbar('Legend Toolbar', self)
        self.axes_toolbar = AxesToolbar('Axes Toolbar', self)
        self.addToolBar(self.subplot_toolbar)
        self.addToolBar(self.legend_toolbar)
        self.addToolBar(self.axes_toolbar)

#        self.figure_settings.setFixedWidth(self.figure_settings.width())

        self.figure_settings.adjust_start_end()
        self.set_app_style(self.current_qss,
                           self.current_rcs,
                           self.current_icon_path)

        self.axes_frame.saved = True

        self.showMaximized()

        #!!! because for some reason it resizes this qcombobox??
        self.legend_toolbar.legend_location.setMinimumWidth(100)
        self.axes_toolbar.selector.setMinimumWidth(100)
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
            for s in groups[group].series(lambda s: s.keep):
                if s.alias:
                    aliases.append(s.alias)
                else:
                    aliases.append(s.header)
            contents.update({group: aliases})
        return contents

    def prep_fig(self):
        af = self.axes_frame
        fs = self.figure_settings
        fs.rename()
        fs.density.setValue(100)
        af.select_subplot(None, force_select=[])

    def save(self):
        """Quick-save feature.
        Saves current figure to most recent save directory
        if a file by that name already exists,
        else defers to explicit Save-As dialog.
        Accessible by Telemetry Grapher's File menu (or Ctrl+S)."""
        af = self.axes_frame
        filename = self.filename + '.jpg'
        if af.first_save or filename not in os.listdir(self.fig_dir):
            self.save_as()
        else:
            self.prep_fig()
            plt.savefig(self.fig_dir + '\\' + filename,
                        dpi=300, transparent=True, bbox_inches='tight')
#            with open(self.filename + '.pickle', 'wb') as f:
#                pl.dump(af.fig, f)
            self.statusBar().showMessage('Saved to {}'.format(self.fig_dir))
            af.saved = True

    def save_as(self):
        """Explicit Save-As feature.
        Saves current figure using PyQt5's file dialog.
        Default format is .jpg.
        Accessible by Telemetry Grapher's File menu (or Ctrl+Shift+S)."""
        self.prep_fig()
        af = self.axes_frame
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
            af.saved = True
            af.first_save = False

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
        af = self.axes_frame
        # af.saved = True  # CONVENIENCE OVERRIDE, DELETE LATER #!!!
        # This will change to if any([af.saved for af in axes_frames])
        if not af.saved:
            result = self.popup('Figure has not been saved. Exit anyway?',
                                title='Exiting Application')
            if result == QMessageBox.Cancel:
                event.ignore()
                return
            elif result == QMessageBox.Save:
                self.save()
        for dock in [self.series_display, self.figure_settings]:
            if dock.isFloating(): dock.close()
        plt.close('all')
        self.figure_settings.title_edit.editingFinished.disconnect()
        event.accept()

    def new(self):
        self.logger.error('too many chairs in here.')
        pass

    def set_app_style(self, qss, mpl_rcs, icon_path):
        app = QApplication.instance()
        if app is None:
            raise RuntimeError("No Qt Application found.")
            return
        app.setStyleSheet(qss)

        st = self.subplot_toolbar
        lt = self.legend_toolbar
        at = self.axes_toolbar
        actions = (st.insert, st.delete, st.clear,
                   st.cycle, st.reorder_up, st.reorder_down,
                   lt.color_toggle, lt.legend_toggle, lt.legend_units,
                   at.log_toggle, at.autoscale_toggle)
        for a in actions:
            a.setIcon(QIcon(icon_path+'/'+a.iconText()))

        for k,v in mpl_rcs.items(): plt.rcParams[k] = v
        af = self.axes_frame
        af.fig.set_facecolor(mpl_rcs['figure.facecolor'])
        af.fig.set_edgecolor(mpl_rcs['figure.edgecolor'])
        af.fig._suptitle.set_color(mpl_rcs['text.color'])
        for sp in af.subplots:
            for ax in sp.axes:
                ax.set_facecolor(mpl_rcs['axes.facecolor'])
                ax.patch.set_visible(False)
                ax.yaxis.label.set_color(mpl_rcs['axes.labelcolor'])
                for spine in ax.spines.values():
                    spine.set_color(mpl_rcs['axes.edgecolor'])
                for line in ax.get_xticklines():
                    line.set_color(mpl_rcs['xtick.color'])
                for line in ax.get_yticklines():
                    line.set_color(mpl_rcs['ytick.color'])
                for label in ax.get_xticklabels():
                    label.set_color(mpl_rcs['xtick.color'])
                for label in ax.get_yticklabels():
                    label.set_color(mpl_rcs['ytick.color'])
                for line in ax.get_xgridlines():
                    line.set_color(mpl_rcs['grid.color'])
                for line in ax.get_ygridlines():
                    line.set_color(mpl_rcs['grid.color'])
        af.replot()
        af.draw()

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
        docks = [self.series_display, self.figure_settings]
        if any([not dock.isVisible() for dock in docks]):
            for dock in docks: dock.show()
        else:
            for dock in docks: dock.hide()

    def toggle_dark_mode(self):
        if self.mode == 'light':
            self.mode = 'dark'
            self.current_qss = self.dark_qss
            self.current_rcs = self.dark_rcs
            self.current_icon_path = 'rc/entypo/dark'
        else:
            self.mode = 'light'
            self.current_qss = self.light_qss
            self.current_rcs = self.light_rcs
            self.current_icon_path = 'rc/entypo/light'
        default_color = self.current_rcs['axes.labelcolor']
        self.figure_settings.color_dict[None] = default_color
        self.figure_settings.color_dict[''] = default_color
        self.set_app_style(self.current_qss,
                           self.current_rcs,
                           self.current_icon_path)
# Legacy
#    def center(self):
#        qr = self.frameGeometry()
#        cp = QDesktopWidget().availableGeometry().center()
#        qr.moveCenter(cp)
#        self.move(qr.topLeft())
