# -*- coding: utf-8 -*-
"""
Created on Thu Jun 13 15:47:08 2019

@author: seery
"""
import re
import itertools
import datetime as dt
import matplotlib.dates as mdates
import matplotlib.pyplot as plt

from PyQt5.QtWidgets import (QWidget, QGridLayout, QStyle, QSizePolicy,
                             QPushButton, QLabel, QLineEdit, QCheckBox,
                             QSpinBox, QComboBox,
                             QDateTimeEdit)
from PyQt5.QtCore import QDateTime, QDate

from ..internal.subplot_manager import Subplot_Manager

class Control_Frame(QWidget):
    """Contains all buttons for controlling subplot organization."""

    def __init__(self, parent):
        super().__init__()
        self.parent = parent
        grid = QGridLayout()
        self.title_edited = False
        self.weights_edited = False
        self.legend_dict = {
            'Outside Right': 'center left',
            'Outside Top': 'lower center',
            'Upper Left': 'upper left',
            'Upper Center': 'upper center',
            'Upper Right': 'upper right',
            'Center Left': 'center left',
            'Center Right': 'center right',
            'Lower Left': 'lower left',
            'Lower Center': 'lower center',
            'Lower Right': 'lower right',
            }

        title = QLabel('Title:')
        grid.addWidget(title, 0, 0)

        self.titleEdit = QLineEdit('New_Figure')
        self.titleEdit.editingFinished.connect(self.rename)
        self.titleEdit.textEdited.connect(self.tte)
        grid.addWidget(self.titleEdit, 0, 1, 1, 2)

        weighting = QLabel('Weights:')
        grid.addWidget(weighting, 1, 0)

        self.weightsEdit = QLineEdit('[1]')
        self.weightsEdit.editingFinished.connect(self.adjust_weights)
        self.weightsEdit.textEdited.connect(self.wte)
        grid.addWidget(self.weightsEdit, 1, 1, 1, 2)

        selectStart = QLabel('Start:')
        grid.addWidget(selectStart, 2, 0)

        self.selectStart = QDateTimeEdit()
        self.selectStart.setDisplayFormat('yyyy-MM-dd hh:mm:ss')
        self.selectStart.dateTimeChanged.connect(self.time_filter)
        grid.addWidget(self.selectStart, 2, 1)

        self.minTS = QPushButton('Min')
        self.minTS.setFixedWidth(30)
        self.minTS.clicked.connect(self.set_start_min)
        grid.addWidget(self.minTS, 2, 2)

        selectEnd = QLabel('End:')
        grid.addWidget(selectEnd, 3, 0)

        self.selectEnd = QDateTimeEdit(QDate.currentDate())
        self.selectEnd.setDisplayFormat('yyyy-MM-dd hh:mm:ss')
        self.selectEnd.dateTimeChanged.connect(self.time_filter)
        grid.addWidget(self.selectEnd, 3, 1)

        self.maxTS = QPushButton('Max')
        self.maxTS.setFixedWidth(30)
        self.maxTS.clicked.connect(self.set_end_max)
        grid.addWidget(self.maxTS, 3, 2)

        self.colorCoord = QCheckBox('Color by Unit')
        slot = lambda: self.color_coordinate(parent.axes_frame.current_sps)
        self.colorCoord.clicked.connect(slot)
        grid.addWidget(self.colorCoord, 0, 3, 1, 2)

        self.legendToggle = QCheckBox('Show Legend')
        slot = lambda: self.toggle_legend(parent.axes_frame.current_sps)
        self.legendToggle.clicked.connect(slot)
        grid.addWidget(self.legendToggle, 1, 3, 1, 2)

        legendColumns = QLabel('Columns')
        grid.addWidget(legendColumns, 2, 3)

        self.legendColumns = QSpinBox()
        self.legendColumns.setRange(1, 10)
        slot = lambda: self.set_legend_columns(parent.axes_frame.current_sps)
        self.legendColumns.valueChanged.connect(slot)
        grid.addWidget(self.legendColumns, 2, 4)

        self.legendPosition = QComboBox()
        self.legendPosition.addItems(list(self.legend_dict.keys()))
        slot = lambda: self.set_legend_position(parent.axes_frame.current_sps)
        self.legendPosition.currentIndexChanged.connect(slot)

        grid.addWidget(self.legendPosition, 3, 3, 1, 2)

        self.cycle = QPushButton('Cycle Axes')
        slot = lambda: self.cycle_subplot(parent.axes_frame.current_sps)
        self.cycle.clicked.connect(slot)
        grid.addWidget(self.cycle, 0, 5)

        self.insert = QPushButton('Insert')
        slot = lambda: self.insert_subplot(parent.axes_frame.current_sps)
        self.insert.clicked.connect(slot)
        grid.addWidget(self.insert, 1, 5)

        self.delete = QPushButton('Delete')
        self.delete.clicked.connect(lambda: self.delete_subplot(parent.axes_frame.current_sps))
        grid.addWidget(self.delete, 2, 5)

        self.clear = QPushButton('Clear')
        self.clear.clicked.connect(lambda: self.clear_subplot(parent.axes_frame.current_sps))
        grid.addWidget(self.clear, 3, 5)

        self.reorderUp = QPushButton()
        self.reorderUp.setIcon(self.style().standardIcon(getattr(QStyle, 'SP_TitleBarShadeButton')))
        self.reorderUp.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.reorderUp.clicked.connect(lambda: self.reorder(parent.axes_frame.current_sps, 'up'))
        grid.addWidget(self.reorderUp, 0, 6, 2, 1)

        self.reorderDown = QPushButton()
        self.reorderDown.setIcon(self.style().standardIcon(getattr(QStyle, 'SP_TitleBarUnshadeButton')))
        self.reorderDown.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.reorderDown.clicked.connect(lambda: self.reorder(parent.axes_frame.current_sps, 'down'))
        grid.addWidget(self.reorderDown, 2, 6, 2, 1)

        col_weights = [.01, .01, .01, 1, 1, 1, .01]
        for i,cw in enumerate(col_weights):
            grid.setColumnStretch(i,cw)
        self.setLayout(grid)

    def wte(self):
        self.weights_edited = True

    def tte(self):
        self.title_edited = True

    def cleanup_axes(self):
        """Manages axes ticks, tick labels, and gridlines for the whole figure."""
        AB = self.parent
        AF = AB.axes_frame
        FS = AB.figure_settings

        self.timespan = self.end - self.start
        if self.timespan >= dt.timedelta(days=4):
