# -*- coding: utf-8 -*-
"""
Created on Mon May  6 14:58:42 2019

@author: seery
"""
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas

class Axes_Frame(FigureCanvas):
    """Container for figure with subplots. New Axes_Frame objects are created and when a new Figure tab is created (TBI)."""
    def __init__(self, parent):
        self.parent = parent
        self.fig = plt.figure(constrained_layout=False)  # not working with gridspec in controls frame. Look into later.
        super().__init__(self.fig)
        self.weights = [1]
        gs = gridspec.GridSpec(1, 1, height_ratios=self.weights)
        ax0 = self.fig.add_subplot(gs[0])
        self.subplots = [Subplot_Manager(parent, ax0, index=0, contents={})]
        self.current_sps = []
        self.available_data = copy.deepcopy(parent.groups)  # holds all unplotted data (unique to each Axes Frame object, see plans for excel tab implementation)
        self.fig.canvas.mpl_connect('button_press_event', self.select_subplot)
        self.fig.suptitle(parent.control_frame.titleEdit.text(), fontsize=20)
        mpl.rc('font', family='serif')
        self.draw()

        ### These will be moved to plotting preferences QDockWidget
        self.unit_dict = {  # ylabels for each unit type so units can be identified by shorthand letters
            'T':'Temperature [°C]',
            'V':'Voltage [V]',
            'I':'Current [A]',
            'P':'Power [W]'
        }
        self.color_dict = {  #when color coordination is on, assign map unit types to these colors
            'T':'r',
            'V':'b',
            'I':'g',
            'P':'y',
        }
        # This will be deprecated in favor of markers (or add the option to preferences QDockWidget)
        self.linestyles = [  # when color coordination is on, use linestyles in this order to differentiate series
            '-',
            '--',
            '-.',
            ':',
        ]



    def select_subplot(self, event, force_select=None):
        """Highlights clicked-on subplot and displays subplot contents in plotted tree.
        Shift and Ctrl clicking supported.
        Click within figure but outside subplots to deselect axis and clear plotted tree.
        Provide force_select=X to programmatically select subplots in list X (wrapped by Subplot_Manager object)."""
        TG = self.parent
        CF = TG.control_frame
        SF = TG.series_frame
        widths = {True:1.5, False:0.5}
        SF.plotted.clear()
        modifiers = QApplication.keyboardModifiers()

        def highlight(sps, invert=False):
            if sps:
                for sp in sps:
                    if invert:
                        plt.setp(sp.host().spines.values(), linewidth=widths[False])
                        if sp in self.current_sps: self.current_sps.remove(sp)
                    else:
                        plt.setp(sp.host().spines.values(), linewidth=widths[True])
                        self.current_sps.append(sp)
            else:
                self.current_sps = []

        if force_select is not None:
            highlight(force_select)
        else:
            if event.inaxes is None:
                highlight(self.subplots, invert=True)
                self.current_sps = []
            else:
#                print('event.inaxes:\t', event.inaxes)
#                print('fig.axes:\t', self.fig.axes)
#                print('subplot hosts:\t', [sp.host() for sp in self.subplots])
#                print(event.inaxes.get_yticks())

                #find out which Subplot_Manager contains event-selected axes
                for sm in self.subplots:
                    if event.inaxes in sm.axes:
                        sp = sm
                        break
#                print(sp)
#                sp = self.subplots[[sp.host() for sp in self.subplots].index(event.inaxes)]
                if modifiers == Qt.ControlModifier:
                    highlight([sp], invert=(sp in self.current_sps))
                elif modifiers == Qt.ShiftModifier:
                    if not self.current_sps:
                        highlight([sp])
                    elif len(self.current_sps) == 1:
                        current_i = self.current_sps[0].index
                        highlight(self.subplots, invert=True)
                        highlight(self.subplots[min([current_i, sp.index]):max([current_i, sp.index])+1])
                    else:
                        highlight(self.subplots, invert=True)
                        highlight([sp])
                else:
                    highlight(self.subplots, invert=True)
                    highlight([sp])
        if len(self.current_sps) == 1:
            sp = self.current_sps[0]
            SF.populate_tree(sp.contents, SF.plotted)
            SF.search(SF.searchPlotted, SF.plotted, sp.contents)
            CF.legendToggle.setCheckable(True)
            CF.legendToggle.setChecked(sp.legend)
            CF.colorCoord.setCheckable(True)
            CF.colorCoord.setChecked(sp.colorCoord)
            TG.statusBar().showMessage('Selected subplot: {}'.format(sp.index))
        else:
            SF.plotted.clear()
            if self.current_sps:
                CF.legendToggle.setChecked(any([sp.legend for sp in self.current_sps]))
                CF.colorCoord.setChecked(any([sp.colorCoord for sp in self.current_sps]))
                TG.statusBar().showMessage('Selected subplots: {}'.format(sorted([sp.index for sp in self.current_sps])))
            else:
                CF.legendToggle.setChecked(False)
                CF.colorCoord.setChecked(False)
                TG.statusBar().showMessage('No subplot selected')
        self.draw()