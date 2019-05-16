# -*- coding: utf-8 -*-
"""
Created on Mon May  6 14:59:10 2019

@author: seery
"""
class Control_Frame(QWidget):
    """Contains all buttons for controlling the organization of subplots and saving the figure."""
    def __init__(self, parent):
        super().__init__()
        self.parent = parent
        self.grid = QGridLayout()

        title = QLabel('Figure title:')
        self.titleEdit = QLineEdit('New_Figure')
        self.titleEdit.returnPressed.connect(self.rename)
        weighting = QLabel('Weighting:')
        self.weightsEdit = QLineEdit('[1]')
        self.weightsEdit.returnPressed.connect(self.adjust_weights)
        self.legendToggle = QCheckBox('Legend')
        self.legendToggle.clicked.connect(lambda: self.toggle_legend(parent.axes_frame.current_sps))
        self.colorCoord = QCheckBox('Color by Unit')
        self.colorCoord.clicked.connect(lambda: self.color_coordinate(parent.axes_frame.current_sps))
        self.cycle = QPushButton('Cycle Axes')
        self.cycle.clicked.connect(lambda: self.cycle_subplot(parent.axes_frame.current_sps))
        self.clear = QPushButton('Clear')
        self.clear.clicked.connect(lambda: self.clear_subplot(parent.axes_frame.current_sps))
        self.resetAll = QPushButton('Reset')
        self.resetAll.clicked.connect(self.reset)
        self.insert = QPushButton('Insert')
        self.insert.clicked.connect(lambda: self.insert_subplot(parent.axes_frame.current_sps))
        self.delete = QPushButton('Delete')
        self.delete.clicked.connect(lambda: self.delete_subplot(parent.axes_frame.current_sps))
        self.reorderUp = QPushButton()
        self.reorderUp.setIcon(self.style().standardIcon(getattr(QStyle, 'SP_TitleBarShadeButton')))
        self.reorderUp.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.reorderUp.clicked.connect(lambda: self.reorder(parent.axes_frame.current_sps, 'up'))
        self.reorderDown = QPushButton()
        self.reorderDown.setIcon(self.style().standardIcon(getattr(QStyle, 'SP_TitleBarUnshadeButton')))
        self.reorderDown.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.reorderDown.clicked.connect(lambda: self.reorder(parent.axes_frame.current_sps, 'down'))


        objects = [
            title,
            self.titleEdit,
            weighting,
            self.weightsEdit,
            self.legendToggle,
            self.colorCoord,
            self.cycle,
            self.clear,
            self.resetAll,
            self.insert,
            self.delete,
            self.reorderUp,
            self.reorderDown,
        ]
        positions = [
            (0,0,1,1),
            (0,1,1,5),
            (1,0,1,1),
            (1,1,1,2),
            (2,0,1,1),
            (2,1,1,1),
            (2,2,1,1),
            (1,3,1,1),
            (2,3,1,1),
            (1,4,1,1),
            (2,4,1,1),
            (1,5,1,1),
            (2,5,1,1),
        ]
        for o,p in zip(objects, positions):
            self.grid.addWidget(o,*p)
        self.setLayout(self.grid)

        col_weights = [.01, .01, .01, 1, 1, .01]
        for i,cw in enumerate(col_weights):
            self.grid.setColumnStretch(i,cw)

    def cleanup_axes(self):
        AF = self.parent.axes_frame
        for sp in AF.subplots[0:-1]:  # set all non-base xaxes invisible
            sp.host().xaxis.set_visible(False)
        AF.subplots[-1].host().xaxis.set_visible(True)
#        if sp.index != nplots:
#            # if sp.contents is not None, save xaxis labels
#            sp.host().xaxis.set_visible(False)
#        else:
#            sp.host().xaxis.set_visible(True)
# later on need to override possibly empty axis with saved xaxis labels

    def reset(self):
        pass

    def reorder(self, sps, direction):
        """Reorders selected subplot up or down and updates weighting field."""
        TG = self.parent
        AF = TG.axes_frame
        if len(sps) == 1:
            if direction == 'up':
                inc = -1
            if direction == 'down':
                inc = 1
            sp = sps[0]
            i = sp.index
            j = i+inc
            if 0 <= j < len(AF.subplots):  # do nothing if moving sp up or down would put it past the first/last index
                AF.weights[i], AF.weights[j] = AF.weights[j], AF.weights[i]
                AF.subplots[i], AF.subplots[j] = AF.subplots[j], AF.subplots[i]



                # Remove all the subplots from the figure
                for ax in AF.fig.axes: ax.remove()

                # Make new, blank subplots, associate them with the appropriate Subplot_Manager, and refresh
                gs = gridspec.GridSpec(len(AF.subplots), 1, height_ratios=AF.weights)
                for i, sp in enumerate(AF.subplots):
                    ax = AF.fig.add_subplot(gs[i, 0])
                    sp.axes = [ax]
                    sp.index = i
                    sp.refresh()