#            self.dateformat = mdates.DateFormatter('%ggs %b %Y')
            self.major_locator = mdates.DayLocator()
            self.minor_locator = mdates.HourLocator(interval=12)
        elif self.timespan >= dt.timedelta(days=2) and self.timespan < dt.timedelta(days=4):
#            self.dateformat = mdates.DateFormatter('%d/%b %H:%M')
            self.major_locator = mdates.DayLocator()
            self.minor_locator = mdates.HourLocator(interval=12)
        else:
#            self.dateformat = mdates.DateFormatter('%d %b %Y %H:%M dalla dalla biyul yall')
            self.major_locator = mdates.HourLocator(interval=2)
            self.minor_locator = mdates.HourLocator(interval=1)

        for i, sp in enumerate(AF.subplots):
            # All subplots
            self.toggle_grid(sp)
            for ax in sp.axes:
                ax.tick_params(axis='y', labelsize=FS.tickSize.value())
                ax.xaxis.set_major_locator(self.major_locator)
                ax.xaxis.set_minor_locator(self.minor_locator)
            # Lowest subplot
            if i == len(AF.subplots)-1:  # Bottom-most subplot only
                if not sp.contents:  # maybe in the future: go through subplots, find one with contents, use its xaxis ticks/labels as base xaxis ticks/labels (quality of life)
                    # If subplot is empty, don't show xaxis ticks
                    sp.host().tick_params(axis='x', labelbottom=False, bottom=False)
                else:
                    # Tell the host axes' xaxis it's plotting dates
                    sp.host().xaxis_date()
                    sp.host().xaxis.set_major_formatter(mdates.DateFormatter(FS.timestamp_format))
                    # Give focus to host axes
                    plt.sca(sp.host())
                    sp.host().tick_params(axis='x', labelbottom=True, bottom=True)
                    plt.xticks(rotation=FS.tickRot.value(), ha='right', fontsize=FS.tickSize.value())
                plt.yticks(fontsize=FS.tickSize.value())

            # All other subplots
            else:
                sp.host().tick_params(axis='x', which='major', labelbottom=False)

    def toggle_grid(self, sp):
        """Controls whether X/Y, major/minor gridlines are displayed in subplot sp."""
        AB = self.parent
        FS = AB.figure_settings
        linestyles = ['-', '--', ':', '-.']

        if FS.majorXgrid.isChecked():
            sp.host().xaxis.grid(which='major')
        if FS.minorXgrid.isChecked():
            sp.host().minorticks_on()
