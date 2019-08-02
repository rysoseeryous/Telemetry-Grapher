# -*- coding: utf-8 -*-
"""unit_tree.py - Contains UnitTree class definition."""

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

from PyQt5.QtWidgets import QTreeView
from PyQt5.QtGui import QStandardItem, QIcon
from PyQt5.QtCore import Qt

class UnitTree(QTreeView):

    def __init__(self, parent, model, unit_dict,
                 L0_edit=True, L1_edit=True, L0_add=True, L1_add=True):
        super().__init__()
        self.parent = parent
        self.doubleClicked.connect(self.add)
        self.setModel(model)
        model.tree = self
        self.unit_dict = unit_dict
        self.type_cache = []
        for unit_type in self.unit_dict:
            self.type_cache.append(unit_type)
            L0 = QStandardItem(unit_type)
            L0.setEditable(L0_edit)
            for unit in self.unit_dict[unit_type]:
                L1 = QStandardItem(unit)
                L1.setEditable(L1_edit)
                L0.appendRow([L1])
            if L1_add: L0.appendRow([self.plus()])
            self.model().appendRow(L0)
        if L0_add: self.model().appendRow([self.plus()])

    def plus(self):
        ut = self.parent
        dm = ut.parent
        item = QStandardItem()
        item.setIcon(QIcon(dm.parent.current_icon_path+'/plus.png'))
        return item

    def add(self, index):
        row = index.row()
        item = self.model().itemFromIndex(index)
        if item.data(1) is not None:
            if item.parent():
                new_item = QStandardItem()
                item.parent().insertRow(row, new_item)
            else:
                new_item = QStandardItem()
                new_item.appendRow([self.plus()])
                self.model().insertRow(row, new_item)
            self.scrollTo(new_item.index())
            self.edit(new_item.index())

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Delete:
            if self.selectedIndexes():
                index = self.selectedIndexes()[0]
                item = self.model().itemFromIndex(index)
                if item.data(1) is None:
                    if item.parent():
                        self.delete_unit(item)
                    else:
                        self.delete_unit_type(item)
        else:
            QTreeView.keyPressEvent(self, event)

    def delete_unit(self, item):
        ut = self.parent
        dm = ut.parent
        level0 = item.parent()
        i = item.row()
        unit = item.text()
        unit_type = level0.text()
        self.unit_dict[unit_type].remove(unit)
        self.model().removeRow(i, level0.index())
        for combo in dm.unit_combos():
            combo.populate()
        dm.modified = True

    def delete_unit_type(self, item):
        ut = self.parent
        dm = ut.parent
        i = item.row()
        unit_type = item.text()
        self.type_cache.remove(unit_type)
        del self.unit_dict[unit_type]
        self.model().removeRow(i, item.index().parent())
        for combo in dm.type_combos():
            combo.removeItem(i+1)
            combo.setCurrentText('')
        dm.modified = True
