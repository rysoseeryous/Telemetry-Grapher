# -*- coding: utf-8 -*-
"""menus.py -
Contains FileMenu, EditMenu, ToolsMenu, and ViewMenu class definitions."""

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

class FileMenu(QMenu):
    def __init__(self, title, parent):
        super().__init__(title)
        self.parent = parent
        ui = parent
        new_action = QAction('New', ui)
        new_action.setShortcut('Ctrl+N')
        new_action.triggered.connect(ui.new)
        self.addAction(new_action)

        open_action = QAction('Open', ui)
        open_action.setShortcut('Ctrl+O')
        open_action.triggered.connect(ui.open_fig)
        self.addAction(open_action)

        save_action = QAction('Save', ui)
        save_action.setShortcut('Ctrl+S')
        save_action.triggered.connect(ui.save)
        self.addAction(save_action)

        save_as_action = QAction('Save As', ui)
        save_as_action.setShortcut('Ctrl+Shift+S')
        save_as_action.triggered.connect(ui.save_as)
        self.addAction(save_as_action)

        exit_action = QAction('Exit', ui)
        exit_action.setShortcut('Ctrl+Q')
        exit_action.triggered.connect(ui.close)
        self.addAction(exit_action)

class EditMenu(QMenu):
    def __init__(self, title, parent):
        super().__init__(title)
        self.parent = parent
        ui = parent
        undo_action = QAction('Undo', ui)
        undo_action.setShortcut('Ctrl+Z')
        undo_action.triggered.connect(ui.undo)
        self.addAction(undo_action)

        redo_action = QAction('Redo', ui)
        redo_action.setShortcut('Ctrl+Y')
        redo_action.triggered.connect(ui.redo)
        self.addAction(redo_action)

#        refresh_action = QAction('Refresh Figure', ui)
#        refresh_action.setShortcut('Ctrl+R')
#        refresh_action.triggered.connect(ui.axes_frame._draw)
#        self.addAction(refresh_action)

class ToolsMenu(QMenu):
    def __init__(self, title, parent):
        super().__init__(title)
        self.parent = parent
        ui = parent
        data_action = QAction('Manage Data', ui)
        data_action.setShortcut('Ctrl+D')
        data_action.triggered.connect(ui.open_data_manager)
        self.addAction(data_action)

        template_action = QAction('Import Template', ui)
        template_action.setShortcut('Ctrl+T')
        template_action.triggered.connect(ui.import_template)
        self.addAction(template_action)

class ViewMenu(QMenu):
    def __init__(self, title, parent):
        super().__init__(title)
        self.parent = parent
        ui = parent
        docks_action = QAction('Show/Hide Docks', ui)
        docks_action.setShortcut('Ctrl+H')
        docks_action.triggered.connect(ui.toggle_docks)
        self.addAction(docks_action)

        dark_action = QAction('Toggle Dark Mode', ui)
        dark_action.setShortcut('Ctrl+B')
        dark_action.triggered.connect(ui.toggle_dark_mode)
        self.addAction(dark_action)