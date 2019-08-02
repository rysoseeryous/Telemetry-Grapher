# -*- coding: utf-8 -*-
"""unit_model.py - Contains UnitModel class definition."""

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

from PyQt5.QtGui import QStandardItemModel

class UnitModel(QStandardItemModel):

    def __init__(self, parent, label):
        super().__init__()
        self.parent = parent
        self.tree = None
        self.setHorizontalHeaderLabels([label])
        self.itemChanged.connect(self.edit_handler)

    def edit_handler(self, item):
        if item.parent():
            self.edit_unit(item)
        else:
            self.edit_unit_type(item)

    def edit_unit(self, item):
        ut = self.parent
        dm = ut.parent
        i = item.row()
        unit_type = item.parent().text()
        unit = item.text().strip()
        if unit and unit not in self.tree.unit_dict[unit_type]:
            try:
                # Rename existing unit
                old = self.tree.unit_dict[unit_type][i]
                self.tree.unit_dict[unit_type][i] = unit
                for combo in dm.unit_combos():
                    idx = combo.findText(old)
                    combo.setItemText(idx, unit)
            except IndexError:
                # Add new unit
                self.tree.unit_dict[unit_type].append(unit)
                for combo in dm.unit_combos():
                    combo.populate()
            dm.modified = True
        else:
            try:
                item.setText(self.tree.unit_dict[unit_type][i])
            except IndexError:
                self.removeRow(i, item.parent().index())

    def edit_unit_type(self, item):
        ut = self.parent
        dm = ut.parent
        i = item.row()
        unit_type = item.text().strip()
        if unit_type and unit_type not in dm.all_units():
            if i < len(self.tree.type_cache):
                # Rename existing unit type
                old = self.tree.type_cache[i]
                self.tree.unit_dict[unit_type] = self.tree.unit_dict[old]
                del self.tree.unit_dict[old]
                self.tree.type_cache[i] = unit_type
                for combo in dm.type_combos():
                    idx = combo.findText(old)
                    combo.setItemText(idx, unit_type)
            else:
                # Add new unit type
                self.tree.type_cache.append(unit_type)
                self.tree.unit_dict[unit_type] = []
                for combo in dm.type_combos():
                    combo.insertItem(i+1, unit_type)
            dm.modified = True
        else:
            try:
                item.setText(self.tree.type_cache[i])
            except IndexError:
                self.removeRow(i, item.index().parent())
