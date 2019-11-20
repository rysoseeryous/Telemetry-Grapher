# -*- coding: utf-8 -*-
"""group.py - Contains Group class definition."""

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

from telemetry_grapher.classes.internal.series import Series

class Group():

    def __init__(self, df, name):
        self.name = name
        self.data = df
        self.series_dict = {header: Series(self, header, '')
                            for header in self.data.columns}
        self.alias_dict = {}
#EG: ui.groups[name].series(header).alias

    def series(self, which=None):
        """Returns all, some, or one Series objects."""
        if which is None:
            return [s for s in self.series_dict.values()]
        else:
            try:
                return self.series_dict[which]
            except TypeError:
                return [self.series_dict[header] for header in which]
            except KeyError:
                try:
                    return [s for s in self.series_dict.values() if which(s)]
                except TypeError:
                    raise KeyError('"{}" is not a valid series reference'
                                   .format(which))

    def get_header(self, alias):
        """Returns original header of alias."""
        try:
            return self.alias_dict[alias]
        except KeyError:
            return alias

    def summarize(self):
        print('Headers')
        for series in self.series():
            print('\t{}\n\t\t{}'.format(series.header, series.summarize()))
        print('\nAssigned Aliases')
        print('\t{}'.format(self.alias_dict.keys()))