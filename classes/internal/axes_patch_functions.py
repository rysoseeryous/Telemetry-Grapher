# -*- coding: utf-8 -*-
"""axes_patch_functions.py - Contains monkey patches for
secondary axes and ygrid proxy axes."""

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

from math import log10
import numpy as np
import matplotlib.pyplot as plt

from telemetry_grapher.classes.internal.contents_dict import ContentsDict

def patch_ax(self, ax):
    ax.parent = self
    ax.contents = ContentsDict()
    ax.color = 'k'
    ax.set_adjustable('datalim')
    ax.patch.set_visible(False)

    ax.log = False
    ax.auto_limits = True
    ax.custom_limits = []

    def set_id(unit_type=None, unit=None, self=ax):
        self.unit_type = unit_type
        self.unit = unit
        self._id = (unit_type, unit)
    ax.set_id = set_id
    ax.set_id()

    def label(self=ax):
        # in the future, use labels instead of (type, unit) _id
        if self.unit_type:
            if self.unit:
                ylabel = '{} [{}]'.format(self.unit_type, self.unit)
            else:
                ylabel = self.unit_type
        else:
            if self.unit:
                ylabel = '[{}]'.format(self.unit)
            else:
                ylabel = ''
        return ylabel
    ax.label = label

    def set_par(offset=0.0, self=ax):
        """see https://matplotlib.org/gallery/
        ticks_and_spines/multiple_yaxis_with_spines.html"""
        self.yaxis.tick_right()
        self.yaxis.set_label_position('right')
        for spine in self.spines.values():
            spine.set_visible(False)
        self.spines['right'].set_visible(True)
        self.spines['right'].set_position(('axes', offset))
    ax.set_par = set_par

    def set_host(self=ax):
        """see https://matplotlib.org/gallery/
        ticks_and_spines/multiple_yaxis_with_spines.html"""
        self.yaxis.tick_left()
        self.yaxis.set_label_position('left')
        for spine in self.spines.values():
            spine.set_visible(True)
        self.spines['right'].set_position(('axes', 1.0))
    ax.set_host = set_host

    def get_data_extents(self=ax):
        try:
            ymin = min([min(line.get_ydata()) for line in self.lines])
            ymax = max([max(line.get_ydata()) for line in self.lines])
            return ymin, ymax
        except ValueError:
            return 0, 0
    ax.get_data_extents = get_data_extents


def patch_ygrid_proxy(self, ygp):
    ygp.parent = self
    ygp.patch.set_visible(False)
    ygp.set_frame_on(False)
    ygp.xaxis.set_visible(False)
    ygp.yaxis.set_visible(False)

    def mock_gridlines(ax, which='both', linestyle=None, self=ygp):
        y0, y1 = ax.yaxis.get_view_interval()
        M_locs = np.clip(ax.yaxis.get_majorticklocs(), y0, y1)
        m_locs = np.clip(ax.yaxis.get_minorticklocs(), y0, y1)
        if which=='both':
            locs = list(M_locs) + list(m_locs)
        elif which=='major':
            locs = M_locs
        elif which=='minor':
            locs = m_locs
        if ax.log:
            z0, z1 = log10(min(locs)), log10(max(locs))
            normalized = [(log10(loc) - z0)/(z1 - z0) for loc in locs]
        else:
            normalized = [(loc - y0)/(y1 - y0) for loc in locs]
        for loc in set(normalized):
            ygp.axhline(loc,
                        color=plt.rcParams['grid.color'],
                        linestyle=linestyle,
                        linewidth=0.5)
    ygp.mock_gridlines = mock_gridlines

