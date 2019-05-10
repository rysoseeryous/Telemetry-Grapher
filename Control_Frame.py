# -*- coding: utf-8 -*-
"""
Created on Mon May  6 14:59:10 2019

@author: seery
"""
from PyQt5.QtWidgets import *

class Control_Frame(QWidget):
    """Contains all buttons for controlling the organization of subplots and saving the figure."""
    def __init__(self, parent):
        super().__init__()
        self.parent = parent
        self.grid = QGridLayout()

        self.reorderUp = QPushButton()
        self.reorderUp.setIcon(self.style().standardIcon(getattr(QStyle, 'SP_TitleBarShadeButton')))
        self.reorderUp.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.reorderUp.clicked.connect(lambda: self.reorder(parent.axes_frame.current_sps, 'up'))
        self.reorderDown = QPushButton()
        self.reorderDown.setIcon(self.style().standardIcon(getattr(QStyle, 'SP_TitleBarUnshadeButton')))
        self.reorderDown.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.reorderDown.clicked.connect(lambda: self.reorder(parent.axes_frame.current_sps, 'down'))
        self.insert = QPushButton('Insert')
        self.insert.clicked.connect(lambda: self.insert_subplot(parent.axes_frame.current_sps))
        self.delete = QPushButton('Delete')
        self.delete.clicked.connect(lambda: self.delete_subplot(parent.axes_frame.current_sps))
        self.clear = QPushButton('Clear Subplot')
        self.clear.clicked.connect(lambda: self.clear_subplot(parent.axes_frame.current_sps))
        self.legendToggle = QCheckBox('Legend')
        self.legendToggle.clicked.connect(lambda: self.toggle_legend(parent.axes_frame.current_sps))
        self.cycle = QPushButton('Cycle Primary')
        self.cycle.clicked.connect(lambda: self.cycle_subplot(parent.axes_frame.current_sps))
        self.colorCoord = QCheckBox('Color by Unit')
        self.colorCoord.clicked.connect(lambda: self.color_coordinate(parent.axes_frame.current_sps))
        self.weighting = QLabel('Weighting:')
        self.weightsEdit = QLineEdit('[1]')
        self.weightsEdit.returnPressed.connect(self.adjust_weights)
        self.title = QLabel('Figure title:')
        self.titleEdit = QLineEdit('New_Figure')
        self.titleEdit.returnPressed.connect(self.rename)
        self.save = QPushButton('Save')
        self.save.clicked.connect(self.save_figure)
        self.pathEdit = QLineEdit(os.getcwd()+'\\'+self.titleEdit.text()+'.jpg')

        col_weights = [1, 1, 1, 1, 100]
        for i,cw in enumerate(col_weights):
            self.grid.setColumnStretch(i,cw)
        objects = [
            self.reorderUp,
            self.reorderDown,
            self.insert,
            self.delete,
            self.clear,
            self.legendToggle,
            self.colorCoord,
            self.cycle,
            self.weighting,
            self.title,
            self.save,
            self.weightsEdit,
            self.titleEdit,
            self.pathEdit,
        ]
        positions = [
            (0,0,3,1),
            (3,0,3,1),
            (0,1,2,1),
            (2,1,2,1),
            (4,1,2,1),
            (0,2,2,1),
            (2,2,2,1),
            (4,2,2,1),
            (0,3,2,1),
            (2,3,2,1),
            (4,3,2,1),
            (0,4,2,1),
            (2,4,2,1),
            (4,4,2,1),
        ]
        for o,p in zip(objects, positions):
            self.grid.addWidget(o,*p)
        self.setLayout(self.grid)

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
            if 0 <= i+inc < len(AF.subplots):  # do nothing if moving sp up or down would put it past the first/last index
                AF.weights[i], AF.weights[i+inc] = AF.weights[i+inc], AF.weights[i]
                AF.subplots[i], AF.subplots[i+inc] = AF.subplots[i+inc], AF.subplots[i]
                for i,sp in enumerate(AF.subplots): sp.index = i
                gs = gridspec.GridSpec(len(AF.subplots), 1, height_ratios=AF.weights)
                for i, sp in enumerate(AF.subplots):
                    sp.host().set_position(gs[i].get_position(AF.fig))
                self.cleanup_axes()
                AF.draw()
        else:
            TG.statusBar().showMessage('Select one subplot to reorder')

    def insert_subplot(self, sps):
        ### Currently breaks everything
        """Inserts subplot at top of figure. (Indexed insertion not working)"""
        TG = self.parent
        AF = TG.axes_frame



        nplots = len(AF.subplots)