#                self.cleanup_axes()
                self.weightsEdit.setText(str(AF.weights))
                AF.select_subplot(None, force_select=[AF.subplots[j]])
                AF.draw()
        else:
            TG.statusBar().showMessage('Select one subplot to reorder')


    def insert_subplot(self, sps):
        """Inserts subplot at top of figure. (Indexed insertion not working)"""
        TG = self.parent
        AF = TG.axes_frame

        # Get indices of currently selected subplots
        reselect = [sp.index for sp in sps]

        # Determine index at which to insert blank subplot
        if len(sps) != 1:
            index = len(AF.subplots)-1
            TG.statusBar().showMessage('No singular subplot selected. Subplot inserted at end.')
        else:
            index = sps[0].index

        # Insert blank Subplot_Manager at position below index (I feel like I shouldn't have to explicitly assign default arguments here, but hey)
        AF.subplots.insert(index+1, Subplot_Manager(TG, [None], order=[None], contents={}, index=None, legend=False, colorCoord=False))
        AF.weights.insert(index+1, 1)

        # Remove all the subplots from the figure
        for ax in AF.fig.axes: ax.remove()

        # Make new, blank subplots, associate them with the appropriate Subplot_Manager, and refresh
        gs = gridspec.GridSpec(len(AF.subplots), 1, height_ratios=AF.weights) #wspace=0.0, hspace=0.0)
        for i, sp in enumerate(AF.subplots):
            ax = AF.fig.add_subplot(gs[i, 0])
            sp.axes = [ax]
            sp.index = i
            sp.refresh()

        # Clean up UI
#        self.cleanup_axes()
        self.weightsEdit.setText(str(AF.weights))
        AF.select_subplot(None, force_select=[AF.subplots[i] for i in reselect])
        AF.draw()


    def delete_subplot(self, sps):
        """Deletes selected subplot(s) and adds contents back into available tree."""
        TG = self.parent
        if sps:
            AF = TG.axes_frame
            if len(AF.subplots) == 1:
                self.clear_subplot(sps)
            else:
                # Delete entries at selected indices from weights, current selection, and Subplot_Managers
                SF = TG.series_frame
                indices = [sp.index for sp in sps]

                print('Deleting: ',indices)
                for i in sorted(indices, reverse=True):
                    AF.available_data = SF.add_to_contents(AF.available_data, AF.subplots[i].contents)
                    SF.populate_tree(AF.available_data, SF.available)  # add contents back into available tree
                    del AF.weights[i]
                    del AF.subplots[i]

                # Remove all the subplots from the figure
                for ax in AF.fig.axes: ax.remove()

                # Make new, blank subplots, associate them with the appropriate Subplot_Manager, and refresh
                gs = gridspec.GridSpec(len(AF.subplots), 1, height_ratios=AF.weights)
                for i, sp in enumerate(AF.subplots):
                    ax = AF.fig.add_subplot(gs[i, 0])
                    sp.axes = [ax]
                    sp.index = i
                    sp.refresh()

                # Clean up UI
#                self.cleanup_axes()
                self.weightsEdit.setText(str(AF.weights))
                AF.select_subplot(None, force_select=[])  # clear selection
                AF.draw()
        else:
            TG.statusBar().showMessage('Select one or more subplots to delete')


    def clear_subplot(self, sps):
        """Adds selected subplot's contents back into available tree, clears axis."""
        TG = self.parent
        if sps:
            AF = TG.axes_frame
            SF = TG.series_frame
            SF.plotted.clear()
            for sp in sps:
                AF.available_data = SF.add_to_contents(AF.available_data, sp.contents)
                SF.populate_tree(AF.available_data, SF.available)
                SF.search(SF.searchAvailable, SF.available, AF.available_data)
                sp.contents = {}
                sp.order = [None]
                sp.refresh()