#            sp.host().tick_params(axis='x', which='minor', bottom=True)
            sp.host().xaxis.grid(which='minor')
        if FS.majorYgrid.isChecked():
            for i, ax in enumerate(sp.axes):
                ax.yaxis.grid(which='major', linestyle=linestyles[i%len(linestyles)])
        if FS.minorYgrid.isChecked():
            for i, ax in enumerate(sp.axes):
                ax.minorticks_on()  # turns both x and y on, don't know how to only get it on one axis
#                ax.tick_params(axis='y', which='minor')
                ax.yaxis.grid(b=True, which='minor', linestyle=linestyles[i%len(linestyles)])

    def cap_start_end(self):
        """Limits the figure start and end datetimes by the extent of the loaded data."""
        AB = self.parent
        try:
            data_start = min([AB.groups[name].data.index[0] for name in AB.groups])
#            print(type(data_start), data_start)
#            print(type(self.start), self.start)
            self.start = max([data_start, self.start])
            data_end = max([AB.groups[name].data.index[-1] for name in AB.groups])
            self.end = min([data_end, self.end])

            self.selectStart.setMinimumDateTime(data_start)
            self.selectStart.setMaximumDateTime(self.end)
            self.selectEnd.setMaximumDateTime(data_end)
            self.selectEnd.setMinimumDateTime(self.start)
        except ValueError:
            self.selectStart.setMinimumDateTime(dt.datetime.strptime('2000-01-01 00:00:00', '%Y-%m-%d  %H:%M:%S'))
            self.selectStart.setMaximumDateTime(self.end)
            self.selectEnd.setMaximumDateTime(QDateTime.currentDateTime())
            self.selectEnd.setMinimumDateTime(self.start)
        return self.start, self.end

    def set_start_min(self):
        self.selectStart.setDateTime(self.selectStart.minimumDateTime())

    def set_end_max(self):
        self.selectEnd.setDateTime(self.selectEnd.maximumDateTime())

    def time_filter(self):
        """Determines timestamp format and major/minor x-axis locators based on the plotted timespan."""
        AB = self.parent
        AF = AB.axes_frame
        self.start = self.selectStart.dateTime().toPyDateTime()
        self.end = self.selectEnd.dateTime().toPyDateTime()
        self.start, self.end = self.cap_start_end()
        AF.refresh_all()

    def reorder(self, sps, direction):
        """Reorders selected subplot up or down."""
        AB = self.parent
        AF = AB.axes_frame
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
                AF.current_sps = [AF.subplots[i]]
                AF.refresh_all()
        else:
            AB.statusBar().showMessage('Select one subplot to reorder')

    def insert_subplot(self, sps):
        """Inserts blank subplot below selected subplot."""
        AB = self.parent
        AF = AB.axes_frame

        # Determine index at which to insert blank subplot
        if len(sps) != 1:
            index = len(AF.subplots)-1
#            AB.statusBar().showMessage('No singular subplot selected. Subplot inserted at end.')
        else:
            index = sps[0].index

        # Insert blank Subplot_Manager at position below index (I feel like I shouldn't have to explicitly assign default arguments here, but hey)
        AF.subplots.insert(index+1, Subplot_Manager(AB, [None], order=[None], contents={}, index=None, legend=False, colorCoord=False))
        AF.weights.insert(index+1, 1)
        AF.refresh_all()

    def delete_subplot(self, sps):
        """Deletes selected subplot(s) and adds contents back into available tree."""
        AB = self.parent
        if sps:
            AF = AB.axes_frame
            SF = AB.series_frame
            indices = [sp.index for sp in sps]
            for i in reversed(indices):
                if len(AF.subplots) == 1:
                    self.clear_subplot(sps)
                else:
                # Delete entries at selected indices from weights, current selection, and Subplot_Managers
                    AF.available_data = SF.add_to_contents(AF.available_data, AF.subplots[i].contents)
                    SF.populate_tree(AF.available_data, SF.available)  # add contents back into available tree
                    del AF.weights[i]
                    del AF.subplots[i]
            AF.current_sps = []  # deselect everything
            AF.refresh_all()
        else:
            AB.statusBar().showMessage('Select one or more subplots to delete')

    def clear_subplot(self, sps):
        """Adds selected subplot's contents back into available tree, clears axis."""
        AB = self.parent
        if sps:
            AF = AB.axes_frame
            SF = AB.series_frame
            SF.plotted.clear()
            for sp in sps:
                AF.available_data = SF.add_to_contents(AF.available_data, sp.contents)
                SF.populate_tree(AF.available_data, SF.available)
                SF.search(SF.searchAvailable, SF.available, AF.available_data)
                sp.contents = {}
                sp.order = [None]
                sp.plot(skeleton=True)
            AF.refresh_all()
