# -*- coding: utf-8 -*-
"""subplot_manager.py - Contains SubplotManager class definition."""

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

from copy import copy
import numpy as np
import matplotlib.pyplot as plt
from .contents_dict import ContentsDict

class SubplotManager():
    """Wrapper around subplot object (host).
    Keeps track of contents and settings of each subplot."""

    def __init__(self, parent, host, contents=None, index=None):
        self.parent = parent
        self.patch_ax(host)
        self.axes = [host]
        if contents is None:
            self.contents = ContentsDict()
        else:
            self.contents = contents
        self.index = index
        self.color_coord = False
        self.legend_on = False
        self.legend = None
        self.location = 'Outside Right'
        self.ncols = 1
        self.legend_units = True

        self.lines = []
        self.labels = []

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
            ymin = min([min(line.get_ydata()) for line in self.lines])
            ymax = max([max(line.get_ydata()) for line in self.lines])
            return ymin, ymax
        ax.get_data_extents = get_data_extents

    def host(self):
        return self.axes[0]

    def get_axes(self, unit_type, unit):
        for ax in self.axes:
            if ax._id == (unit_type, unit):
                return ax
        if len(self.axes) == 1 and not self.host().contents:
            ax = self.host()
            ax.set_id(unit_type, unit)
            return ax
        return None

    def add(self, contents):
        """Adds contents to sp.contents and distributes them into axes."""
        sp = self
        ui = self.parent
        af = ui.axes_frame
        sp.contents.add(contents)
        for group_name in contents:
            group = ui.groups[group_name]
            for alias in contents[group_name]:
                header = group.get_header(alias)
                s = group.series(header)
                ax = self.get_axes(s.unit_type, s.unit)
                if ax is None:
                    par = af.fig.add_subplot(af.gs[sp.index])
                    sp.patch_ax(par)
                    par.set_id(s.unit_type, s.unit)
                    sp.axes.append(par)
                    ax = par
                ax.contents.add({group_name: [alias]})

    def remove(self, contents):
        """Removes contents from sp.contents and from their axes."""
        sp = self
        ui = self.parent
        af = ui.axes_frame
        sp.contents.remove(contents)
        for group_name in contents:
            group = ui.groups[group_name]
            for alias in contents[group_name]:
                header = group.get_header(alias)
                s = group.series(header)
                ax = self.get_axes(s.unit_type, s.unit)
                ax.contents.remove({group_name: [alias]})
        for ax in [ax for ax in sp.axes if not ax.contents]:
            ax.remove()
            sp.axes.remove(ax)
        if not sp.axes:
            ax = af.fig.add_subplot(111)
            sp.patch_ax(ax)
            ax.set_id()
            sp.axes = [ax]
            plt.setp(ax.spines.values(),
                     linewidth=ui.highlight['True'])

    def plot(self, skeleton=False):
        """Plots all data in each axis according to current style settings."""
        sp = self
        ui = self.parent
        af = ui.axes_frame
        fs = ui.figure_settings

        color_index = 0
        style_dict = {}
        sp.lines = []
        sp.labels = []
        for ax in sp.axes:
            ax.clear()
            ax.patch.set_visible(False)
#            lines = [line for line in ax.lines]
#            for line in lines:
#                .remove(line)
            for group_name in ax.contents:
                group = ui.groups[group_name]
                df = group.data
                subdf = df[(df.index >= af.start) & (df.index <= af.end)]
                for alias in ax.contents[group_name]:
                    header = group.get_header(copy(alias))
                    s = group.series(header)
                    data = subdf[header]
                    n = len(data.index)
                    d = fs.density.value()/100
                    thin = np.linspace(0, n-1, num=int(n*d), dtype=int)
                    data = data.iloc[thin]
                    data = data.map(lambda x: x*s.scale)

                    if sp.color_coord:
                        if s.unit_type not in style_dict:
                            style_dict[s.unit_type] = 0
                        counter = style_dict[s.unit_type]
                        style = fs.markers[counter%len(fs.markers)]
                        style_dict[s.unit_type] += 1
                        color = fs.color_dict[s.unit_type]
                        labelcolor = color
                    else:
                        style = 'o'
                        color='C'+str(color_index%10)
                        color_index += 1
                        labelcolor = ui.current_rcs['axes.labelcolor']
                    if fs.scatter.isChecked():
                        line, = ax.plot(data, style, color=color,
                                        markersize=fs.dot_size.value(),
                                        linestyle='None')
                    else:
                        line, = ax.plot(data, color=color)
                    sp.lines.append(line)
                    sp.labels.append((s.alias, s.unit))
            if ax.contents:
                ax.set_ylabel(ax.label(),
                              fontsize=fs.label_size.value(),
                              color=labelcolor)
                ax.tick_params(axis='y', labelcolor=labelcolor)
                ax.relim()
                ax.autoscale(axis='x')
                if ax.auto_limits:
                    ax.autoscale(axis='y')
                else:
                    ax.set_ylim(ax.custom_limits)
                if ax.log:
                    ax.set_yscale('log')

        sp.arrange_axes()
        af.format_axes()
        af.update_toolbars()

    def arrange_axes(self):
        sp = self
        ui = self.parent
        fs = ui.figure_settings
        sp.host().set_host()
        offset = fs.axis_offset.value()
        for i, ax in enumerate(sp.axes[1:]):
            ax.set_par(offset=1+offset*(i))

    def show_legend(self):
        sp = self
        ui = self.parent
        fs = ui.figure_settings
        lt = ui.legend_toolbar
        if sp.legend is not None:
            sp.legend.remove()
        if sp.legend_on and sp.contents:
            if sp.location == 'Outside Right':
                offset = fs.axis_offset.value()
                npars = len(sp.axes[1:])
                bbox = (1+offset*npars, 0.5)
            elif sp.location == 'Outside Top':
                bbox = (0.5, 1)
            else:
                bbox = (0, 0, 1, 1)
            if sp.legend_units:
                labels = ['{} [{}]'.format(*x) for x in sp.labels]
            else:
                labels = [x[0] for x in sp.labels]

            sp.legend = sp.host().legend(sp.lines, labels,
                   loc=lt.locations[sp.location],
                   bbox_to_anchor=bbox,
                   ncol=sp.ncols,
                   framealpha=1.0)
            for handle in sp.legend.legendHandles:
                handle._legmarker.set_markersize(4)
