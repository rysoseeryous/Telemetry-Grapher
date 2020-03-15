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

import datetime as dt
from copy import copy, deepcopy
import numpy as np
import matplotlib.pyplot as plt
from telemetry_grapher.classes.internal.contents_dict import ContentsDict
from telemetry_grapher.classes.internal.axes_patch_functions import patch_ax, patch_ygrid_proxy

class SubplotManager():
    """Wrapper around subplot object (host).
    Keeps track of contents and settings of each subplot."""

    def __init__(self, parent, host, index):
        self.parent = parent
        cf = self.parent
        patch_ax(self, host)
        self.axes = [host]

        self.index = index
        self.color_coord = False
        self.legend_on = False
        self.legend = None
        self.location = 'Outside Right'
        self.ncols = 1
        self.legend_units = True
        self.lines = []
        self.labels = []

        self.ygrid_proxy = cf.fig.add_subplot(111)
        self.ygrid_proxy.set_zorder(-1)
        patch_ygrid_proxy(self, self.ygrid_proxy)

    def host(self):
        return self.axes[0]

    @property
    def contents(self):
        contents = ContentsDict()
        for ax in self.axes:
            contents.add(deepcopy(ax.contents))
        return contents

    def get_axes(self, unit_type, unit):
        for ax in self.axes:
            if ax._id == (unit_type, unit):
                return ax
        if len(self.axes) == 1 and not self.host().contents:
            ax = self.host()
            ax.set_id(unit_type, unit)
            return ax
        return None

    def add(self, contents, cf=None):
        """Adds contents to self.contents and distributes them into axes."""
        if cf is None:
            cf = self.parent
        ui = cf.parent
        for group_name in contents:
            group = ui.all_groups[group_name]
            for alias in contents[group_name]:
                header = group.get_header(alias)
                s = group.series(header)
                ax = self.get_axes(s.unit_type, s.unit)
                if ax is None:
                    par = cf.fig.add_subplot(111)
                    patch_ax(self, par)
                    par.set_id(s.unit_type, s.unit)
                    self.axes.append(par)
                    ax = par
                ax.contents.add({group_name: [alias]})

    def remove(self, contents, cf=None):
        """Removes contents from self.contents and from their axes."""
        if cf is None:
            cf = self.parent
        ui = cf.parent
        for group_name in contents:
            group = ui.all_groups[group_name]
            for alias in contents[group_name]:
                header = group.get_header(alias)
                s = group.series(header)
                ax = self.get_axes(s.unit_type, s.unit)
                ax.contents.remove({group_name: [alias]})
        for ax in [ax for ax in self.axes if not ax.contents]:
            ax.remove()
            self.axes.remove(ax)
        if not self.axes:
            ax = cf.fig.add_subplot(111)
            patch_ax(self, ax)
            ax.set_id()
            self.axes = [ax]
            if self in cf.current_sps:
                plt.setp(ax.spines.values(),
                         linewidth=ui.highlight[True])

    def plot(self, skeleton=False):
        """Plots all data in each axis according to current style settings."""
        cf = self.parent
        ui = cf.parent

        color_index = 0
        style_dict = {}
        self.lines = []
        self.labels = []
        for ax in self.axes:
            ax.clear()
            ax.patch.set_visible(False)
            for group_name in ax.contents:
                group = ui.all_groups[group_name]
                df = group.data
                subdf = df[(df.index >= cf.start) & (df.index <= cf.end)]
                for alias in ax.contents[group_name]:
                    header = group.get_header(copy(alias))
                    s = group.series(header)
                    data = subdf[header]
                    n = len(data.index)
                    d = cf.density/100
                    thin = np.linspace(0, n-1, num=int(n*d), dtype=int)
                    data = data.iloc[thin]
                    data = data.map(lambda x: x*s.scale)

                    if self.color_coord:
                        if s.unit_type not in style_dict:
                            style_dict[s.unit_type] = 0
                        counter = style_dict[s.unit_type]
                        style = ui.markers[counter%len(ui.markers)]
                        style_dict[s.unit_type] += 1
                        if s.unit_type:
                            color = ui.color_dict[s.unit_type]
                        else:
                            color = ui.current_rcs['axes.labelcolor']
                        labelcolor = color
                    else:
                        style = 'o'
                        color='C'+str(color_index%10)
                        color_index += 1
                        labelcolor = ui.current_rcs['axes.labelcolor']
                    if cf.scatter:
                        line, = ax.plot(data, style, color=color,
                                        markersize=cf.dot_size,
                                        linestyle='None')
                    else:
                        line, = ax.plot(data, color=color)
                    self.lines.append(line)
                    self.labels.append((s.label, s.unit))
#                    if s.alias:
#                        self.labels.append((s.alias, s.unit))
#                    else:
#                        self.labels.append((header, s.unit))
            if ax.contents:
                ax.set_ylabel(ax.label(),
                              fontsize=cf.label_size,
                              color=labelcolor)
                ax.tick_params(axis='y', labelcolor=labelcolor)
                ax.relim()
                seconds = (cf.end - cf.start).total_seconds()*cf.x_margin
                offset = dt.timedelta(seconds=seconds)
                ax.set_xlim([cf.start-offset, cf.end+offset])
                if ax.auto_limits:
                    ax.autoscale(axis='y')
                else:
                    ax.set_ylim(ax.custom_limits)
                if ax.log:
                    ax.set_yscale('log')
                else:
                    ax.set_yscale('linear')

        self.arrange_axes()
        cf.format_axes()
        cf.update_toolbars()

    def arrange_axes(self):
        cf = self.parent
        self.host().set_host()
        self.host().set_zorder(0)
        offset = cf.axis_offset
        for i, ax in enumerate(self.axes[1:]):
            ax.set_par(offset=1+offset*(i))
            ax.set_zorder(i+1)

    def show_legend(self):
        cf = self.parent
        ui = cf.parent
        if self.legend is not None:
            self.legend.remove()
        if self.legend_on and self.contents:
            if self.location == 'Outside Right':
                offset = cf.axis_offset
                npars = len(self.axes[1:])
                bbox = (1+offset*npars, 0.5)
            elif self.location == 'Outside Top':
                bbox = (0.5, 1)
            else:
                bbox = (0, 0, 1, 1)
            if self.legend_units:
                labels = ['{} [{}]'.format(*x) for x in self.labels]
            else:
                labels = [x[0] for x in self.labels]
            self.legend = self.axes[-1].legend(self.lines, labels,
                   loc=ui.locations[self.location],
                   bbox_to_anchor=bbox,
                   ncol=self.ncols,
                   framealpha=1.0)
            self.legend.set_zorder(len(self.labels)+1)
            for handle in self.legend.legendHandles:
                handle._legmarker.set_markersize(4)
        else:
            self.legend = None
