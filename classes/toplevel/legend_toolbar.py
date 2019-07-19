# -*- coding: utf-8 -*-
"""legend_toolbar.py - Contains LegendToolbar class definition."""

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

from PyQt5.QtWidgets import (QToolBar, QComboBox, QAction, QSpinBox)

class LegendToolbar(QToolBar):

    def __init__(self, title, parent):
        super().__init__(title)
        self.parent = parent

        self.color_toggle = QAction('cc', self)
        self.color_toggle.setToolTip('Color Coordinate')
        self.color_toggle.setCheckable(True)
        self.color_toggle.setEnabled(False)
        self.color_toggle.triggered.connect(self.color_coordinate)
        self.addAction(self.color_toggle)

        self.legend_toggle = QAction('legend', self)
        self.legend_toggle.setToolTip('Toggle Legend')
        self.legend_toggle.setCheckable(True)
        self.legend_toggle.setEnabled(False)
        self.legend_toggle.triggered.connect(self.toggle_legend)
        self.addAction(self.legend_toggle)

#        self.legend_units = QToolButton(self)
#        def iconText():
#            return 'units'
#        self.legend_units.iconText = iconText
        self.legend_units = QAction('units', self)
        self.legend_units.setToolTip('Toggle Legend Units')
        self.legend_units.setCheckable(True)
        self.legend_units.setEnabled(False)
        self.legend_units.triggered.connect(self.toggle_legend_units)
        self.addAction(self.legend_units)

        self.legend_location = QComboBox()
        self.legend_location.setToolTip('Legend Location')
        self.legend_location.setEnabled(False)
        self.legend_location.addItem('None selected')
        # !!! Figure out how to make these comboboxes the right size!
#        self.legend_location.addItems(list(self.locations.keys()))
#        self.legend_location.clear()
        self.legend_location.currentTextChanged.connect(
                self.set_legend_location)
        self.legend_location.setMinimumHeight(33)
        self.addWidget(self.legend_location)

        self.legend_columns = QSpinBox()
        self.legend_columns.setToolTip('Legend Columns')
        self.legend_columns.setEnabled(False)
        self.legend_columns.setRange(1, 10)
        self.legend_columns.clear()
        self.legend_columns.valueChanged.connect(self.set_legend_columns)
        self.legend_columns.setMinimumHeight(33)
        self.addWidget(self.legend_columns)

    def toggle_legend(self, checked):
        """Toggles legend display of selected subplot(s)."""
        ui = self.parent
        cf = ui.get_current_figure()
        for sp in cf.current_sps:
            sp.legend_on = checked
        cf.replot(data=False)
        cf.update_gridspec()
        cf.draw()

    def set_legend_location(self, text):
        ui = self.parent
        cf = ui.get_current_figure()
        for sp in cf.current_sps:
            sp.location = text
        cf.replot(data=False)
        cf.update_gridspec()
        cf.draw()

    def set_legend_columns(self, value):
        ui = self.parent
        cf = ui.get_current_figure()
        for sp in cf.current_sps:
            sp.ncols = value
        cf.replot(data=False)
        cf.draw()

    def toggle_legend_units(self, checked):
        ui = self.parent
        cf = ui.get_current_figure()
        for sp in cf.current_sps:
            sp.legend_units = checked
        cf.replot(data=False)
        cf.draw()

    def color_coordinate(self, checked):
        """Coordinates colors of selected subplot(s) by unit type (not unit).
        Each unit type gets its own color for lines, labels, and ticks."""
        ui = self.parent
        cf = ui.get_current_figure()
        for sp in cf.current_sps:
            sp.color_coord = checked
        cf.replot()
        cf.draw()
