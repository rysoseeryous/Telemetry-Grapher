# -*- coding: utf-8 -*-
"""q_color_button.py - Contains QColorButton class definition."""

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

from PyQt5.QtWidgets import QPushButton

class QColorButton(QPushButton):
    """Associates unit type with color."""

    def __init__(self, parent, color, unit_type):
        super(QColorButton, self).__init__()
        self.setFixedSize(20,20)
        self.parent = parent
        self.color = color
        self.setStyleSheet("background-color:{};".format(color))
        self.unit_type = unit_type