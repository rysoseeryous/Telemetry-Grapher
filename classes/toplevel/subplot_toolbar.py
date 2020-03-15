# -*- coding: utf-8 -*-
"""subplot_toolbar.py - Contains SubplotToolbar class definition."""

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

import math
import functools
import itertools
from copy import copy, deepcopy
import matplotlib.pyplot as plt

from PyQt5.QtWidgets import QToolBar, QAction
from PyQt5.QtCore import QObject

from telemetry_grapher.classes.internal.subplot_manager import SubplotManager

class SubplotToolbar(QToolBar):

    def __init__(self, title, parent):
        super().__init__(title)
        self.parent = parent

        self.insert = QAction('insert', self)
        self.insert.setToolTip('Insert Subplot')
        self.insert.triggered.connect(self.insert_subplot)
        self.addAction(self.insert)

        self.delete = QAction('delete', self)
        self.delete.setToolTip('Delete Subplot')
        self.delete.triggered.connect(self.delete_subplot)
        self.addAction(self.delete)

        self.clear = QAction('clear', self)
        self.clear.setToolTip('Clear Subplot')
        self.clear.triggered.connect(self.clear_subplot)
        self.addAction(self.clear)

        self.cycle = QAction('cycle', self)
        self.cycle.setToolTip('Cycle Axes')
        self.cycle.setEnabled(False)
        self.cycle.triggered.connect(self.cycle_subplot)
        self.addAction(self.cycle)

        self.reorder_up = QAction('up', self)
        self.reorder_up.setToolTip('Promote Subplot')
        self.reorder_up.triggered.connect(self.reorder)
        self.addAction(self.reorder_up)

        self.reorder_down = QAction('down', self)
        self.reorder_down.setToolTip('Demote Subplot')
        self.reorder_down.triggered.connect(self.reorder)
        self.addAction(self.reorder_down)

    def insert_subplot(self):
        """Inserts blank subplot below selected subplot."""
        ui = self.parent
        cf = ui.get_current_figure()
        fs = ui.figure_settings
        if len(cf.current_sps) == 1:
            idx = cf.current_sps[0].index
        else:
            idx = cf.nplots()-1
        weights = cf.weights()
        weights.insert(idx+1, 1)
        nplots = cf.nplots() + 1
        ax = cf.fig.add_subplot(111)
        cf.subplots.insert(idx+1, SubplotManager(cf, ax, idx+1))
        fs.weights_edit.setText(str(weights))
        cf.update_gridspec(nplots, weights)
        cf.format_axes()
        cf.draw()

    def delete_subplot(self):
        """Deletes selected subplot(s) and returns contents to available."""
        ui = self.parent
        cf = ui.get_current_figure()
        fs = ui.figure_settings
        sd = ui.series_display
        nplots = cf.nplots()
        weights = cf.weights()
        print(len(cf.subplots))
        for i in reversed([sp.index for sp in cf.current_sps]):
            # add contents back into available tree
            sp = cf.subplots[i]
            cf.available_data.add(deepcopy(sp.contents))
            if nplots == 1:
                sp.remove(deepcopy(sp.contents))
                weights = [1]
            else:
                for ax in sp.axes: ax.remove()
                del cf.subplots[i]
                del weights[i]
                nplots -= 1
            sp.ygrid_proxy.remove()
        sd.populate_tree('available', cf.available_data)
        cf.select_subplot(None, force_select=[])
        g = functools.reduce(math.gcd, weights)
        # simplify weights by their greatest common denominator
        # (eg [2,2,4] -> [1,1,2])
        weights = [x//g for x in weights]
        fs.weights_edit.setText(str(weights))
        cf.update_gridspec(nplots, weights)
        cf.format_axes()
        cf.draw()

    def clear_subplot(self):
        """Clears selected subplots.
        Adds selected subplots' contents back into available tree."""
        ui = self.parent
        cf = ui.get_current_figure()
        sd = ui.series_display
        for sp in cf.current_sps:
            cf.available_data.add((sp.contents))
            sp.remove(deepcopy(sp.contents))
        sd.populate_tree('available', cf.available_data)
        cf.select_subplot(None, force_select=copy(cf.current_sps))
        cf.update_gridspec()
        cf.format_axes()
        cf.draw()

    def cycle_subplot(self):
        """Cycles through unit order permutations of selected subplot(s)."""
        ui = self.parent
        cf = ui.get_current_figure()
        for sp in cf.current_sps:
            plt.setp(sp.host().spines.values(),
                     linewidth=ui.highlight[False])
            ids = [ax._id for ax in sp.axes]
            sorted_perms = sorted(itertools.permutations(ids))
            perms = [list(p) for p in sorted_perms]
            i = perms.index(ids)
            new_ids = perms[(i+1)%len(perms)]
            sp.axes = [sp.get_axes(*_id) for _id in new_ids]
            plt.setp(sp.host().spines.values(),
                     linewidth=ui.highlight[True])
        cf.replot()
        cf.format_axes()
        cf.draw()

    def reorder(self):
        """Reorders selected subplot up or down."""
        ui = self.parent
        cf = ui.get_current_figure()
        fs = ui.figure_settings
        sp = cf.current_sps[0]
        i = sp.index
        caller = QObject.sender(self)
        if caller == self.reorder_up:
            j = i-1
        if caller == self.reorder_down:
            j = i+1
        nplots = cf.nplots()
        # if can be moved up/down
        if 0 <= j < nplots:
            weights = cf.weights()
            weights.insert(j, weights.pop(i))
            cf.subplots.insert(j, cf.subplots.pop(i))
            cf.select_subplot(None, force_select=[cf.subplots[j]])
            fs.weights_edit.setText(str(weights))
            cf.update_gridspec(nplots, weights)
            cf.format_axes()
            cf.draw()
