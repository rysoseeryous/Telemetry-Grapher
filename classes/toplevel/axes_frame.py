# -*- coding: utf-8 -*-
"""
Created on Thu Jun 13 15:46:31 2019

@author: seery
"""
import math
import functools
import matplotlib.pyplot as plt
from matplotlib.gridspec import GridSpec
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigCanvas

from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore import Qt

from ..internal.subplot_manager import SubplotManager

class AxesFrame(FigCanvas):
    """Central widget in Application Base main window."""

    def __init__(self, parent):
        self.fig = plt.figure()
        super().__init__(self.fig)
        self.parent = parent
        ui = self.parent
        cp = ui.control_panel
        fs = ui.figure_settings
        self.weights = [1]
        left = fs.left_pad.value()
        right = 1 - fs.right_pad.value()
        bottom = fs.lower_pad.value()
        top = 1 - fs.upper_pad.value()
        gs = GridSpec(1, 1, left=left, right=right, bottom=bottom, top=top)
        ax0 = self.fig.add_subplot(gs[0])
        ax0.tick_params(axis='x', labelbottom=False, bottom=False)
        self.subplots = [SubplotManager(parent, ax0)]
        self.current_sps = []
#        self.refresh_all()
        # holds all unplotted data (unique to each Axes Frame object
        # see plans for excel tab implementation)
        self.available_data = ui.groups_to_contents(ui.groups)
        self.fig.canvas.mpl_connect('button_press_event', self.select_subplot)
        self.fig.suptitle(cp.title_edit.text(), fontsize=fs.title_size.value())
        self.draw()

    def refresh_all(self):
        """Refreshes entire figure.
        Called when:
            - Any value in Figure Settings is updated
            - Subplots are modified in any way
            - User calls via Edit menu (Ctrl+R)"""
        ui = self.parent
        fs = ui.figure_settings
        cp = ui.control_panel
        reselect = [sp.index for sp in self.current_sps]
        for ax in self.fig.axes: ax.remove()

        n = max([len(sp.axes[2:]) for sp in self.subplots])
        # If any subplot has a shown legend, treat like another secondary axis
        for sp in self.subplots:
            c1 = sp.legend
            c2 = sp.contents
            c3 = sp.location=='Outside Right'
            if c1 and c2 and c3:
                n += 1
                break

        left = fs.left_pad.value()
        right = 1 - fs.right_pad.value() - fs.axis_offset.value()*n
        bottom = fs.lower_pad.value()
        top = 1 - fs.upper_pad.value()
        gs = GridSpec(len(self.subplots), 1,
                      height_ratios=self.weights,
                      left=left, right=right, bottom=bottom, top=top,
                      hspace=fs.spacing.value())
        for i, sp in enumerate(self.subplots):
            ax = self.fig.add_subplot(gs[i])
            sp.axes = [ax]
            sp.index = i
            sp.plot()

        self.fig.suptitle(cp.title_edit.text(), fontsize=fs.title_size.value())

        cp.cleanup_axes()
        g = functools.reduce(math.gcd, self.weights)
        # simplify weights by their greatest common denominator
        # (eg [2,2,4] -> [1,1,2])
        self.weights = [w//g for w in self.weights]
        cp.weights_edit.setText(str(self.weights))

        try:
            fs = [self.subplots[i] for i in reselect]
            self.select_subplot(None, force_select=fs)
        except IndexError:
            # happens when you try to delete all the plots
            # some issue with instance attribute
            # current_sps not updating when you set it to []?
            self.draw()
#            pass
            # select_subplot calls self.draw(), don't need to do it again
        ui.saved = False

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
        cp = ui.control_panel
        sd = ui.series_display
        widths = {True: 1.5, False: 0.5}
        sd.plotted.clear()
        modifiers = QApplication.keyboardModifiers()

        def highlight(sps, invert=False):
            if sps:
                for sp in sps:
                    if invert:
                        plt.setp(sp.host().spines.values(),
                                 linewidth=widths[False])
                        if sp in self.current_sps:
                            self.current_sps.remove(sp)
                    else:
                        plt.setp(sp.host().spines.values(),
                                 linewidth=widths[True])
                        self.current_sps.append(sp)
            else:
                self.current_sps = []

        if force_select is not None:
            highlight(self.subplots, invert=True)
            self.current_sps = []
            highlight(force_select)
        else:
            if event.inaxes is None:
                highlight(self.subplots, invert=True)
                self.current_sps = []
            else:
                #find out which Subplot_Manager contains event-selected axes
                sp = self.get_subplot(event)
                if modifiers == Qt.ControlModifier:
                    highlight([sp], invert=(sp in self.current_sps))
                elif modifiers == Qt.ShiftModifier:
                    if not self.current_sps:
                        highlight([sp])
                    elif len(self.current_sps) == 1:
                        current_i = self.current_sps[0].index
                        highlight(self.subplots, invert=True)
                        first = min([current_i, sp.index])
                        last = max([current_i, sp.index])
                        highlight(self.subplots[first:last+1])
                    else:
                        highlight(self.subplots, invert=True)
                        highlight([sp])
                else:
                    highlight(self.subplots, invert=True)
                    highlight([sp])

        cp.legend_columns.blockSignals(True)
        cp.legend_location.blockSignals(True)
        cp.legend_location.clear()
        if not self.current_sps:
            cp.color_toggle.setChecked(False)
            cp.color_toggle.setEnabled(False)
            cp.legend_toggle.setChecked(False)
            cp.legend_toggle.setEnabled(False)
            cp.legend_columns.clear()
            cp.legend_columns.setEnabled(False)
            cp.legend_location.setEnabled(False)
            ui.statusBar().showMessage('No subplot selected')
        else:
            cp.color_toggle.setEnabled(True)
            cp.legend_toggle.setEnabled(True)
            cp.legend_columns.setEnabled(True)
            cp.legend_location.setEnabled(True)
            cp.legend_location.addItems(list(cp.locations.keys()))
            if len(self.current_sps) == 1:
                sp = self.current_sps[0]
                sd.populate_tree(sp.contents, sd.plotted)
                sd.search_plotted.textChanged.emit(sd.search_plotted.text())
                cp.color_toggle.setChecked(sp.color_coord)
                cp.legend_toggle.setChecked(sp.legend)
                cp.legend_columns.setValue(sp.ncols)
                cp.legend_location.setCurrentText(sp.location)
                ui.statusBar().showMessage(
                        'Selected subplot: {}'.format(sp.index))
            else:
                sd.plotted.clear()
                any_colored = any([sp.color_coord for sp in self.current_sps])
                cp.color_toggle.setChecked(any_colored)
                any_legend = any([sp.legend for sp in self.current_sps])
                cp.legend_toggle.setChecked(any_legend)
                selected_cols = [sp.ncols for sp in self.current_sps]
                if all(x==selected_cols[0] for x in selected_cols):
                    cp.legend_columns.setValue(selected_cols[0])
                else:
                    cp.legend_columns.clear()
                cp.legend_location.setCurrentText(self.current_sps[0].location)
                selected = sorted([sp.index for sp in self.current_sps])
                ui.statusBar().showMessage(
                        'Selected subplots: {}'.format(selected))
        cp.legend_columns.blockSignals(False)
        cp.legend_location.blockSignals(False)
        self.draw()
