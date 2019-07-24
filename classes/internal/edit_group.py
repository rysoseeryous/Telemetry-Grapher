# -*- coding: utf-8 -*-
"""edit_group.py - Contains EditGroup class definition."""

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

from PyQt5.QtWidgets import QDialog, QGridLayout, QLineEdit, QPushButton
from PyQt5.QtCore import Qt

class EditGroup(QDialog):

    def __init__(self, parent, group_name):
        super().__init__()
        self.setModal(True)
        self.parent = parent
        self.group_name = group_name
        self.setWindowTitle('Edit Group')

        grid = QGridLayout()
        self.name = QLineEdit(group_name)
        self.name.setPlaceholderText('Group name')
        self.name.returnPressed.connect(self.accept)
        grid.addWidget(self.name, 0, 0, 1, 3)
        self.delete_button = QPushButton('Delete Group')
        self.delete_button.clicked.connect(self.delete_group)
        grid.addWidget(self.delete_button, 1, 0)
        self.ok_button = QPushButton('OK')
        self.ok_button.clicked.connect(self.accept)
        grid.addWidget(self.ok_button)
        self.cancel_button = QPushButton('Cancel')
        self.cancel_button.clicked.connect(self.reject)
        grid.addWidget(self.cancel_button)
        self.setLayout(grid)
        self.delete = False

    def keyPressEvent(self, event):
        """Close dialog from escape key."""
        if event.key() == Qt.Key_Escape:
            self.close()

    def delete_group(self):
        gt = self.parent
        dm = gt.parent
        ui = dm.parent
        ok = ui.popup('Delete group "{}"?'.format(self.group_name),
                      mode='confirm')
        if ok:
            self.delete = True
            self.reject()
        else:
            return