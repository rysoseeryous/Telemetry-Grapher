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
import matplotlib.pyplot as plt

from PyQt5.QtWidgets import (QApplication, QWidget, QMainWindow, QTabWidget,
                             QMessageBox, QFileDialog, QTabBar)
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
from ..internal.bunch import Bunch
from ..internal.editable_tab_bar import EditableTabBar

class UI(QMainWindow):
    """Main application window."""

    def __init__(self, logger):
        super().__init__()
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
        self.mode = startup['start_mode']
        obj = startup['highlight']
        self.highlight = {True: obj['True'], False: obj['False']}
        self.af_init = startup['af_init']

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
        cf = AxesFrame(self, Bunch(self.af_init))
        self.tab_base.addTab(cf, cf.fig_params.title)
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

    def close_tab(self, i):
        if i != self.nfigs() and self.nfigs() != 1:
            cf = self.tab_base.widget(i)
            plt.close(cf.fig)
            self.tab_base.blockSignals(True)
            self.tab_base.removeTab(i)
            self.tab_base.blockSignals(False)
            if self.tab_base.currentIndex() == self.nfigs():
                self.tab_base.setCurrentIndex(i-1)

    def update_dock_widgets(self, i):
        if i == self.nfigs():
            default = Bunch(self.af_init)
            title = default.title
            count = 1
            while default.title in self.open_figure_titles():
                default.title = title + str(count)
                count += 1
            cf = AxesFrame(self, default)
            self.tab_base.insertTab(i, cf, default.title)
            self.tab_base.setCurrentIndex(i)
            cf.replot()

        cf = self.tab_base.widget(i)
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
        cf = self.get_current_figure()
        fs = self.figure_settings
        fs.rename()
        fs.density.setValue(100)
        cf.select_subplot(None, force_select=[])

    def save(self):
        """Quick-save feature.
        Saves current figure to most recent save directory
        if a file by that name already exists,
        else defers to explicit Save-As dialog.
        Accessible by Telemetry Grapher's File menu (or Ctrl+S)."""
        cf = self.get_current_figure()
        filename = cf.fig_params.title + '.jpg'
        if cf.first_save or filename not in os.listdir(self.fig_dir):
            self.save_as()
        else:
            self.prep_fig()
            plt.savefig(self.fig_dir + '\\' + filename,
                        dpi=300, transparent=True, bbox_inches='tight')
#            with open(self.filename + '.pickle', 'wb') as f:
#                pl.dump(cf.fig, f)
            self.statusBar().showMessage('Saved to {}'.format(self.fig_dir))
            cf.saved = True

    def save_as(self):
        """Explicit Save-As feature.
        Saves current figure using PyQt5's file dialog.
        Default format is .jpg.
        Accessible by Telemetry Grapher's File menu (or Ctrl+Shift+S)."""
        self.prep_fig()
        cf = self.get_current_figure()
        dlg = QFileDialog()
        dlg.setFileMode(QFileDialog.AnyFile)
        dlg.setViewMode(QFileDialog.Detail)
        dlg_out = dlg.getSaveFileName(self, 'Save Figure',
                                      self.fig_dir + '/' + cf.fig_params.title,
                                      'JPEG Image (*.jpg)')#;;PNG Image (*.png)
        if dlg_out[0]:
            savepath = dlg_out[0]
            # store saving directory
            self.fig_dir = os.path.dirname(savepath)
            plt.savefig(savepath,
                        dpi=300, transparent=True, bbox_inches='tight')
#            with open(self.filename + '.pickle', 'wb') as f:
#                pkl.dump(cf.fig, f)
            self.statusBar().showMessage('Saved to {}'.format(savepath))
            cf.saved = True
            cf.first_save = False

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
        cf = self.get_current_figure()
        cf.saved = True  # CONVENIENCE OVERRIDE, DELETE LATER #!!!
        # This will change to if any([cf.saved for af in axes_frames])
        if not cf.saved:
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
        event.accept()

    def new(self):
        # overriding for testing
        print(self.tab_base.currentWidget())

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

    def open_fig(self):
        raise Exception
        pass
#        print(self.figure_settings.unit_table.size())
#        print(self.figure_settings.majorXgrid.isChecked())
#        pass
#        cf = self.get_current_figure()
#        dlg_output = QFileDialog.getOpenFileName(self,
#                                                  "Open Saved Figure",
#                                                  self.fig_dir,
#                                                  "(*.pickle)")
#        if dlg_output[0]:
#            fig = pkl.load(open(dlg_output[0], 'rb'))
#            _ = plt.figure()
#            manager = _.canvas.manager
#            manager.canvas.figure = fig
#            cf.fig.set_canvas(manager.canvas)
#            print(fig)
#            for ax in fig.axes:
#                print(ax)
#                print(ax.lines)
#                print(ax.get_legend())
#                h, l = ax.get_legend_handles_labels()
#                print(h)
#                print(l)
#            cf.fig.show()
#            cf.draw()

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

