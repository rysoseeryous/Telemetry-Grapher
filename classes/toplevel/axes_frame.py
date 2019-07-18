# -*- coding: utf-8 -*-
"""axes_frame.py - Contains AxesFrame class definition."""

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

import matplotlib.dates as mdates
import matplotlib.pyplot as plt
from matplotlib.ticker import AutoMinorLocator
from matplotlib.gridspec import GridSpec
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigCanvas

from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore import Qt

from ..internal.subplot_manager import SubplotManager

class AxesFrame(FigCanvas):
    """Central widget in Application Base main window."""
    def patch_figure(self, fig):
        """Bypasses issue where add_subplot(key) returns the subplot already
        created with that key (if it exists) instead of creating a new one."""
        def get(key, self=fig):
            return None
        fig._axstack.get = get

    def _draw(self, event):
        self.draw()

    def __init__(self, parent):
        self.fig = plt.figure()
        self.patch_figure(self.fig)
        super().__init__(self.fig)
        self.parent = parent
        ui = self.parent
        self.timestamp_format = '%b %d, %H:%M'
        left = ui.af_init['left_pad']
        right = 1 - ui.af_init['right_pad']
        bottom = ui.af_init['lower_pad']
        top = 1 - ui.af_init['upper_pad']
        self.gs = GridSpec(1, 1,
                           left=left, right=right, bottom=bottom, top=top,
                           height_ratios=[1])
        ax0 = self.fig.add_subplot(self.gs[0])
        self.subplots = [SubplotManager(parent, ax0, index=0)]
        self.current_sps = []
        self.available_data = ui.groups_to_contents(ui.groups)
        self.fig.canvas.mpl_connect('button_press_event', self.select_subplot)
        self.fig.canvas.mpl_connect('button_press_event', self._draw)
        self.fig.suptitle(ui.af_init['title'], fontsize=ui.af_init['title_size'])
        self.draw()

    def weights(self):
        return self.gs.get_height_ratios()

    def nplots(self):
        return self.gs.get_geometry()[0]

    def update_gridspec(self, nplots=None, weights=None):
        ui = self.parent
        fs = ui.figure_settings
        if nplots is None:
            nplots = self.nplots()
        if weights is None:
            weights = self.weights()
        n = max([len(sp.axes[2:]) for sp in self.subplots])
        # If any subplot has a shown legend, treat like another secondary axis
        for sp in self.subplots:
            c1 = sp.legend_on
            c2 = sp.contents
            c3 = sp.location=='Outside Right'
            if c1 and c2 and c3:
                n += 1
                break
        left = fs.left_pad.value()
        right = 1 - fs.right_pad.value() - fs.axis_offset.value()*n
        bottom = fs.lower_pad.value()
        top = 1 - fs.upper_pad.value()
        self.gs = GridSpec(nplots, 1, height_ratios=weights,
                           left=left, right=right, bottom=bottom, top=top,
                           hspace=fs.spacing.value())
        for i, sp in enumerate(self.subplots):
            sp.index = i
            for ax in sp.axes:
                ax.set_position(self.gs[i].get_position(self.fig))

    def replot(self, data=True, legend=True):
        for sp in self.subplots:
            if data:
                sp.plot()
            if legend:
                sp.show_legend()

    def format_axes(self):
        """Manages figure axes ticks, tick labels."""
        ui = self.parent
        fs = ui.figure_settings
        linestyles = ['-', '--', ':', '-.']

        self.fig._suptitle.set_fontsize(fs.title_size.value())

        for sp in self.subplots:
            for i, ax in enumerate(sp.axes):
                ax.tick_params(axis='x', which='both',
                               labelbottom=False, bottom=False)
                ax.yaxis.label.set_size(fs.label_size.value())
                ax.tick_params(axis='y', labelsize=fs.tick_size.value())

                ax.minorticks_off()
                if fs.major_y.isChecked():
                    ax.yaxis.grid(which='major',
                                  linestyle=linestyles[i%len(linestyles)])
                else:
                    ax.yaxis.grid(which='major', b=False)
                if fs.minor_y.isChecked():
                    ax.yaxis.set_minor_locator(AutoMinorLocator())
                    ax.yaxis.grid(which='minor',
                                  linestyle=linestyles[i%len(linestyles)])
                else:
                    ax.yaxis.grid(which='minor', b=False)
            if sp.contents:
                if sp.index == len(self.subplots)-1:
                    sp.host().tick_params(axis='x', which='both',
                           labelbottom=True, bottom=True)
                    for tick in sp.host().xaxis.get_ticklabels():
                        tick.set_size(fs.tick_size.value())
                        tick.set_rotation(fs.tick_rot.value())
                        tick.set_horizontalalignment('right')
                sp.host().xaxis_date()
                sp.host().xaxis.set_major_locator(self.major_locator)
                if fs.minor_x.isChecked():
                    sp.host().xaxis.set_minor_locator(self.minor_locator)
                else:
                    sp.host().xaxis.grid(which='minor', b=False)
                sp.host().xaxis.set_major_formatter(
                        mdates.DateFormatter(self.timestamp_format))
            sp.host().xaxis.grid(which='major', b=fs.major_x.isChecked())
            sp.host().xaxis.grid(which='minor', b=fs.minor_x.isChecked())

    def get_subplot(self, event):
        for sp in self.subplots:
            if event.inaxes in sp.axes:
                return sp
        return None

    def select_subplot(self, event, force_select=None):
        """Controls highlighting and contents display.
        Shift and Ctrl clicking supported.
        Click within figure but outside subplots to deselect axis.
        Provide force_select=X to select subplots in list X
        where X is a list of Subplot_Manager objects."""
        ui = self.parent
        sd = ui.series_display
        sd.plotted.clear()
        modifiers = QApplication.keyboardModifiers()

        def select(sps, add=True):
            """Toggles subplot border thickness
            and membership in self.current_sps."""
            if sps:
                for sp in sps.copy():
                    plt.setp(sp.host().spines.values(),
                             linewidth=ui.highlight[str(add)])
                    if add:
                        self.current_sps.append(sp)
                    else:
                        self.current_sps.remove(sp)
            else:
                self.current_sps = []

        if force_select is not None:
            select(self.current_sps, False)
            select(force_select)
        else:
            if event.inaxes is None:
                select(self.current_sps, False)
            else:
                sp = self.get_subplot(event)
                if modifiers == Qt.ControlModifier:
                    select([sp], add=(sp not in self.current_sps))
                elif modifiers == Qt.ShiftModifier:
                    if not self.current_sps:
                        select([sp])
                    elif len(self.current_sps) == 1:
                        current_i = self.current_sps[0].index
                        select(self.current_sps, False)
                        first = min([current_i, sp.index])
                        last = max([current_i, sp.index])
                        select(self.subplots[first:last+1])
                    else:
                        select(self.current_sps, False)
                        select([sp])
                else:
                    select(self.current_sps, False)
                    select([sp])