#        if len(sps) != 1:
#            index = nplots-1
#            TG.statusBar().showMessage('No singular subplot selected. Subplot inserted at end.')
#        else:
#            index = sps[0].index
        index = nplots-1  #always insert at end
        AF.weights.insert(index+1,1)
        gs = gridspec.GridSpec(nplots+1, 1, height_ratios=AF.weights)
        for i, sp in enumerate(AF.subplots):
            if i <= index:
                sp.host().set_position(gs[i].get_position(AF.fig))
            else:
                sp.host().set_position(gs[i+1].get_position(AF.fig))
        ax = AF.fig.add_subplot(gs[index+1])

        """At this point we have _appended_ an axes object to AF.fig.axes and displayed it in the correct position."""

        AF.subplots.insert(index+1, Subplot_Manager(TG, ax, index=index+1))  # AF.subplots kept in displayed order
        for i,sp in enumerate(AF.subplots): sp.index = i
#        for sp in AF.subplots:
#            print(sp.index, sp)
#        print('')
        self.cleanup_axes()
        self.weightsEdit.setText(str(AF.weights))
        AF.draw()

    def delete_subplot(self, sps):
        """Deletes selected subplot(s) and adds contents back into available tree."""
        TG = self.parent
        if sps:
            AF = TG.axes_frame
            if len(AF.subplots) == 1:
                self.clear_subplot(sps)
            else:
                SF = TG.series_frame
                indices = [sp.index for sp in sps]
                for i in sorted(indices, reverse=True):
                    del AF.weights[i]
                    SF.populate_tree(AF.subplots[i].contents, SF.available)  # add contents back into available tree
                    del AF.current_sps[AF.current_sps.index(AF.subplots[i])]  # remove from selection
                    AF.subplots[i].host().remove()  # remove from figure
                    del AF.subplots[i]  # delete from subplots list
                gs = gridspec.GridSpec(len(AF.subplots), 1, height_ratios=AF.weights)
                for i, sp in enumerate(AF.subplots):
                    sp.index = i
                    sp.host().set_position(gs[i].get_position(AF.fig))
                self.cleanup_axes()
                self.weightsEdit.setText(str(AF.weights))
                AF.draw()
                AF.select_subplot(None, force_select=[])  # clear selelection
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
            if len(sps) > 1: TG.statusBar().showMessage('Cleared subplots: {}'.format(sorted([sp.index for sp in sps])))
            else: TG.statusBar().showMessage('Cleared subplot: {}'.format(sps[0].index))
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
        self.weightsEdit.setText(str(weights))
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
        input_path = self.pathEdit.text()
        try:
            save_dir = input_path[:input_path.rindex('\\')]  # path string up until last backslash occurrence
        except ValueError:
            save_dir = os.getcwd()
        try:
            ext = input_path[input_path.rindex('.'):]  # path string from last . occurrence to end
        except ValueError:
            ext = '.jpg'  # default to JPG format
        self.pathEdit.setText(save_dir + '\\' + fig_title + ext)
        AF.draw()

    def save_figure(self):
        """Saves figure to displayed directory. If no path or extension is given, defaults are current directory and .jpg."""
#         Hijacking this function to test twinx() error
#        TG = self.parent
#        AF = TG.axes_frame
#        sp = AF.current_sps[0]
#        sp.host().plot([1,2,3,4])
#        AF.draw()

        # real function
        TG = self.parent
        AF = TG.axes_frame
        AF.select_subplot(None, force_select=[])  # force deselect before save (no highlighted axes in saved figure)
        AF.draw()
        plt.savefig(self.pathEdit.text(), dpi=300, format='jpg', transparent=True, bbox_inches='tight')
        TG.statusBar().showMessage('Saved to {}'.format(self.pathEdit.text()))


