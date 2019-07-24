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
import json
import datetime as dt
import matplotlib.pyplot as plt

from PyQt5.QtWidgets import (QApplication, QWidget, QMainWindow, QTabWidget,
                             QMessageBox, QTabBar)
from PyQt5.QtGui import QIcon
from PyQt5.QtCore import Qt, QTextStream, QFile

from .axes_frame import AxesFrame
from .series_display import SeriesDisplay
from .figure_settings import FigureSettings
from .file_menu import FileMenu
from .edit_menu import EditMenu
from .tools_menu import ToolsMenu
from .view_menu import ViewMenu
from .subplot_toolbar import SubplotToolbar
from .legend_toolbar import LegendToolbar
from .axes_toolbar import AxesToolbar

from ..internal.contents_dict import ContentsDict
#from ..internal.bunch import Bunch
from ..internal.editable_tab_bar import EditableTabBar

class UI(QMainWindow):
    """Main application window."""

    def __init__(self, logger):
        super().__init__()
        self.logger = logger
        self.logger.info(' Application opened at {}'
                         .format(dt.datetime.now()))
        self.fig_dir = os.getcwd()
        self.df_dir = os.getcwd()
        self.path_kwargs = {}
        self.auto_parse = True
        self.all_groups = {}
        self.bypass = False

        stylesheets = []
        for f in (QFile('rc/light.qss'), QFile('rc/dark.qss')):
            if not f.exists():
                self.logger.error('Unable to load stylesheet,'
                                  '\"{}\" not found'.format(f.fileName()))
                stylesheets.append('')
            else:
                f.open(QFile.ReadOnly | QFile.Text)
                stylesheets.append(QTextStream(f).readAll())
        self.light_qss, self.dark_qss = stylesheets

        # Read settings from config file
        with open('config.json', 'r', encoding='utf-8') as f:
            self.config = json.load(f)
        self.unit_dict = self.config['unit_dict']
        self.unit_clarify = self.config['unit_clarify']
        self.user_units = self.config['user_units']
        self.default_type = self.config['default_type']
        self.default_unit = self.config['default_unit']
        self.light_rcs = self.config['light_rcs']
        self.dark_rcs = self.config['dark_rcs']
        self.mode = self.config['start_mode']
        obj = self.config['highlight']
        self.highlight = {True: obj['True'], False: obj['False']}
        self.af_init = self.config['af_init']
        self.csv_dir = self.config['csv_dir']

        if self.mode == 'light':
            self.current_qss = self.light_qss
            self.current_rcs = self.light_rcs
            self.current_icon_path = 'rc/entypo/light'
        elif self.mode == 'dark':
            self.current_qss = self.dark_qss
            self.current_rcs = self.dark_rcs
            self.current_icon_path = 'rc/entypo/dark'

        # For displaying subplot legends
        self.locations = {
            'Outside Right': 'center left',
            'Outside Top': 'lower center',
            'Upper Left': 'upper left',
            'Upper Center': 'upper center',
            'Upper Right': 'upper right',
            'Center Left': 'center left',
            'Center Right': 'center right',
            'Lower Left': 'lower left',
            'Lower Center': 'lower center',
            'Lower Right': 'lower right',
            }

        self.setWindowTitle('Telemetry Plot Configurator')
        self.setWindowIcon(QIcon('rc/satellite.png'))
        self.statusBar().showMessage('No subplot selected')

        self.tab_base = QTabWidget()
        self.tab_bar = EditableTabBar(self)
        self.tab_base.setTabBar(self.tab_bar)
        cf = AxesFrame(self)
        self.tab_base.addTab(cf, cf.title)
        self.tab_base.addTab(QWidget(), '+')
        self.tab_base.tabBar().setStyleSheet("""
                            QTabBar::tab:last
                            {
                                width: 6ex;
                                min-width: 6ex;
                                height: 6ex;
                            }
                            """)
        self.tab_base.setTabsClosable(True)
        self.tab_base.tabCloseRequested.connect(self.close_tab)
        self.tab_base.tabBar().tabButton(1, QTabBar.RightSide).resize(0,0)
        self.tab_base.tabBar().setSelectionBehaviorOnRemove(
                QTabBar.SelectPreviousTab)
        self.tab_base.setTabPosition(QTabWidget.South)
        self.tab_base.setStyleSheet("""
                            QTabWidget::tab-bar
                            {
                                alignment: left;
                            }
                            """)
        self.setCentralWidget(self.tab_base)

        self.series_display = SeriesDisplay(self, "Series Display")
        self.figure_settings = FigureSettings(self, "Figure Settings")
        self.figure_settings.setAllowedAreas(Qt.RightDockWidgetArea |
                                             Qt.LeftDockWidgetArea)

        self.addDockWidget(Qt.LeftDockWidgetArea, self.series_display)
        self.addDockWidget(Qt.RightDockWidgetArea, self.figure_settings)

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

        self.figure_settings.update_fields(cf)
        self.set_app_style(self.current_qss,
                           self.current_rcs,
                           self.current_icon_path)
        cf.saved = True
        self.tab_base.currentChanged.connect(self.update_dock_widgets)
        self.showMaximized()

        self.resizeDocks([self.series_display, self.figure_settings],
                         [420, 165],
                         Qt.Horizontal)
        #!!! because for some reason it resizes this qcombobox??
        self.legend_toolbar.legend_location.setMinimumWidth(100)
        self.axes_toolbar.selector.setMinimumWidth(100)
        ### Delete later, just for speed
