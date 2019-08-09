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

#from dateutil.rrule import DAILY
import datetime as dt
from matplotlib.dates import HourLocator, MinuteLocator, DateFormatter
import matplotlib.pyplot as plt
from matplotlib.ticker import NullLocator, AutoMinorLocator
from matplotlib.gridspec import GridSpec
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg

from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore import Qt

from ..internal.subplot_manager import SubplotManager
from ..internal.contents_dict import ContentsDict

class AxesFrame(FigureCanvasQTAgg):
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
        self.transfer_contents = ContentsDict()
        self.transfer_sp = None
        self.setAcceptDrops(True)

        self.saved = True
        self.never_saved = True
        self.parent = parent
        ui = self.parent
        for k,v in ui.af_init.items():
            setattr(self, k, v)

        self.gs = GridSpec(1, 1,
                           left=self.left_pad,
                           right=1-self.right_pad,
                           bottom=self.lower_pad,
                           top=1-self.upper_pad,
                           hspace=self.spacing,
                           height_ratios=[1])
        ax0 = self.fig.add_subplot(self.gs[0])
        sp = SubplotManager(self, ax0, 0)
        sp.ygrid_proxy.set_position(self.gs[0].get_position(self.fig))
        self.subplots = [sp]
        self.current_sps = []
        self.groups = []
        self.available_data = ContentsDict()

        self.fig.canvas.mpl_connect('button_press_event', self.select_subplot)
        self.fig.canvas.mpl_connect('button_press_event', self._draw)
        self.fig.suptitle(self.title,
                          fontsize=self.title_size)

        self.start = dt.datetime.strptime('2000-01-01 00:00:00',
                                              '%Y-%m-%d  %H:%M:%S')
        self.end = dt.datetime.now()
        self.draw()

    def weights(self):
        return self.gs.get_height_ratios()

    def nplots(self):
        return self.gs.get_geometry()[0]

    def update_gridspec(self, nplots=None, weights=None):
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
        left = self.left_pad
        right = 1 - self.right_pad - self.axis_offset*n
        bottom = self.lower_pad
        top = 1 - self.upper_pad
        self.gs = GridSpec(nplots, 1, height_ratios=weights,
                           left=left, right=right, bottom=bottom, top=top,
                           hspace=self.spacing)
        for i, sp in enumerate(self.subplots):
            sp.index = i
            for ax in sp.axes:
                ax.set_position(self.gs[i].get_position(self.fig))
            sp.ygrid_proxy.set_position(self.gs[i].get_position(self.fig))
        self.saved = False

    def replot(self, data=True, legend=True):
        for sp in self.subplots:
            if data:
                sp.plot()
            if legend:
                sp.show_legend()
        self.saved = False

