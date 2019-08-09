# -*- coding: utf-8 -*-
"""data_manager.py - Contains DataManager class definition."""

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

import re
from copy import copy, deepcopy

from PyQt5.QtWidgets import (QDialog, QMessageBox, QWidget,
                             QDialogButtonBox, QVBoxLayout, QSplitter,
                             QTabWidget, QTextEdit, QLabel)
from PyQt5.QtGui import QIcon
from PyQt5.QtCore import Qt

from .groups_tab import GroupsTab
from .configure_tab import ConfigureTab
from .units_tab import UnitsTab
from ..internal.contents_dict import ContentsDict

class DataManager(QDialog):
    """Manages the importing of data and configuration of data groups."""

    def __init__(self, parent):
        self.debug = False

        super().__init__()
        self.parent = parent
        ui = self.parent
        self.setWindowTitle('Data Manager')
        self.setWindowIcon(QIcon('rc/satellite.png'))
        self.all_groups = deepcopy(ui.all_groups)
        self.group_rename = {name:[name] for name in self.all_groups}
        self.fig_groups = {}
        self.unit_clarify = copy(ui.unit_clarify)
        self.user_units = deepcopy(ui.user_units)
        self.base_units = deepcopy(ui.base_units)
        self.default_unit_type = deepcopy(ui.default_unit_type)
        self.default_unit = deepcopy(ui.default_unit)
        for cf in ui.all_figures():
            self.fig_groups[cf.title] = copy(cf.groups)
        self.modified = False
        self.resize(1000, 500)
        splitter = QSplitter(Qt.Vertical)

        self.tab_base = QTabWidget()
        self.groups_tab = GroupsTab(self)
        self.configure_tab = ConfigureTab(self)
        self.units_tab = UnitsTab(self)
        self.tab_base.addTab(self.groups_tab, 'File Grouping')
        self.tab_base.addTab(self.configure_tab, 'Series Configuration')
        self.tab_base.addTab(self.units_tab, 'Unit Settings')
        splitter.addWidget(self.tab_base)

        self.log_base = QWidget()
        vbox = QVBoxLayout()
        vbox.addWidget(QLabel('Message Log:'))
        self.message_log = QTextEdit()
        self.message_log.setReadOnly(True)
        vbox.addWidget(self.message_log)
        self.log_base.setLayout(vbox)
        splitter.addWidget(self.log_base)

        vbox = QVBoxLayout()
        self.buttonBox = QDialogButtonBox()
        self.buttonBox.setStandardButtons(QDialogButtonBox.Save |
                                          QDialogButtonBox.Close)
        self.buttonBox.accepted.connect(self.save_changes)
        self.buttonBox.rejected.connect(self.close)

        vbox.addWidget(splitter)
        vbox.addWidget(self.buttonBox)
        self.setLayout(vbox)

        self.groups_tab.search_dir()
        if self.debug:
            self.groups_tab.import_group() #!!! Delete Later
            self.save_changes()

    def get_default_unit_type(self):
        return self.default_unit_type

    def get_default_unit(self):
        return self.default_unit

    def unit_combos(self):
        ut = self.units_tab
        ct = self.configure_tab
        combos = [ut.default_unit_combo]
        combos.extend([stack.unit_combo for stack in ct.stacks])
        combos.extend(ut.clarified_table.combos())
        return combos

    def type_combos(self):
        ut = self.units_tab
        ct = self.configure_tab
        combos = [ut.default_type_combo]
        combos.extend([stack.type_combo for stack in ct.stacks])
        return combos

    def parse_unit(self, header):
        """Parses unit information from header.
        Returns characters between last instance of square brackets."""
        # matches any characters between square brackets
        regex = re.compile('\[[^\[]*?\]')
        parsed = ''
        for match in re.finditer(regex, header):  # as last match
            parsed = match.group(0)[1:-1]  # strip brackets
        return parsed

    def interpret_unit(self, unit):
        """Tries to interpret unit.
        - Run unit through self.unit_clarify dictionary.
        - Check if unit can be associated with a unit type.
        - If so, return unit, otherwise return default unit.
        - Boolean indicates whether or not the unit was interpretable."""
        if unit:
            if unit in self.unit_clarify:
                unit = self.unit_clarify[unit]
            unit_type = self.get_unit_type(unit)
        else:
            unit = self.default_unit
            unit_type = self.default_unit_type
        return unit, unit_type, bool(unit and unit_type)

    def get_unit_type(self, unit):
        """Returns unit type of given unit.
        Priority is first given to user-defined units, then base unit types.
        If unit is not recognized in either dictionary,
        then the default unit type is returned."""
        # check user units first
        for unit_type in self.user_units:
            if unit in self.user_units[unit_type]:
                return unit_type
        # if not found, check hard-coded base_units
        for unit_type in self.base_units:
            if unit in self.base_units[unit_type]:
                return unit_type
        # else, return default unit type
        return self.default_unit_type

    def all_units(self):
        return {**self.user_units, **self.base_units}

    def keyPressEvent(self, event):
        """Close dialog from escape key."""
        if event.key() == Qt.Key_Escape:
            self.close()

    def feedback(self, message, mode='line'):
        """Adds message to message log as one line.
        Set mode=overwrite to overwrite the last line in the log.
        Set mode=append to append the last line in the log."""
        if self.message_log.toPlainText():
            if mode == 'line':
                self.message_log.setText(
                        self.message_log.toPlainText() + '\n' + message)
            elif mode == 'append':
                self.message_log.setText(
                        self.message_log.toPlainText() + message)
            elif mode == 'overwrite':
                current_text = self.message_log.toPlainText()
                self.message_log.setText(
                        current_text[:current_text.rfind('\n')+1] + message)
        else:
            self.message_log.setText(message)
        v_scrollbar = self.message_log.verticalScrollBar()
        v_scrollbar.setValue(v_scrollbar.maximum())

    def save_changes(self):
        """Saves groups created in Data Manager dialog to main window.
        Maps existing data to new data."""

        if not self.modified: return
        ui = self.parent
        sd = ui.series_display
        fs = ui.figure_settings

        ui.unit_clarify = self.unit_clarify
        ui.user_units = self.user_units
        ui.base_units = self.base_units
        ui.default_unit_type = self.default_unit_type
        ui.default_unit = self.default_unit

        header_ref = deepcopy(ui.all_groups)
        ui.all_groups = self.all_groups

        for cf in ui.all_figures():
            # Get new group: alias information from self.fig_groups
            cf.groups = self.fig_groups[cf.title]
            dm_contents = ui.groups_to_contents(cf.groups)
            for sp in cf.subplots:
                new_contents = ContentsDict()
                for sp_name in copy(tuple(sp.contents.keys())):
                    # Rename/delete groups in subplots first
                    try:
                        dm_name = self.group_rename[sp_name][-1]
                    except KeyError:
