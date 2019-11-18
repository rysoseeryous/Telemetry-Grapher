# -*- coding: utf-8 -*-
"""view_menu.py - Contains ViewMenu class definition."""

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

class ViewMenu(QMenu):
    def __init__(self, title, parent):
        super().__init__(title)
        self.parent = parent
        ui = parent
        docks_action = QAction('Show/Hide Docks', ui)
        docks_action.setShortcut('Ctrl+H')
        docks_action.triggered.connect(self.toggle_docks)
        self.addAction(docks_action)

        dark_action = QAction('Toggle Dark Mode', ui)
        dark_action.setShortcut('Ctrl+B')
        dark_action.triggered.connect(self.toggle_dark_mode)
        self.addAction(dark_action)

    def toggle_docks(self):
        """Toggles visibility of dock widgets.
        Accessible through Telemetry Grapher's View menu (or Ctrl+H)."""
        ui = self.parent
        docks = [ui.series_display, ui.figure_settings]
        if any([not dock.isVisible() for dock in docks]):
            for dock in docks: dock.show()
        else:
            for dock in docks: dock.hide()

    def toggle_dark_mode(self):
        ui = self.parent
        if ui.mode == 'light':
            ui.mode = 'dark'
            ui.current_qss = ui.dark_qss
            ui.current_rcs = ui.dark_rcs
            ui.current_icon_path = 'telemetry_grapher/rc/entypo/dark'
        else:
            ui.mode = 'light'
            ui.current_qss = ui.light_qss
            ui.current_rcs = ui.light_rcs
            ui.current_icon_path = 'telemetry_grapher/rc/entypo/light'
        default_color = ui.current_rcs['axes.labelcolor']
        ui.color_dict[None] = default_color
        ui.color_dict[''] = default_color
        ui.set_app_style(ui.current_qss,
                         ui.current_rcs,
                         ui.current_icon_path)