#    def create_rrule(self, num_major_ticks, num_minor_ticks):
#        period = 24*60//num_major_ticks//num_minor_ticks
#        div = num_minor_ticks*60
#        byminute = sorted(set([(i*period%div)%60 for i in range(60)]))
#        byhour = list(range(24))
#        c = 0
#        bysetpos = []
#        for hour in byhour:
#            for minute in byminute:
#                if (hour*60 + minute)%period == 0:
#                    bysetpos.append(c+1)
#                c += 1
#        return rrulewrapper(DAILY, bysetpos=bysetpos, byhour=byhour,
#                            byminute=byminute, bysecond=0)

    def create_mlocator(self, m_T):
        hours = m_T//60
        minutes = m_T - 60*hours
        if hours: return HourLocator(byhour=range(0, 24, hours))
        if minutes: return MinuteLocator(byminute=range(0, 60, minutes))

    def verify_ticks(self, M_T, m_T):
        try:
            if any([sp.contents for sp in self.subplots]):
                days = (self.end - self.start).days
                if self.mx:
                    self.create_mlocator(m_T)
                    ticks_per_day = 24/M_T + 1440/m_T
                else:
                    ticks_per_day = 24/M_T
                if days*ticks_per_day > 500:
                    raise ValueError
        except ValueError:
            return False
        return True

    def format_axes(self):
        """Manages figure axes ticks, tick labels."""
        linestyles = ['-', '--', ':', '-.']
        self.fig._suptitle.set_fontsize(self.title_size)
        Mlocator = HourLocator(byhour=range(0, 24, self.M_T))
        mlocator = self.create_mlocator(self.m_T)

        for sp in self.subplots:
            sp.ygrid_proxy.clear()
            sp.ygrid_proxy.set_ymargin(0)
            for i, ax in enumerate(sp.axes):
                ls = linestyles[i%len(linestyles)]
                ax.tick_params(axis='x', which='both',
                               labelbottom=False, bottom=False)
                ax.yaxis.label.set_size(self.label_size)
                ax.tick_params(axis='y', labelsize=self.tick_size)

                if self.MY and not self.my:
                    sp.ygrid_proxy.mock_gridlines(ax, which='major',
                                                  linestyle=ls)
                if self.my:
                    if ax.log:
                        ax.minorticks_on()
                    else:
                        ax.yaxis.set_minor_locator(AutoMinorLocator())
                    ax.tick_params(axis='y', which='minor',
                                   labelleft=False, labelright=False)
                    sp.ygrid_proxy.mock_gridlines(ax, which='both',
                                                  linestyle=ls)
                else:
                    ax.yaxis.set_minor_locator(NullLocator())
            if sp.contents:
                if sp.index == len(self.subplots)-1:
                    sp.host().tick_params(axis='x', which='both',
                           labelbottom=True, bottom=True)
                    for tick in sp.host().xaxis.get_ticklabels():
                        tick.set_size(self.tick_size)
                        tick.set_rotation(self.tick_rot)
                        tick.set_horizontalalignment('right')
                sp.host().xaxis_date()
                sp.host().xaxis.set_major_locator(Mlocator)
                if self.mx:
                    sp.host().xaxis.set_minor_locator(mlocator)
                else:
                    sp.host().xaxis.set_minor_locator(NullLocator())
                sp.host().xaxis.set_major_formatter(
                        DateFormatter(self.tsf))
            sp.host().xaxis.grid(which='major', b=self.MX)
            sp.host().xaxis.grid(which='minor', b=self.mx)
            self.saved = False

    def get_subplot(self, event):
        for sp in self.subplots:
            if event.inaxes in sp.axes + [sp.ygrid_proxy]:
                return sp
        return None

    def get_subplot_drag(self, event):
        x, y = event.pos().x(), event.pos().y()
        bbox = self.fig.get_window_extent().transformed(
                self.fig.dpi_scale_trans.inverted())
        height = bbox.height*self.fig.dpi
        for sp in self.subplots:
            bbox = sp.host().get_window_extent().transformed(
                    self.fig.dpi_scale_trans.inverted())
            xmin = bbox.xmin*self.fig.dpi
            ymin = height-bbox.ymax*self.fig.dpi
            xmax = bbox.xmax*self.fig.dpi
            ymax = height-bbox.ymin*self.fig.dpi
            if xmin <= x <= xmax and ymin <= y <= ymax:
                return sp
        return None

    def dragEnterEvent(self, event):
        ui = self.parent
        sd = ui.series_display
        if QApplication.focusWidget() is sd.plotted:
            selected = sd.plotted.selectedItems()
            self.transfer_contents = sd.tree_items_to_contents(selected)
            self.transfer_sp = self.current_sps[0]
        self.select_subplot(None, force_select=[])
        self.draw()
        self.dragMoveEvent(event)

    def dragMoveEvent(self, event):
        sp = self.get_subplot_drag(event)
        if sp is not None:
            self.select_subplot(None, force_select=[sp])
        else:
            self.select_subplot(None, force_select=[])
        self.draw()
        event.accept()

    def dragLeaveEvent(self, event):
        self.select_subplot(None, force_select=[])
        self.draw()
        event.accept()

    def dropEvent(self, event):
        ui = self.parent
        sd = ui.series_display
        if self.current_sps:
            if QApplication.focusWidget() is sd.available:
                sd.add_to_subplot()
            elif QApplication.focusWidget() is sd.plotted:
                if self.transfer_sp is not self.current_sps[0]:
                    sd.transfer_plotted()
                self.transfer_contents = None
                self.transfer_sp = None

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
                             linewidth=ui.highlight[add])
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
            lt.legend_location.addItems(list(ui.locations.keys()))
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

    def prep_fig(self):
        ui = self.parent
        fs = ui.figure_settings
        self.select_subplot(None, force_select=[])
        fs.density.blockSignals(True)
        fs.density.setValue(100)
        fs.density.blockSignals(False)
        self.density = 100
        self.replot()
        self.draw()