#                        del sp.contents[sp_name]
                        for ax in sp.axes:
                            if sp_name in ax.contents: del ax.contents[sp_name]
                    else:
                        group = ui.all_groups[dm_name]
                        new_contents[dm_name] = []
                        sp_headers = [header_ref[sp_name].get_header(alias) for
                                      alias in sp.contents[sp_name]]
                        for s in group.series(lambda s: s.keep):
                            if s.header in sp_headers:
                                if s.alias:
                                    new_contents[dm_name].append(s.alias)
                                    dm_contents[dm_name].remove(s.alias)
                                else:
                                    new_contents[dm_name].append(s.header)
                                    dm_contents[dm_name].remove(s.header)
                        if not dm_contents[dm_name]: del dm_contents[dm_name]
                        if not new_contents[dm_name]: del new_contents[dm_name]
                if new_contents:
#                    sp.contents.clear()
                    for ax in sp.axes:
                        ax.contents.clear()
                    sp.add(new_contents, cf)
                    for ax in [ax for ax in sp.axes if not ax.contents]:
                        ax.remove()
                        sp.axes.remove(ax)
                else:
                    sp.remove(sp.contents, cf)
            # Dump everything else into cf.available_data
            cf.available_data = dm_contents
            cf.update_gridspec()
            fs.cap_start_end(cf)
            cf.draw()

        # Reset group_rename
        self.group_rename = {name:[name] for name in ui.all_groups}
        cf = ui.get_current_figure()
        sd.populate_tree('available', cf.available_data)
        sd.plotted.clear()
        if len(cf.current_sps) == 1:
            sp = cf.current_sps[0]
            sd.populate_tree('plotted', sp.contents)
        fs.update_unit_table()
        self.feedback('Saved data to main window.')
        self.modified = False

    def closeEvent(self, event):
        """Asks user to save changes before exiting."""
        ui = self.parent
        if self.modified:
            choice = ui.popup('Discard changes?', title='Exiting Data Manager')
            if choice == QMessageBox.Cancel:
                event.ignore()
                return
            elif choice == QMessageBox.Save:
                self.save_changes()
        event.accept()
