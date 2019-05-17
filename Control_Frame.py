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
        self.grid.addWidget(title,0,0)

        self.titleEdit = QLineEdit('New_Figure')
        self.titleEdit.returnPressed.connect(self.rename)
        self.grid.addWidget(self.titleEdit,0,1,1,5)

        weighting = QLabel('Weighting:')
        self.grid.addWidget(weighting,1,0,2,1)

        self.weightsEdit = QLineEdit('[1]')
        self.weightsEdit.returnPressed.connect(self.adjust_weights)
        self.grid.addWidget(self.weightsEdit,1,1,2,2)

        selectStart = QLabel('Start Timestamp')
        self.grid.addWidget(selectStart,3,0,2,1)

        self.selectStart = QLineEdit('2018-12-06 00:00')
        self.selectStart.returnPressed.connect(self.time_filter)
        self.grid.addWidget(self.selectStart,3,1,2,2)

        selectEnd = QLabel('End Timestamp')
        self.grid.addWidget(selectEnd,5,0,2,1)

        self.selectEnd = QLineEdit('2018-12-09 00:00')  # dummy start/end from PHI_HK, default will be None
        self.selectEnd.returnPressed.connect(self.time_filter)
        self.grid.addWidget(self.selectEnd,5,1,2,2)

        self.cycle = QPushButton('Cycle Axes')
        self.cycle.clicked.connect(lambda: self.cycle_subplot(parent.axes_frame.current_sps))
        self.grid.addWidget(self.cycle,1,3,2,1)

        self.legendToggle = QCheckBox('Legend')
        self.legendToggle.clicked.connect(lambda: self.toggle_legend(parent.axes_frame.current_sps))
        self.grid.addWidget(self.legendToggle,3,3,2,1)

        self.colorCoord = QCheckBox('Color by Unit')
        self.colorCoord.clicked.connect(lambda: self.color_coordinate(parent.axes_frame.current_sps))
        self.grid.addWidget(self.colorCoord,5,3,2,1)

        self.insert = QPushButton('Insert')
        self.insert.clicked.connect(lambda: self.insert_subplot(parent.axes_frame.current_sps))
        self.grid.addWidget(self.insert,1,4,2,1)

        self.delete = QPushButton('Delete')
        self.delete.clicked.connect(lambda: self.delete_subplot(parent.axes_frame.current_sps))
        self.grid.addWidget(self.delete,3,4,2,1)

        self.clear = QPushButton('Clear')
        self.clear.clicked.connect(lambda: self.clear_subplot(parent.axes_frame.current_sps))
        self.grid.addWidget(self.clear,5,4,2,1)

        self.reorderUp = QPushButton()
        self.reorderUp.setIcon(self.style().standardIcon(getattr(QStyle, 'SP_TitleBarShadeButton')))
        self.reorderUp.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.reorderUp.clicked.connect(lambda: self.reorder(parent.axes_frame.current_sps, 'up'))
        self.grid.addWidget(self.reorderUp,1,5,3,1)

        self.reorderDown = QPushButton()
        self.reorderDown.setIcon(self.style().standardIcon(getattr(QStyle, 'SP_TitleBarUnshadeButton')))
        self.reorderDown.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.reorderDown.clicked.connect(lambda: self.reorder(parent.axes_frame.current_sps, 'down'))
        self.grid.addWidget(self.reorderDown,4,5,3,1)

        self.setLayout(self.grid)

        col_weights = [.01, .01, .01, 1, 1, .01]
        for i,cw in enumerate(col_weights):
            self.grid.setColumnStretch(i,cw)

    def cleanup_axes(self):
        AF = self.parent.axes_frame
        FS = self.parent.figure_settings
        for sp in AF.subplots[:-1]:  # set all xaxes invisible
            sp.host().tick_params(axis='x', which='major', labelbottom=False)
            for ax in sp.axes: ax.tick_params(axis='y', labelsize=FS.tickSize.value())
            # if FS.majorX.isChecked():
            sp.host().grid(b=True, axis='x')
        base_X = AF.subplots[-1].host()
        base_X.grid(b=True, axis='x')
        plt.sca(base_X)
        plt.xticks(rotation=FS.tickRot.value(), ha='right', fontsize=FS.tickSize.value())
        plt.yticks(fontsize=FS.tickSize.value())


    def time_filter(self):
        self.start = pd.to_datetime(self.selectStart.text())
        self.end = pd.to_datetime(self.selectEnd.text())
        if not self.start: self.start = min([self.groups[name].data.index[0] for name in self.groups.keys()])
        if not self.end: self.end = max([self.groups[name].data.index[-1] for name in self.groups.keys()])

        # doch you do need them because they're strings (I think) (dunno if it'll stay that way)
        self.timespan = pd.to_datetime(self.end)-pd.to_datetime(self.start)  # shouldn't need to use pd.to_datetime here, self.start/end should already be datetimes at this point
        if self.timespan < dt.timedelta(days=1):
            self.dotsize = 0.8
        else:
            self.dotsize = 0.5
        if self.timespan >= dt.timedelta(days=2) and self.timespan < dt.timedelta(days=4):
            self.dateformat = mdates.DateFormatter('%d/%b %H:%M')
            self.major_locator = mdates.DayLocator()
        elif self.timespan >= dt.timedelta(days=4):
            self.dateformat = mdates.DateFormatter('%d/%b %H:%M')
            self.major_locator = mdates.DayLocator()
        else:
            self.dateformat = mdates.DateFormatter('%d %b %Y %H:%M')
            self.major_locator = mdates.HourLocator(interval=2)
        self.parent.axes_frame.refresh_all()

    def reorder(self, sps, direction):
        """Reorders selected subplot up or down and updates weighting field."""
        TG = self.parent
        AF = TG.axes_frame
        FS = TG.figure_settings
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
                AF.refresh_all()
        else:
            TG.statusBar().showMessage('Select one subplot to reorder')


    def insert_subplot(self, sps):
        """Inserts subplot at top of figure. (Indexed insertion not working)"""
        TG = self.parent
        AF = TG.axes_frame

        # Determine index at which to insert blank subplot
        if len(sps) != 1:
            index = len(AF.subplots)-1
            TG.statusBar().showMessage('No singular subplot selected. Subplot inserted at end.')
        else:
            index = sps[0].index

        # Insert blank Subplot_Manager at position below index (I feel like I shouldn't have to explicitly assign default arguments here, but hey)
        AF.subplots.insert(index+1, Subplot_Manager(TG, [None], order=[None], contents={}, index=None, legend=False, colorCoord=False))
        AF.weights.insert(index+1, 1)
        AF.refresh_all()


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

                for i in sorted(indices, reverse=True):
                    AF.available_data = SF.add_to_contents(AF.available_data, AF.subplots[i].contents)
                    SF.populate_tree(AF.available_data, SF.available)  # add contents back into available tree
                    del AF.weights[i]
                    del AF.subplots[i]
                AF.current_sps = []  # deselect everything
                AF.refresh_all()
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
            AF.refresh_all()
