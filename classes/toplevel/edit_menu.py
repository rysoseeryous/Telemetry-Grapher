# -*- coding: utf-8 -*-
"""edit_menu.py - Contains EditMenu class definition."""

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

class EditMenu(QMenu):
    def __init__(self, title, parent):
        super().__init__(title)
        self.parent = parent
        ui = parent
        undo_action = QAction('Undo', ui)
        undo_action.setShortcut('Ctrl+Z')
        undo_action.triggered.connect(self.undo)
        self.addAction(undo_action)

        redo_action = QAction('Redo', ui)
        redo_action.setShortcut('Ctrl+Y')
        redo_action.triggered.connect(self.redo)
        self.addAction(redo_action)

#        refresh_action = QAction('Refresh Figure', ui)
#        refresh_action.setShortcut('Ctrl+R')
#        refresh_action.triggered.connect(ui.axes_frame._draw)
#        self.addAction(refresh_action)

    def undo(self):
        pass

    def redo(self):
        pass
