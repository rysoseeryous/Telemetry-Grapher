# -*- coding: utf-8 -*-
"""series.py - Contains Series class definition."""

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

class Series():

    def __init__(self, parent, header, alias, unit=None, unit_type=None):
        self.parent = parent
        self.header = header
        self.alias = alias
        self.unit_type = unit_type
        self.unit = unit
        self.scale = 1.0
        self.keep = True
        self.color = None

    def summarize(self):
        return ('Header: '+str(self.header),
                'Alias: '+str(self.alias),
                'Unit Type: '+str(self.unit_type),
                'Unit: '+str(self.unit),
                'Scale: '+str(self.scale),
                'Keep: '+str(self.keep))