#            if len(sps) > 1: TG.statusBar().showMessage('Cleared subplots: {}'.format(sorted([sp.index for sp in sps])))
#            else: TG.statusBar().showMessage('Cleared subplot: {}'.format(sps[0].index))
        else:
            TG.statusBar().showMessage('Select one or more subplots to clear')


    def toggle_legend(self, sps):
        """Toggles legend display of selected subplot."""
        TG = self.parent
        if sps:
            AF = TG.axes_frame
            if len(sps) == 1:
                sp = sps[0]
                sp.legend = not sp.legend
            else:
                any_legend = any([sp.legend for sp in sps])
                for sp in sps:
                    sp.legend = not any_legend
            AF.refresh_all()
        else:
            self.legendToggle.setCheckable(False)
            TG.statusBar().showMessage('Select one or more subplots to toggle legend')


    def color_coordinate(self, sps):
        """Recolors lines and axes in selected subplot to correspond by unit type."""
        TG = self.parent
        if sps:
            AF = TG.axes_frame
            if len(sps) == 1:
                sp = sps[0]
                sp.colorCoord = not sp.colorCoord
            else:
                any_coord = any([sp.colorCoord for sp in sps])
                for sp in sps:
                    sp.colorCoord = not any_coord
            AF.refresh_all()
        else:

            self.colorCoord.setCheckable(False)
            TG.statusBar().showMessage('Select one or more subplots to toggle color coordination')


    def cycle_subplot(self, sps):
        """Cycles through unit order permutations."""
        TG = self.parent
        if sps:
            AF = TG.axes_frame
            for sp in sps:
                perms = [list(p) for p in sorted(itertools.permutations(sp.order))]
                i = perms.index(sp.order)
                sp.order = perms[(i+1)%len(perms)]
            AF.refresh_all()
        else:
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
        AF.refresh_all()

    def rename(self):
        """Renames figure and changes save path to new figure title."""
        TG = self.parent
        AF = TG.axes_frame
        FS = TG.figure_settings
        fig_title = re.sub('[\\\\.]', '', self.titleEdit.text())  # get rid of any backslashes or dots
        if not fig_title:
            AF.fig.suptitle('')
            fig_title = 'New_Figure'
        else:
            AF.fig.suptitle(fig_title, fontsize=FS.titleSize.value())
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


