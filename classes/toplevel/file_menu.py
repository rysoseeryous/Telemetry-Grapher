# -*- coding: utf-8 -*-
"""file_menu.py - Contains FileMenu class definition."""

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

from PyQt5.QtWidgets import QMenu, QAction, QFileDialog

from telemetry_grapher.classes.toplevel.axes_frame import AxesFrame

class FileMenu(QMenu):
    def __init__(self, title, parent):
        super().__init__(title)
        self.parent = parent
        ui = parent
        new_action = QAction('New', ui)
        new_action.setShortcut('Ctrl+N')
        new_action.triggered.connect(self.new)
        self.addAction(new_action)

#        open_action = QAction('Open', ui)
#        open_action.setShortcut('Ctrl+O')
#        open_action.triggered.connect(self.open_fig)
#        self.addAction(open_action)

        close_action = QAction('Close', ui)
        close_action.setShortcut('Ctrl+W')
        close_action.triggered.connect(self.close_tab)
        self.addAction(close_action)

        save_action = QAction('Save', ui)
        save_action.setShortcut('Ctrl+S')
        save_action.triggered.connect(self.save)
        self.addAction(save_action)

        save_as_action = QAction('Save As', ui)
        save_as_action.setShortcut('Ctrl+Shift+S')
        save_as_action.triggered.connect(self.save_as)
        self.addAction(save_as_action)

        save_all_action = QAction('Save All', ui)
        save_all_action.setShortcut('Ctrl+Alt+S')
        save_all_action.triggered.connect(self.save_all)
        self.addAction(save_all_action)

        exit_action = QAction('Exit', ui)
        exit_action.setShortcut('Ctrl+Q')
        exit_action.triggered.connect(ui.close)
        self.addAction(exit_action)

    def new(self):
        ui = self.parent
        i = ui.nfigs()
        cf = AxesFrame(ui)
        title = cf.title
        count = 1
        while cf.title in ui.open_figure_titles():
            cf.title = title + str(count)
            count += 1
        cf.fig._suptitle.set_text(cf.title)
        ui.tab_base.insertTab(i, cf, cf.title)
        ui.tab_base.setCurrentIndex(i)
        cf.replot()
        cf.saved = True

    def open_fig(self):
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

    def close_tab(self):
        ui = self.parent
        i = ui.tab_base.currentIndex()
        ui.close_tab(i)

    def save(self, _=None, cf=None):
        """Quick-save feature.
        Saves current figure to most recent save directory
        if a file by that name already exists,
        else defers to explicit Save-As dialog.
        Accessible by Telemetry Grapher's File menu (or Ctrl+S)."""
        ui = self.parent
        if cf is None:
            cf = ui.get_current_figure()
        filename = cf.title + '.jpg'
        if cf.never_saved or filename not in os.listdir(ui.fig_dir):
            return self.save_as(cf=cf)
        else:
            cf.prep_fig()
            cf.fig.savefig(ui.fig_dir + '/' + filename,
                           dpi=300, transparent=True, bbox_inches='tight')
#            with open(self.filename + '.pickle', 'wb') as f:
#                pl.dump(cf.fig, f)
            ui.statusBar().showMessage('Saved to {}'.format(ui.fig_dir))
            cf.saved = True
            return True

    def save_as(self, _=None, cf=None):
        """Explicit Save-As feature.
        Saves current figure using PyQt5's file dialog.
        Default format is .jpg.
        Accessible by Telemetry Grapher's File menu (or Ctrl+Shift+S)."""
        ui = self.parent
        if cf is None:
            cf = ui.get_current_figure()
        cf.prep_fig()
        dlg = QFileDialog()
        dlg.setFileMode(QFileDialog.AnyFile)
        dlg.setViewMode(QFileDialog.Detail)
        dlg_out = dlg.getSaveFileName(ui, 'Save Figure',
                                      ui.fig_dir + '/' + cf.title,
                                      'PNG Image (*.png)')
        # JPG export in matplotlib is bugged as of Jun 30 2020
        if dlg_out[0]:
            savepath = dlg_out[0]
            # store saving directory
            ui.fig_dir = os.path.dirname(savepath)
            cf.fig.savefig(savepath,
                           dpi=300, transparent=True, bbox_inches='tight')
#            with open(self.filename + '.pickle', 'wb') as f:
#                pkl.dump(cf.fig, f)
            ui.statusBar().showMessage('Saved to {}'.format(savepath))
            cf.saved = True
            cf.never_saved = False
            return True
        else:
            return False

    def save_all(self, _=None):
        ui = self.parent
        for cf in ui.all_figures():
            self.save(cf)