#            if len(sps) > 1: AB.statusBar().showMessage('Cleared subplots: {}'.format(sorted([sp.index for sp in sps])))
#            else: AB.statusBar().showMessage('Cleared subplot: {}'.format(sps[0].index))
        else:
            AB.statusBar().showMessage('Select one or more subplots to clear')

    def color_coordinate(self, sps):
        """Coordinates color of lines and axis labels in selected subplot(s) by unit type."""
        AB = self.parent
        if sps:
            AF = AB.axes_frame
            if len(sps) == 1:
                sp = sps[0]
                sp.colorCoord = not sp.colorCoord
            else:
                any_coord = any([sp.colorCoord for sp in sps])
                for sp in sps:
                    sp.colorCoord = not any_coord
            AF.refresh_all()
        else:
            AB.statusBar().showMessage('Select one or more subplots to toggle color coordination')

    def toggle_legend(self, sps):
        """Toggles legend display of selected subplot(s)."""
        AB = self.parent
        if sps:
            AF = AB.axes_frame
            if len(sps) == 1:
                sp = sps[0]
                sp.legend = not sp.legend
            else:
                any_legend = any([sp.legend for sp in sps])
                for sp in sps:
                    sp.legend = not any_legend
            AF.refresh_all()
        else:
            AB.statusBar().showMessage('Select one or more subplots to toggle legend')

    def set_legend_columns(self, sps):
        AB = self.parent
        AF = AB.axes_frame
        for sp in sps:
            sp.ncols = self.legendColumns.value()
        AF.refresh_all()

    def set_legend_position(self, sps):
        AB = self.parent
        AF = AB.axes_frame
        for sp in sps:
            sp.legendLocation = self.legendPosition.currentText()
        AF.refresh_all()

    def cycle_subplot(self, sps):
        """Cycles through unit order permutations of selected subplot(s)."""
        AB = self.parent
        if sps:
            AF = AB.axes_frame
            for sp in sps:
                perms = [list(p) for p in sorted(itertools.permutations(sp.order))]
                i = perms.index(sp.order)
                sp.order = perms[(i+1)%len(perms)]
            AF.refresh_all()
        else:
            AB.statusBar().showMessage('Select one or more subplots to cycle unit plotting order')

    def adjust_weights(self):
        """Adjusts subplot vertical aspect ratios based on provided list of weights or sequence of digits."""
        if self.weights_edited:
            AB = self.parent
            AF = AB.axes_frame
            weights = []
            for i in self.weightsEdit.text():  # parse weighting input
                if i.isdigit():
                    weights.append(int(i))
                elif i in ', []':  # ignore commas, spaces, and brackets
                    continue
                else:
                    AB.statusBar().showMessage('Only integer inputs <10 allowed')
                    return
            if len(weights) != len(AF.subplots):
                AB.statusBar().showMessage('Figure has {} subplots but {} weights were provided'.format(len(AF.subplots), len(weights)))
                return
            AF.weights = weights
            AF.refresh_all()
            self.weights_edited = False

    def rename(self):
        """Renames figure."""
        if self.title_edited:
            AB = self.parent
            AF = AB.axes_frame
            FS = AB.figure_settings
            fig_title = re.sub('[\\\\.]', '', self.titleEdit.text())  # get rid of any backslashes or dots
            if not fig_title:
                AF.fig.suptitle('')
                fig_title = 'New_Figure'
            else:
                AF.fig.suptitle(fig_title, fontsize=FS.titleSize.value())
                AB.filename = fig_title
            AF.draw()
            AB.saved = False
            self.title_edited = False