# -*- coding: utf-8 -*-
"""tools_menu.py - Contains ToolsMenu class definition."""

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

import json
import os

from PyQt5.QtWidgets import QMenu, QAction, QFileDialog
from PyQt5.QtCore import Qt

from telemetry_grapher.classes.manager.data_manager import DataManager

class ToolsMenu(QMenu):
    def __init__(self, title, parent):
        super().__init__(title)
        self.parent = parent
        ui = parent
        data_action = QAction('Manage Data', ui)
        data_action.setShortcut('Ctrl+D')
        data_action.triggered.connect(self.open_data_manager)
        self.addAction(data_action)

        export_template_action = QAction('Export Template', ui)
        export_template_action.setShortcut('Ctrl+E')
        export_template_action.triggered.connect(self.export_template)
        self.addAction(export_template_action)

        import_template_action = QAction('Import Template', ui)
        import_template_action.setShortcut('Ctrl+I')
        import_template_action.triggered.connect(self.import_template)
        self.addAction(import_template_action)

    def open_data_manager(self):
        """Opens Data Manager dialog.
        Accessible through Telemetry Grapher's Tools menu (or Ctrl+D)."""
        ui = self.parent
        ui.statusBar().showMessage('Opening Data Manager')
        ui.dlg = DataManager(ui)
        ui.dlg.setWindowFlags(Qt.Window)
        ui.dlg.setModal(True)
        ui.dlg.show()

    def export_template(self):
        ui = self.parent
        dlg = QFileDialog()
        dlg.setFileMode(QFileDialog.AnyFile)
        dlg.setViewMode(QFileDialog.Detail)
        dlg_out = dlg.getSaveFileName(ui, 'Export Template',
                                        'templates',
                                        'JSON (*.json)')
        if dlg_out[0]:
            export_path = dlg_out[0]
            cf = ui.get_current_figure()
            template = {
                'tsf': cf.tsf,
                # 'title': 'Untitled',
                'upper_pad': cf.upper_pad,
                'lower_pad': cf.lower_pad,
                'left_pad': cf.left_pad,
                'right_pad': cf.right_pad,
                'spacing': cf.spacing,
                'axis_offset': cf.axis_offset,
                'MX': cf.MX,
                'mx': cf.mx,
                'MY': cf.MY,
                'my': cf.my,
                'M_T': cf.M_T,
                'm_T': cf.m_T,
                'scatter': cf.scatter,
                'dot_size': cf.dot_size,
                'density': cf.density,
                'x_margin': cf.x_margin,
                'title_size': cf.title_size,
                'label_size': cf.label_size,
                'tick_size': cf.tick_size,
                'tick_rot': cf.tick_rot,
                'nplots': cf.nplots(),
                'weights': cf.weights()
            }
            with open(export_path, 'w', encoding='utf-8') as f:
                json.dump(template, f, indent=2, ensure_ascii=False)
            ui.statusBar().showMessage('Exported to {}'.format(export_path))
            return True
        return False

    def import_template(self):
        ui = self.parent
        dlg = QFileDialog()
        dlg.setFileMode(QFileDialog.AnyFile)
        dlg.setViewMode(QFileDialog.Detail)
        dlg_out = dlg.getOpenFileName(ui, 'Import Template',
                                        'templates',
                                        'JSON (*.json)')
        if dlg_out[0]:
            import_path = dlg_out[0]
            cf = ui.get_current_figure()
            with open(import_path, 'r', encoding='utf-8') as f:
                template = json.load(f)
            nplots = template['nplots']
            weights = template['weights']
            del template['nplots'], template['weights']

            for k,v in template.items():
                setattr(cf, k, v)
            if cf.nplots() > nplots:
                filename = os.path.split(import_path)[1].split('.')[0]
                ui.popup(
                    text='Too few subplots in template', title='Import Template',
                    informative='\"{}\" has fewer subplots than the current figure.'
                    'The number of subplots and their weights are unchanged.'.format(filename),
                    mode='alert'
                    )
            else:
                while cf.nplots() < nplots:
                    ui.subplot_toolbar.insert_subplot()
                cf.update_gridspec(nplots, weights)
            ui.figure_settings.update_fields(cf)
            cf.draw()
            return True
        return False
