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

import itertools
from copy import copy, deepcopy
import matplotlib.pyplot as plt

from PyQt5.QtWidgets import QToolBar, QAction, QStyle
from PyQt5.QtGui import QIcon
from PyQt5.QtCore import QObject

from ..internal.subplot_manager import SubplotManager

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
        af = ui.axes_frame
        fs = ui.figure_settings
        if len(af.current_sps) == 1:
            idx = af.current_sps[0].index
        else:
            idx = af.nplots()-1
        weights = af.weights()
        weights.insert(idx+1, 1)
        nplots = af.nplots() + 1
        ax = af.fig.add_subplot(111)
        af.subplots.insert(idx+1, SubplotManager(ui, ax, index=idx+1))
        fs.weights_edit.setText(str(weights))
        af.update_gridspec(nplots, weights)
        af.format_axes()
        af.draw()

    def delete_subplot(self):
        """Deletes selected subplot(s) and returns contents to available."""
        ui = self.parent
        af = ui.axes_frame
        fs = ui.figure_settings
        sd = ui.series_display
        nplots = af.nplots()
        weights = af.weights()
        for i in reversed([sp.index for sp in af.current_sps]):
            # add contents back into available tree
            sp = af.subplots[i]
            af.available_data.add(deepcopy(sp.contents))
            if nplots == 1:
                sp.remove(deepcopy(sp.contents))
                weights = [1]
            else:
                for ax in sp.axes: ax.remove()
                del af.subplots[i]
                del weights[i]
                nplots -= 1
        sd.populate_tree('available', af.available_data)
        af.select_subplot(None, force_select=[])
        fs.weights_edit.setText(str(weights))
        af.update_gridspec(nplots, weights)
        af.format_axes()
        af.draw()

    def clear_subplot(self):
        """Clears selected subplots.
        Adds selected subplots' contents back into available tree."""
        ui = self.parent
        af = ui.axes_frame
        sd = ui.series_display
        for sp in af.current_sps:
            af.available_data.add(deepcopy(sp.contents))
            sp.remove(deepcopy(sp.contents))
        sd.populate_tree('available', af.available_data)
        af.select_subplot(None, force_select=copy(af.current_sps))
        af.update_gridspec()
        af.format_axes()
        af.draw()

    def cycle_subplot(self):
        """Cycles through unit order permutations of selected subplot(s)."""
        ui = self.parent
        af = ui.axes_frame
        for sp in af.current_sps:
            plt.setp(sp.host().spines.values(),
                     linewidth=ui.highlight['False'])
            ids = [ax._id for ax in sp.axes]
            sorted_perms = sorted(itertools.permutations(ids))
            perms = [list(p) for p in sorted_perms]
            i = perms.index(ids)
            new_ids = perms[(i+1)%len(perms)]
            sp.axes = [sp.get_axes(*_id) for _id in new_ids]
            plt.setp(sp.host().spines.values(),
                     linewidth=ui.highlight['True'])
        af.replot()
        af.format_axes()
        af.draw()

    def reorder(self):
        """Reorders selected subplot up or down."""
        ui = self.parent
        af = ui.axes_frame
        fs = ui.figure_settings
        sp = af.current_sps[0]
        i = sp.index
        caller = QObject.sender(self)
        if caller == self.reorder_up:
            j = i-1
        if caller == self.reorder_down:
            j = i+1
        nplots = af.nplots()
        # if can be moved up/down
        if 0 <= j < nplots:
            weights = af.weights()
            weights.insert(j, weights.pop(i))
            af.subplots.insert(j, af.subplots.pop(i))
            af.select_subplot(None, force_select=[af.subplots[j]])
            fs.weights_edit.setText(str(weights))
            af.update_gridspec(nplots, weights)
            af.format_axes()
            af.draw()
