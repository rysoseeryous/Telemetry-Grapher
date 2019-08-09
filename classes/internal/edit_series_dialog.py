# -*- coding: utf-8 -*-
"""edit_series_dialog.py - Contains EditSeriesDialog class definition."""

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

from PyQt5.QtWidgets import (QDialog, QFormLayout, QHBoxLayout, QMessageBox,
                             QLabel, QLineEdit, QDoubleSpinBox, QPushButton)
from PyQt5.QtGui import QIcon
from PyQt5.QtCore import Qt

from .dict_combo import DictCombo

class EditSeriesDialog(QDialog):

    def __init__(self, parent, item):
        super().__init__()
        self.parent = parent
        ui = self.parent
        self.item = item
        group_name = item.parent().text(0)
        alias = item.text(0)
        group = ui.all_groups[group_name]
        header = group.get_header(alias)
        s = group.series(header)
        self.s = s
        self.alias = s.alias
        self.unit_type = s.unit_type
        self.unit = s.unit
        self.scale = s.scale
        self.setWindowTitle('Edit Series')
        self.setWindowIcon(QIcon('rc/satellite.png'))

        form = QFormLayout()
        form.addRow('Group:', QLabel(s.group.name))
        form.addRow('Header:', QLabel(s.header))
        self.alias_edit = QLineEdit(s.alias)
        self.alias_edit.setPlaceholderText(s.header)
        self.alias_edit.textChanged.connect(self.update_alias)
        form.addRow('Alias:', self.alias_edit)
        self.type_combo = DictCombo(ui.all_units, self.get_type)
        self.type_combo.populate()
        self.type_combo.currentTextChanged.connect(self.type_combo_slot)
        form.addRow('Unit Type:', self.type_combo)
        self.unit_combo = DictCombo(ui.all_units, self.get_type, self.get_unit)
        self.unit_combo.populate()
        self.unit_combo.currentTextChanged.connect(self.unit_combo_slot)
        form.addRow('Unit:', self.unit_combo)
        self.scale_spinbox = QDoubleSpinBox()
        self.scale_spinbox.setRange(0, 1000)
        self.scale_spinbox.setValue(s.scale)
        self.scale_spinbox.valueChanged.connect(self.update_scale)
        form.addRow('Scale:', self.scale_spinbox)
        form.addRow(QLabel(self.stats()))
        hbox = QHBoxLayout()
        self.accept_button = QPushButton('Save && Exit')
        self.accept_button.clicked.connect(self.save_exit)
        hbox.addWidget(self.accept_button)
        self.reject_button = QPushButton('Cancel')
        self.reject_button.clicked.connect(self.close)
        hbox.addWidget(self.reject_button)
        form.addRow(hbox)
        self.setLayout(form)
        self.setFixedSize(self.sizeHint())

    def update_alias(self, text):
        s = self.s
        alias = text.strip()
        if alias in s.group.alias_dict or alias in s.group.data.columns:
            self.alias_edit.blockSignals(True)
            self.alias_edit.setText(s.alias)
            self.alias_edit.blockSignals(False)
        else:
            self.alias = alias

    def get_type(self):
        return self.unit_type

    def get_unit(self):
        return self.unit

    def type_combo_slot(self, text):
        self.unit_type = text
        self.unit_combo.populate()

    def unit_combo_slot(self, text):
        self.unit = text

    def update_scale(self, value):
        self.scale = value

    def stats(self):
        series = self.s.group.data[self.s.header]
        start = series.index[0].strftime('%Y-%m-%d  %H:%M:%S')
        end = series.index[-1].strftime('%Y-%m-%d  %H:%M:%S')
        idmin = series.idxmin().strftime('%Y-%m-%d  %H:%M:%S')
        idmax = series.idxmax().strftime('%Y-%m-%d  %H:%M:%S')
        stats = 'Series Statistics:\n'
        stats += '    Count:\t {}\n'.format(series.size)
        stats += '    Start:\t {}\n'.format(start)
        stats += '    End:\t {}\n'.format(end)
        stats += '    Min:\t {}\n'.format(series.min())
        stats += '    @\t {}\n'.format(idmin)
        stats += '    Max:\t {}\n'.format(series.max())
        stats += '    @\t {}\n'.format(idmax)
#        stats += '    Mean:\t{}\n'.format(series.mean())
#        stats += '    Median:\t{}'.format(series.median())
        return stats

    def apply_changes(self):
        s = self.s
        s.alias = self.alias
        s.unit_type = self.unit_type
        s.unit = self.unit
        s.scale = self.scale
        if s.alias:
            self.item.setText(0, s.alias)
        else:
            self.item.setText(0, s.header)

    def save_exit(self):
        ui = self.parent
        sd = ui.series_display
        cf = ui.get_current_figure()
        s = self.s

#        known_aliases = [alias for alias in s.group.alias_dict.keys()]
        for alias in s.group.alias_dict:
            if s.group.alias_dict[alias] == s.header:
                del s.group.alias_dict[alias]
                if self.alias:
                    s.group.alias_dict[self.alias] = s.header
                break

        if self.item.treeWidget() is sd.available:
            aliases = cf.available_data[s.group.name]
            i = aliases.index(s.alias)
            self.apply_changes()
            aliases[i] = s.alias
        elif self.item.treeWidget() is sd.plotted:
            sp = cf.current_sps[0]
            if s.unit_type != self.unit_type or s.unit != self.unit:
                sp.remove({s.group.name: [s.alias]})
            else:
#                sp.contents.remove({s.group.name: [s.alias]})
                for ax in sp.axes:
                    try:
                        ax.contents.remove({s.group.name: [s.alias]})
                    except ValueError:
                        pass
            self.apply_changes()
            if s.alias:
                sp.add({s.group.name: [s.alias]})
            else:
                sp.add({s.group.name: [s.header]})
        cf.replot()
        cf.update_gridspec()
        cf.draw()
        self.close()

    def closeEvent(self, event):
        ui = self.parent
        s = self.s
        c1 = self.alias != s.alias
        c2 = self.unit_type != s.unit_type
        c3 = self.unit != s.unit
        c4 = self.scale != s.scale
        if any([c1, c2, c3, c4]):
            result = ui.popup('Discard changes?')
            if result == QMessageBox.Cancel:
                event.ignore()
            elif result == QMessageBox.Save:
                self.save_exit()
            else:
                event.accept()
        else:
            event.accept()

    def keyPressEvent(self, event):
        """Enables dialog closure by escape key."""
        if event.key() == Qt.Key_Escape:
            self.close()
