# -*- coding: utf-8 -*-
"""
Created on Thu Jun 13 15:46:31 2019

@author: seery
"""
import math
import functools
import matplotlib.pyplot as plt
from matplotlib.gridspec import GridSpec
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas

from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore import Qt

from ..internal.subplot_manager import Subplot_Manager

class Axes_Frame(FigureCanvas):
    """Central widget in Application Base main window."""

    def __init__(self, parent):
        self.parent = parent
        AB = self.parent
        CF = AB.control_frame
        FS = AB.figure_settings
        self.fig = plt.figure()
        super().__init__(self.fig)
        self.weights = [1]
        left = FS.leftPad.value()
        right = 1 - FS.rightPad.value()
        bottom = FS.lowerPad.value()
        top = 1 - FS.upperPad.value()
        gs = GridSpec(1, 1, left=left, right=right, bottom=bottom, top=top)
        ax0 = self.fig.add_subplot(gs[0])
        ax0.tick_params(axis='x', labelbottom=False, bottom=False)
        self.subplots = [Subplot_Manager(parent, ax0, index=0, contents={})]
        self.current_sps = []
        # holds all unplotted data (unique to each Axes Frame object
        # see plans for excel tab implementation)
        self.available_data = AB.groups_to_contents(AB.groups)
        self.fig.canvas.mpl_connect('button_press_event', self.select_subplot)
        self.fig.suptitle(CF.titleEdit.text(), fontsize=FS.titleSize.value())
        self.draw()

    def refresh_all(self):
        """Refreshes entire figure.
        Called when:
            - Any value in Figure Settings is updated
            - Subplots are modified in any way
            - User calls via Edit menu (Ctrl+R)"""
#        print(inspect.stack())
        AB = self.parent
        FS = AB.figure_settings
        CF = AB.control_frame
        reselect = [sp.index for sp in self.current_sps]
        for ax in self.fig.axes: ax.remove()

        n = max([len(sp.axes[2:]) for sp in self.subplots])
        # If any subplot has a shown legend, treat like another secondary axis
        for sp in self.subplots:
            c1 = sp.legend
            c2 = sp.contents
            c3 = sp.legendLocation=='Outside Right'
            if c1 and c2 and c3:
                n += 1
                break

        left = FS.leftPad.value()
        right = 1 - FS.rightPad.value() - FS.parOffset.value()*n
        bottom = FS.lowerPad.value()
        top = 1 - FS.upperPad.value()
        gs = GridSpec(len(self.subplots), 1,
                      height_ratios=self.weights,
                      left=left, right=right, bottom=bottom, top=top,
                      hspace=FS.hspace.value())
        for i, sp in enumerate(self.subplots):
            ax = self.fig.add_subplot(gs[i, 0])
            sp.axes = [ax]
            sp.index = i
            sp.plot()

        self.fig.suptitle(CF.titleEdit.text(), fontsize=FS.titleSize.value())

        CF.cleanup_axes()
        g = functools.reduce(math.gcd, self.weights)
        # simplify weights by their greatest common denominator
        # (eg [2,2,4] -> [1,1,2])
        self.weights = [w//g for w in self.weights]
        CF.weightsEdit.setText(str(self.weights))

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
        AB.saved = False

    def select_subplot(self, event, force_select=None):
        """Controls highlighting and contents display.
        Shift and Ctrl clicking supported.
        Click within figure but outside subplots to deselect axis.
        Provide force_select=X to select subplots in list X
        where X is a list of Subplot_Manager objects."""
        AB = self.parent
        CF = AB.control_frame
        SF = AB.series_frame
        widths = {True: 1.5, False: 0.5}
        SF.plotted.clear()
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
                for sm in self.subplots:
                    if event.inaxes in sm.axes:
                        sp = sm
                        break
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

        CF.legendColumns.blockSignals(True)
        CF.legendPosition.blockSignals(True)
        CF.legendPosition.clear()
        if not self.current_sps:
            CF.colorCoord.setChecked(False)
            CF.colorCoord.setEnabled(False)
            CF.legendToggle.setChecked(False)
            CF.legendToggle.setEnabled(False)
            CF.legendColumns.clear()
            CF.legendColumns.setEnabled(False)
            CF.legendPosition.setEnabled(False)
            AB.statusBar().showMessage('No subplot selected')
        else:
            CF.colorCoord.setEnabled(True)
            CF.legendToggle.setEnabled(True)
            CF.legendColumns.setEnabled(True)
            CF.legendPosition.setEnabled(True)
            CF.legendPosition.addItems(list(CF.legend_dict.keys()))
            if len(self.current_sps) == 1:
                sp = self.current_sps[0]
                SF.populate_tree(sp.contents, SF.plotted)
                SF.search(SF.searchPlotted, SF.plotted, sp.contents)
                CF.colorCoord.setChecked(sp.colorCoord)
                CF.legendToggle.setChecked(sp.legend)
                CF.legendColumns.setValue(sp.ncols)
                CF.legendPosition.setCurrentText(sp.legendLocation)
                AB.statusBar().showMessage(
                        'Selected subplot: {}'.format(sp.index)
                        )
            else:
                SF.plotted.clear()
                any_colored = any([sp.colorCoord for sp in self.current_sps])
                CF.colorCoord.setChecked(any_colored)
                any_legend = any([sp.legend for sp in self.current_sps])
                CF.legendToggle.setChecked(any_legend)
                selected_cols = [sp.ncols for sp in self.current_sps]
                if all(x==selected_cols[0] for x in selected_cols):
                    CF.legendColumns.setValue(selected_cols[0])
                else:
                    CF.legendColumns.clear()
                CF.legendPosition.setCurrentText(
                        self.current_sps[0].legendLocation
                        )
                selected = sorted([sp.index for sp in self.current_sps])
                AB.statusBar().showMessage(
                        'Selected subplots: {}'.format(selected)
                        )
        CF.legendColumns.blockSignals(False)
        CF.legendPosition.blockSignals(False)
        self.draw()