#            if len(sps) > 1: TG.statusBar().showMessage('Cleared subplots: {}'.format(sorted([sp.index for sp in sps])))
#            else: TG.statusBar().showMessage('Cleared subplot: {}'.format(sps[0].index))
        else:
            TG.statusBar().showMessage('Select one or more subplots to clear')


    def toggle_legend(self, sps):
        """Toggles legend display of selected subplot."""
        if sps:
            if len(sps) == 1:
                sp = sps[0]
                sp.legend = not sp.legend
                sp.refresh()
            else:
                any_legend = any([sp.legend for sp in sps])
                for sp in sps:
                    sp.legend = not any_legend
                    sp.refresh()
        else:
            TG = self.parent
            self.legendToggle.setCheckable(False)
            TG.statusBar().showMessage('Select one or more subplots to toggle legend')


    def color_coordinate(self, sps):
        """Recolors lines and axes in selected subplot to correspond by unit type."""
        if sps:
            if len(sps) == 1:
                sp = sps[0]
                sp.colorCoord = not sp.colorCoord
                sp.refresh()
            else:
                any_coord = any([sp.colorCoord for sp in sps])
                for sp in sps:
                    sp.colorCoord = not any_coord
                    sp.refresh()
        else:
            TG = self.parent
            self.colorCoord.setCheckable(False)
            TG.statusBar().showMessage('Select one or more subplots to toggle color coordination')


    def cycle_subplot(self, sps):
        """Cycles through unit order permutations."""
        if sps:
            for sp in sps:
                perms = [list(p) for p in sorted(itertools.permutations(sp.order))]
                i = perms.index(sp.order)
                sp.order = perms[(i+1)%len(perms)]
                sp.refresh()
        else:
            TG = self.parent
            TG.statusBar().showMessage('Select one or more subplots to cycle unit plotting order')


    def adjust_weights(self):
        """Adjusts subplot vertical aspect ratios based on provided list of weights (or sequence of digits)."""
        TG = self.parent
        AF = TG.axes_frame
        weights = []
        for i in self.weightsEdit.text():  # parse weighting input
            if i.isdigit():
                weights.append(int(i))
            elif i in ', []':  # ignore commas, spaces, and brackets
                continue
            else:
                TG.statusBar().showMessage('Only integer inputs <10 allowed')
                return
        if len(weights) != len(AF.subplots):
            TG.statusBar().showMessage('{} weights provided for figure with {} subplots'.format(len(weights), len(AF.subplots)))
            return
        g = functools.reduce(math.gcd, weights)
        weights = [w//g for w in weights]  # simplify weights by their greatest common denominator (eg [2,2,4] -> [1,1,2])
        AF.weights = weights
        self.weightsEdit.setText(str(AF.weights))
        gs = gridspec.GridSpec(len(AF.subplots), 1, height_ratios=weights)
        for i, sp in enumerate(AF.subplots):
            sp.host().set_position(gs[i].get_position(AF.fig))
        AF.draw()


    def rename(self):
        """Renames figure and changes save path to new figure title."""
        TG = self.parent
        AF = TG.axes_frame
        fig_title = re.sub('[\\\\.]', '', self.titleEdit.text())  # get rid of any backslashes or dots
        if not fig_title:
            AF.fig.suptitle('')
            fig_title = 'New_Figure'
        else:
            AF.fig.suptitle(fig_title, fontsize=20)
#        input_path = self.pathEdit.text()
#        try:
#            save_dir = input_path[:input_path.rindex('\\')]  # path string up until last backslash occurrence
#        except ValueError:
#            save_dir = os.getcwd()
#        try:
#            ext = input_path[input_path.rindex('.'):]  # path string from last . occurrence to end
#        except ValueError:
#            ext = '.jpg'  # default to JPG format
#        self.pathEdit.setText(save_dir + '\\' + fig_title + ext)
        AF.draw()

    def save_figure(self):
        ### Disconnected from button, but still should be connected to menubar action (TBI)
        """Saves figure to displayed directory. If no path or extension is given, defaults are current directory and .jpg."""
        TG = self.parent
        AF = TG.axes_frame
        AF.select_subplot(None, force_select=[])  # force deselect before save (no highlighted axes in saved figure)
        AF.draw()
        plt.savefig(self.pathEdit.text(), dpi=300, format='jpg', transparent=True, bbox_inches='tight')
        TG.statusBar().showMessage('Saved to {}'.format(self.pathEdit.text()))