#                    for ax in sp.axes:
#                        print(ax.label())
#                        print('    ', ax.get_frame_on())
#                        print('    ', ax.patch.get_visible())
        self.update_toolbars()


    def update_toolbars(self):
        ui = self.parent
        sd = ui.series_display
        st = ui.subplot_toolbar
        lt = ui.legend_toolbar
        at = ui.axes_toolbar
        b = (len(self.current_sps) >= 1)

        # Subplot Toolbar
        st.cycle.setEnabled(b)
#        st.insert.setEnabled(b)
        st.delete.setEnabled(b)
        st.clear.setEnabled(b)
        st.reorder_up.setEnabled(len(self.current_sps) == 1)
        st.reorder_down.setEnabled(len(self.current_sps) == 1)

        # Legend Toolbar
        lt.legend_toggle.setEnabled(b)
        any_legend = any([sp.legend_on for sp in self.current_sps])
        lt.legend_toggle.setChecked(any_legend)

        lt.legend_location.setEnabled(b)
        lt.legend_location.blockSignals(True)
        lt.legend_location.clear()
        if b:
            lt.legend_location.addItems(list(lt.locations.keys()))
            lt.legend_location.setCurrentText(self.current_sps[0].location)
        lt.legend_location.blockSignals(False)

        lt.legend_columns.setEnabled(b)
        lt.legend_columns.blockSignals(True)
        lt.legend_columns.clear()
        if b:
            lt.legend_columns.setValue(self.current_sps[0].ncols)
        lt.legend_columns.blockSignals(False)

        lt.legend_units.setEnabled(b)
        any_units = any([sp.legend_units for sp in self.current_sps])
        lt.legend_units.setChecked(any_units)

        lt.color_toggle.setEnabled(b)
        any_colored = any([sp.color_coord for sp in self.current_sps])
        lt.color_toggle.setChecked(any_colored)

        # Axes Toolbar
        at.selector.setEnabled(b)
        at.selector.clear()

        if b:
            if len(self.current_sps) == 1:
                sp = self.current_sps[0]
                sd.populate_tree('plotted', sp.contents)
                if sp.contents:
                    at.selector.addItem('All')
                    at.selector.addItems([ax.label() for ax in sp.axes])
                if len(at.current_axes) == 1:
                    at.selector.setCurrentText(at.current_axes[0].label())
                else:
                    at.selector.setCurrentText('All')
                ui.statusBar().showMessage(
                        'Selected subplot: {}'.format(sp.index))
            else:
                sd.plotted.clear()
                selected = sorted([sp.index for sp in self.current_sps])
                ui.statusBar().showMessage(
                        'Selected subplots: {}'.format(selected))
        else:
            ui.statusBar().showMessage('No subplot selected')
