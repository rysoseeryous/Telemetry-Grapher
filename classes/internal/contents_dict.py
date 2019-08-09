# -*- coding: utf-8 -*-
"""contents_dict.py - Contains ContentsDict class definition."""

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

class ContentsDict(dict):
    """Hierarchical dictionary.
    {group1: aliases1, group2: aliases2...}
    group -> string
    aliases -> list of strings"""

    def __init__(self, *args):
        dict.__init__(self, args)

    def add(self, to_add):
        for group in to_add:
            if group in self:
                self[group].extend(to_add[group])
            else:
                self[group] = to_add[group]

    def remove(self, to_remove):
        for group in to_remove:
#            if group in contents:  # this should always be true
            for alias in to_remove[group]:
                self[group].remove(alias)
            if not self[group]:
                del self[group]
