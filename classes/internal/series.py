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

    def __init__(self, group, header, alias, unit_type=None, unit=None):
        self.group = group
        self.header = header
        self.alias = alias
        if unit_type is None:
            unit_type = ''
        self.unit_type = unit_type
        if unit is None:
            unit = ''
        self.unit = unit
        self.scale = 1.0
        self.keep = True
        self.color = None
        
    @property
    def label(self):
        if self.alias:
            return self.alias
        else:
            return self.header

    def get_unit_type(self):
        return self.unit_type

    def get_unit(self):
        return self.unit

    def summarize(self):
        return ('Header: '+str(self.header),
                'Alias: '+str(self.alias),
                'Unit Type: '+str(self.unit_type),
                'Unit: '+str(self.unit),
                'Scale: '+str(self.scale),
                'Keep: '+str(self.keep))