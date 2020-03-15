# -*- coding: utf-8 -*-
"""clarified_table.py - Contains ClarifiedTable class definition."""

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

from PyQt5.QtWidgets import (QTableWidget, QTableWidgetItem,
                             QPushButton, QHeaderView)
from PyQt5.QtCore import Qt, QObject

from telemetry_grapher.classes.internal.dict_combo import DictCombo

class ClarifiedTable(QTableWidget):

    def __init__(self, parent):
        super().__init__()
        self.parent = parent
        ut = self.parent
        dm = ut.parent

        self.setColumnCount(2)
        self.setHorizontalHeaderLabels(['Parsed', 'Interpreted'])
        self.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.verticalHeader().hide()
        self.setRowCount(len(dm.unit_clarify)+1)
        self.clarify_cache = []
        for row, key in enumerate(dm.unit_clarify):
            self.clarify_cache.append(key)
            self.setItem(row, 0, QTableWidgetItem(key))
            clarify_combo = DictCombo(dm.all_units,
                                      None,
                                      self.get_clarified_value)
            clarify_combo.row = row
            clarify_combo.populate()
            clarify_combo.currentTextChanged.connect(self.update_clarify_value)
            self.setCellWidget(row, 1, clarify_combo)
        self.add_button = QPushButton('Add')
        self.add_button.clicked.connect(self.add_clarified_row)
        self.setSpan(row+1, 0, 1, 2)
        self.setCellWidget(row+1, 0, self.add_button)
        self.cellChanged.connect(self.update_clarify_key)

    def combos(self):
        return [self.cellWidget(row, 1) for row in range(self.rowCount()-1)]

    def get_clarified_value(self, row):
        ut = self.parent
        dm = ut.parent
        key = self.item(row, 0).text()
        try:
            return dm.unit_clarify[key]
        except KeyError:
            return ''

    def update_clarify_key(self, row, col):
        ut = self.parent
        dm = ut.parent
        item = self.item(row, 0)
        key = item.text()
        if key and key not in self.clarify_cache:
            value = self.cellWidget(row, 1).currentText()
            if row < len(self.clarify_cache):
                # Rename existing entry
                old = self.clarify_cache[row]
                del dm.unit_clarify[old]
                self.clarify_cache[row] = key
            else:
                # Add new entry
                self.clarify_cache.append(key)
            dm.unit_clarify[key] = value
            dm.modified = True
        else:
            try:
                item.setText(self.clarify_cache[row])
            except IndexError:
                self.removeRow(row)
                self.clearSelection()

    def update_clarify_value(self, value):
        ut = self.parent
        dm = ut.parent
        clarify_combo = QObject.sender(self)
        key = self.item(clarify_combo.row, 0).text()
        dm.unit_clarify[key] = value
        dm.modified = True

    def add_clarified_row(self):
        ut = self.parent
        dm = ut.parent
        row = self.rowCount()-1
        self.insertRow(row)
        item = QTableWidgetItem()
        self.blockSignals(True)
        self.setItem(row, 0, item)
        clarify_combo = DictCombo(dm.all_units,
                                  None,
                                  self.get_clarified_value)
        clarify_combo.row = row
        clarify_combo.populate()
        clarify_combo.currentTextChanged.connect(self.update_clarify_value)
        self.clearSelection()
        self.setCellWidget(row, 1, clarify_combo)
        self.editItem(item)
        self.blockSignals(False)

    def delete_clarified_row(self):
        ut = self.parent
        dm = ut.parent
        all_rows = [item.row() for item in self.selectedIndexes()]
        for row in sorted(set(all_rows), reverse=True):
            key = self.item(row, 0).text()
            if key in dm.unit_clarify:
                del dm.unit_clarify[key]
            self.clarify_cache.pop(row)
            self.removeRow(row)
            dm.modified = True
        for row in range(self.rowCount()-1):
            clarify_combo = self.cellWidget(row, 1)
            clarify_combo.row = row

    def closeEditor(self, editor, hint):
        self.commitData(editor)
        QTableWidget.closeEditor(self, editor, hint)

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Delete:
            ut = self.parent
            dm = ut.parent
            all_rows = [item.row() for item in self.selectedIndexes()]
            for row in sorted(set(all_rows), reverse=True):
                key = self.item(row, 0).text()
                if key in dm.unit_clarify:
                    del dm.unit_clarify[key]
                self.clarify_cache.pop(row)
                self.removeRow(row)
                dm.modified = True
            for row in range(self.rowCount()-1):
                clarify_combo = self.cellWidget(row, 1)
                clarify_combo.row = row
        QTableWidget.keyPressEvent(self, event)