#        self.open_data_manager()

    def get_current_figure(self):
        return self.tab_base.currentWidget()

    def all_figures(self):
        return [self.tab_base.widget(i) for i in range(self.nfigs())]

    def nfigs(self):
        return self.tab_base.count()-1

    def open_figure_titles(self):
        return [self.tab_base.tabText(i) for i in range(self.nfigs())]

    def update_dock_widgets(self, i):
        if i == self.nfigs():
            self.file_menu.new()
        cf = self.tab_base.widget(i)
        savestate = cf.saved
        sd = self.series_display
        fs = self.figure_settings
        sd.populate_tree('available', cf.available_data)
        if len(cf.current_sps) == 1:
            sp = cf.current_sps[0]
            sd.populate_tree('plotted', sp.contents)
        else:
            sd.plotted.clear()
        fs.update_fields(cf)
        cf.update_toolbars()
        cf.saved = savestate

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
        for group_name in groups:
            group = self.all_groups[group_name]
            aliases = []
            for s in group.series(lambda s: s.keep):
                if s.alias:
                    aliases.append(s.alias)
                else:
                    aliases.append(s.header)
            contents.update({group_name: aliases})
        return contents

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
        for cf in self.all_figures():
            cf.fig.set_facecolor(mpl_rcs['figure.facecolor'])
            cf.fig.set_edgecolor(mpl_rcs['figure.edgecolor'])
            cf.fig._suptitle.set_color(mpl_rcs['text.color'])
            for sp in cf.subplots:
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
            cf.replot()
            cf.draw()
        lt.legend_location.setMinimumWidth(100)
        at.selector.setMinimumWidth(100)

    def close_tab(self, i):
        if i == self.nfigs(): return
        cf = self.tab_base.widget(i)
        if self.nfigs() == 1:
            if not cf.saved:
                result = self.popup('{} has not been saved. Exit anyway?'
                                    .format(cf.title),
                                    title='Closing Tab',
                                    informative='Application will exit.')
            else:
                result = self.popup('Closing the last tab will exit '
                                'the application. Continue?',
                                title='Exiting Application',
                                mode='confirm')
            if result == QMessageBox.Cancel:
                return
            elif result == QMessageBox.Save:
                if not self.file_menu.save(): return
            self.bypass = True
            self.close()
        else:
            if not cf.saved:
                result = self.popup('{} has not been saved. Close anyway?'
                                    .format(cf.title),
                                    title='Closing Tab')
                if result == QMessageBox.Cancel:
                    return
                elif result == QMessageBox.Save:
                    if not self.file_menu.save(): return
            plt.close(cf.fig)
            self.tab_base.blockSignals(True)
            self.tab_base.removeTab(i)
            self.tab_base.blockSignals(False)
            if self.tab_base.currentIndex() == self.nfigs():
                self.tab_base.setCurrentIndex(i-1)

    def closeEvent(self, event):
        """Called when application is about to exit.
        If close event accepted,
        - hide any floating dockwidgets
        - close all created figures"""
        if not self.bypass:
            for i in reversed(range(self.nfigs())):
                self.tab_base.setCurrentIndex(i)
                cf = self.tab_base.widget(i)
                if not cf.saved:
                    result = self.popup('{} has not been saved. Close anyway?'
                                        .format(cf.title),
                                        title='Exiting Application')
                    if result == QMessageBox.Cancel:
                        event.ignore()
                        break
                    elif result == QMessageBox.Save:
                        if not self.file_menu.save():
                            event.ignore()
                            break

        if event.isAccepted():
            for dock in [self.series_display, self.figure_settings]:
                if dock.isFloating(): dock.close()

            self.config['start_mode'] = self.mode
            self.config['csv_dir'] = self.csv_dir
            with open('config.json', 'w', encoding='utf-8') as f:
                json.dump(self.config, f, indent=2, ensure_ascii=False)

            plt.close('all')
            self.logger.info(' Application closed at {}\n'
                             .format(dt.datetime.now()))
