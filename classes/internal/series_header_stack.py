# -*- coding: utf-8 -*-
"""series_header_stack.py - Contains SeriesHeaderStack class definition."""

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

from PyQt5.QtWidgets import QWidget, QLabel, QCheckBox, QVBoxLayout
from PyQt5.QtCore import Qt, QObject

from .item_edit import ItemEdit
from ..internal.dict_combo import DictCombo

class SeriesHeaderStack(QWidget):

    def __init__(self, parent, i, s):
        super().__init__()
        self.parent = parent
        ct = self.parent
        dm = ct.parent
        self.col = i
        self.s = s

        self.keep_check = QCheckBox()
        self.keep_check.stack = self
        self.keep_check.row = 0
        self.keep_check.setChecked(s.keep)
        self.keep_check.stateChanged.connect(self.update_keep)
#        self.patch_switch_focus(self.keep_check)
        self.keep_widget = QWidget()
        self.keep_widget.row = 0
        vbox = QVBoxLayout(self.keep_widget)
        vbox.setAlignment(Qt.AlignCenter)
        vbox.setContentsMargins(0, 0, 0, 0)
        vbox.addWidget(self.keep_check)

        self.header_item = QLabel(s.header)
        self.header_item.setStyleSheet('QLabel {padding: 0px 3px 0px 3px;}')
        self.header_item.stack = self
        self.header_item.row = 1
        self.patch_switch_focus(self.header_item)

        self.alias_item = ItemEdit(s.alias, parent)
        self.alias_item.stack = self
        self.alias_item.row = 2
        self.alias_item.home(False)
        self.alias_item.setPlaceholderText(s.header)
        self.alias_item.editingFinished.connect(self.update_alias)
        self.patch_switch_focus(self.alias_item)

        self.type_combo = DictCombo(dm.all_units, s.get_unit_type)
        self.type_combo.stack = self
        self.type_combo.row = 3
        self.type_combo.populate()
        self.type_combo.currentTextChanged.connect(self.type_combo_slot)

        self.patch_switch_focus(self.type_combo)

        self.unit_combo = DictCombo(dm.all_units, s.get_unit_type, s.get_unit)
        self.unit_combo.stack = self
        self.unit_combo.row = 4
        self.unit_combo.populate()
        self.unit_combo.currentTextChanged.connect(self.unit_combo_slot)
        self.patch_switch_focus(self.unit_combo)

    def patch_switch_focus(self, w):
        def appendFocusInEvent(event, self=w):
            type(w).focusInEvent(w, event)
            ct = w.stack.parent
            ct.header_table.setCurrentCell(w.row, w.stack.col)
        w.focusInEvent = appendFocusInEvent

    def update_keep(self, checked):
        ct = self.parent
        dm = ct.parent
        keep_check = QObject.sender(self)
        selected = ct.header_table.selectedIndexes()
        stacks = set([keep_check.stack] + [ct.stacks[i.column()] for i in selected])
        for stack in stacks:
            stack.s.keep = checked
        if ct.hide_unused.isChecked():
            ct.display_header_info()
        else:
            for stack in stacks:
                stack.keep_check.blockSignals(True)
                stack.keep_check.setChecked(checked)
                stack.keep_check.blockSignals(False)
        dm.modified = True

    def type_combo_slot(self, text):
        ct = self.parent
        dm = ct.parent
        stack = QObject.sender(self).stack
        stack.s.unit_type = text
        stack.unit_combo.populate()
        dm.modified = True

    def unit_combo_slot(self, text):
        ct = self.parent
        dm = ct.parent
        stack = QObject.sender(self).stack
        stack.s.unit = text
        dm.modified = True

    def update_alias(self):
        """Updates the alias and scaling factor of series."""
        ct = self.parent
        dm = ct.parent
        item = QObject.sender(self)
        s = item.stack.s
        group = s.group
        alias = item.text().strip()

        def remove_key_by_value(dictionary, value):
            for key in dictionary:
                if dictionary[key] == value:
                    del dictionary[key]
                    break

        accept = True
        if alias != s.alias and alias in group.alias_dict:
            dm.feedback('"{}" is already in use.'
                        'Please choose a different alias.'
                        .format(alias))
            accept = False
        if alias in group.data.columns:
            dm.feedback('"{}" is the name of an original header.'
                        'Please choose a different alias.'
                        .format(alias))
            accept = False
        if accept:
            s.alias = alias
            remove_key_by_value(group.alias_dict, s.header)
            if alias:
                group.alias_dict[alias] = s.header
            dm.modified = True
        else:
            ct.header_table.blockSignals(True)
            item.setText(s.alias)
            ct.header_table.blockSignals(False)
