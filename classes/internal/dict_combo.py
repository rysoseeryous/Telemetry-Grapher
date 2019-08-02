# -*- coding: utf-8 -*-
"""dict_combo.py - Contains DictCombo class definition."""

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

from PyQt5.QtWidgets import QComboBox

class DictCombo(QComboBox):

    def __init__(self, get_unit_dict, get_unit_type=None, get_unit=None):
        super().__init__()
        self.get_unit_dict = get_unit_dict
        self.get_unit = get_unit
        self.get_unit_type = get_unit_type

        def populate_units():
            # Unit Combos
            reset = self.get_unit()
            self.clear()
            if self.get_unit_type() in self.get_unit_dict():
                self.addItem('')
                self.addItems(self.get_unit_dict()[self.get_unit_type()])
            self.setCurrentText(reset)

        def populate_types():
            # Type Combos
            reset = self.get_unit_type()
            self.clear()
            self.addItem('')
            self.addItems(list(self.get_unit_dict().keys()))
            self.setCurrentText(reset)

        def populate_all_units():
            # Clarify Combos
            reset = self.get_unit(self.row)
            self.clear()
            for units in self.get_unit_dict().values():
                self.addItems(units)
            self.setCurrentText(reset)

        if self.get_unit_type is not None:
            if self.get_unit is not None:
                self.populate = populate_units
            else:
                self.populate = populate_types
        else:
            self.populate = populate_all_units
