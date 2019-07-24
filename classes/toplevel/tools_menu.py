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

from PyQt5.QtWidgets import QMenu, QAction
from PyQt5.QtCore import Qt

from ..manager.data_manager import DataManager

class ToolsMenu(QMenu):
    def __init__(self, title, parent):
        super().__init__(title)
        self.parent = parent
        ui = parent
        data_action = QAction('Manage Data', ui)
        data_action.setShortcut('Ctrl+D')
        data_action.triggered.connect(self.open_data_manager)
        self.addAction(data_action)

        template_action = QAction('Import Template', ui)
        template_action.setShortcut('Ctrl+T')
        template_action.triggered.connect(self.import_template)
        self.addAction(template_action)

    def open_data_manager(self):
        """Opens Data Manager dialog.
        Accessible through Telemetry Grapher's Tools menu (or Ctrl+D)."""
        ui = self.parent
        ui.statusBar().showMessage('Opening Data Manager')
        ui.dlg = DataManager(ui)
        ui.dlg.setWindowFlags(Qt.Window)
        ui.dlg.setModal(True)
        ui.dlg.show()

    def import_template(self):
        pass