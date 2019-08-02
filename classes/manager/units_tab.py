# -*- coding: utf-8 -*-
"""units_tab.py - Contains UnitsTab class definition."""

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

from PyQt5.QtWidgets import QWidget, QHBoxLayout, QFormLayout, QCheckBox

from ..internal.unit_tree import UnitTree
from ..internal.unit_model import UnitModel
from ..internal.dict_combo import DictCombo
from ..internal.clarified_table import ClarifiedTable

class UnitsTab(QWidget):

    def __init__(self, parent):
        super().__init__()
        self.parent = parent
        dm = self.parent
        ui = dm.parent

        hbox = QHBoxLayout()
        self.base_model = UnitModel(self, 'Base Units')
        self.base_tree = UnitTree(self, self.base_model, dm.base_units,
                                  L0_edit=False, L0_add=False)
        ui.make_widget_deselectable(self.base_tree)
        hbox.addWidget(self.base_tree)

        self.user_model = UnitModel(self, 'Custom Units')
        self.user_tree = UnitTree(self, self.user_model, dm.user_units)
        ui.make_widget_deselectable(self.user_tree)
        hbox.addWidget(self.user_tree)

        self.clarified_table = ClarifiedTable(self)
        ui.make_widget_deselectable(self.clarified_table)
        hbox.addWidget(self.clarified_table)

        form = QFormLayout()
        self.auto_parse_check = QCheckBox('Automatically parse '
                                          'units from headers')
        self.auto_parse_check.setChecked(ui.auto_parse)
        self.auto_parse_check.stateChanged.connect(self.toggle_auto_parse)
        form.addRow(self.auto_parse_check)

        self.default_type_combo = DictCombo(dm.all_units,
                                            dm.get_default_unit_type)
        self.default_type_combo.populate()
        self.default_type_combo.currentTextChanged.connect(
                self.default_type_combo_slot)
        form.addRow('Default Unit Type', self.default_type_combo)

        self.default_unit_combo = DictCombo(dm.all_units,
                                            dm.get_default_unit_type,
                                            dm.get_default_unit)
        self.default_unit_combo.populate()
        self.default_unit_combo.currentTextChanged.connect(
                self.default_unit_combo_slot)
        form.addRow('Default Unit', self.default_unit_combo)
        hbox.addLayout(form)
        self.setLayout(hbox)

    def toggle_auto_parse(self, checked):
        dm = self.parent
        ui = dm.parent
        ui.auto_parse = checked

    def default_type_combo_slot(self, text):
        dm = self.parent
        dm.default_unit_type = text
        self.default_unit_combo.populate()
        dm.modified = True

    def default_unit_combo_slot(self, text):
        dm = self.parent
        dm.default_unit = text
        dm.modified = True
