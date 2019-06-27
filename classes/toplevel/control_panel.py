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

from PyQt5.QtWidgets import (QDockWidget, QWidget,
                             QGridLayout, QStyle, QSizePolicy,
                             QPushButton, QLabel, QLineEdit, QCheckBox,
                             QSpinBox, QComboBox,
                             QDateTimeEdit)
from PyQt5.QtCore import QDateTime, QDate, QObject

from ..internal.subplot_manager import SubplotManager

class ControlPanel(QDockWidget):
    """Contains all buttons for controlling subplot organization."""

    def __init__(self, parent, title):
        super().__init__(title)
        self.parent = parent
        grid = QGridLayout()
        w = QWidget()
        self.title_edited = False
        self.weights_edited = False
        self.locations = {
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

        self.title_edit = QLineEdit('New_Figure')
        self.title_edit.editingFinished.connect(self.rename)
        self.title_edit.textEdited.connect(self.tte)
        grid.addWidget(self.title_edit, 0, 1, 1, 2)

        grid.addWidget(QLabel('Weights:'), 1, 0)
        self.weights_edit = QLineEdit('[1]')
        self.weights_edit.editingFinished.connect(self.adjust_weights)
        self.weights_edit.textEdited.connect(self.wte)
        grid.addWidget(self.weights_edit, 1, 1, 1, 2)

        grid.addWidget(QLabel('Start:'), 2, 0)
        self.select_start = QDateTimeEdit()
        self.select_start.setDisplayFormat('yyyy-MM-dd hh:mm:ss')
        self.select_start.dateTimeChanged.connect(self.time_filter)
        grid.addWidget(self.select_start, 2, 1)

        self.min_timestamp = QPushButton('Min')
        self.min_timestamp.setFixedWidth(30)
        self.min_timestamp.clicked.connect(self.set_start_min)
        grid.addWidget(self.min_timestamp, 2, 2)

        grid.addWidget(QLabel('End:'), 3, 0)
        self.select_end = QDateTimeEdit(QDate.currentDate())
        self.select_end.setDisplayFormat('yyyy-MM-dd hh:mm:ss')
        self.select_end.dateTimeChanged.connect(self.time_filter)
        grid.addWidget(self.select_end, 3, 1)

        self.max_timestamp = QPushButton('Max')
        self.max_timestamp.setFixedWidth(30)
        self.max_timestamp.clicked.connect(self.set_end_max)
        grid.addWidget(self.max_timestamp, 3, 2)

        self.color_toggle = QCheckBox('Color by Unit')
        self.color_toggle.clicked.connect(self.color_coordinate)
        grid.addWidget(self.color_toggle, 0, 3, 1, 2)

        self.legend_toggle = QCheckBox('Show Legend')
        self.legend_toggle.clicked.connect(self.toggle_legend)
        grid.addWidget(self.legend_toggle, 1, 3, 1, 2)

        grid.addWidget(QLabel('Columns'), 2, 3)
        self.legend_columns = QSpinBox()
        self.legend_columns.setRange(1, 10)
        self.legend_columns.valueChanged.connect(self.set_legend_columns)
        grid.addWidget(self.legend_columns, 2, 4)

        self.legend_location = QComboBox()
        self.legend_location.addItems(list(self.locations.keys()))
        self.legend_location.currentIndexChanged.connect(
                self.set_legend_location)
        grid.addWidget(self.legend_location, 3, 3, 1, 2)

        self.cycle = QPushButton('Cycle Axes')
        self.cycle.clicked.connect(self.cycle_subplot)
        grid.addWidget(self.cycle, 0, 5)

        self.insert = QPushButton('Insert')
        self.insert.clicked.connect(self.insert_subplot)
        grid.addWidget(self.insert, 1, 5)

        self.delete = QPushButton('Delete')
        self.delete.clicked.connect(self.delete_subplot)
        grid.addWidget(self.delete, 2, 5)

        self.clear = QPushButton('Clear')
        self.clear.clicked.connect(self.clear_subplot)
        grid.addWidget(self.clear, 3, 5)

        self.reorder_up = QPushButton()
        upicon = getattr(QStyle, 'SP_TitleBarShadeButton')
        self.reorder_up.setIcon(self.style().standardIcon(upicon))
        self.reorder_up.setSizePolicy(QSizePolicy.Expanding,
                                     QSizePolicy.Expanding)
        self.reorder_up.clicked.connect(self.reorder)
        grid.addWidget(self.reorder_up, 0, 6, 2, 1)

        self.reorder_down = QPushButton()
        downicon = getattr(QStyle, 'SP_TitleBarUnshadeButton')
        self.reorder_down.setIcon(self.style().standardIcon(downicon))
        self.reorder_down.setSizePolicy(QSizePolicy.Expanding,
                                       QSizePolicy.Expanding)
        self.reorder_down.clicked.connect(self.reorder)
        grid.addWidget(self.reorder_down, 2, 6, 2, 1)

        w.setLayout(grid)
        self.setWidget(w)

    def wte(self):
        self.weights_edited = True

    def tte(self):
        self.title_edited = True

    def cleanup_axes(self):
        """Manages figure axes ticks, tick labels, and gridlines."""
        ui = self.parent
        af = ui.axes_frame
        fs = ui.figure_settings

        self.timespan = self.end - self.start
        if self.timespan >= dt.timedelta(days=4):
            self.major_locator = mdates.DayLocator()
            self.minor_locator = mdates.HourLocator(interval=12)
        elif (self.timespan >= dt.timedelta(days=2) and
              self.timespan < dt.timedelta(days=4)):
            self.major_locator = mdates.DayLocator()
            self.minor_locator = mdates.HourLocator(interval=12)
        else:
            self.major_locator = mdates.HourLocator(interval=2)
            self.minor_locator = mdates.HourLocator(interval=1)

        for i, sp in enumerate(af.subplots):
            # All subplots
            self.toggle_grid(sp)
            for ax in sp.axes:
                ax.tick_params(axis='y', labelsize=fs.tick_size.value())
                ax.xaxis.set_major_locator(self.major_locator)
                ax.xaxis.set_minor_locator(self.minor_locator)
            # Lowest subplot
            if i == len(af.subplots)-1:  # Bottom-most subplot only
                # maybe in the future:
                # - go through subplots
                # - find one with contents
                # - use its xaxis ticks/labels as base xaxis ticks/labels
                if not sp.contents:
                    # If subplot is empty, don't show xaxis ticks
                    sp.host().tick_params(axis='x',
                           labelbottom=False, bottom=False)
                else:
                    # Tell the host axes' xaxis it's plotting dates
                    sp.host().xaxis_date()
                    sp.host().xaxis.set_major_formatter(
                            mdates.DateFormatter(fs.timestamp_format))
                    # Give focus to host axes
                    plt.sca(sp.host())
                    sp.host().tick_params(axis='x',
                           labelbottom=True, bottom=True)
                    plt.xticks(rotation=fs.tick_rot.value(),
                               ha='right', fontsize=fs.tick_size.value())
                plt.yticks(fontsize=fs.tick_size.value())

            # All other subplots
            else:
                sp.host().tick_params(axis='x',
                       which='major', labelbottom=False)

    def toggle_grid(self, sp):
        """Controls whether X/Y, major/minor gridlines are displayed."""
        ui = self.parent
        fs = ui.figure_settings
        linestyles = ['-', '--', ':', '-.']

        if fs.major_x.isChecked():
            sp.host().xaxis.grid(which='major')
        if fs.minor_x.isChecked():
            sp.host().minorticks_on()
#            sp.host().tick_params(axis='x', which='minor', bottom=True)
            sp.host().xaxis.grid(which='minor')
        if fs.major_y.isChecked():
            for i, ax in enumerate(sp.axes):
                ax.yaxis.grid(which='major',
                              linestyle=linestyles[i%len(linestyles)])
        if fs.minor_y.isChecked():
            for i, ax in enumerate(sp.axes):
                # turns both x and y on, dunno how to only get it on one axis
                ax.minorticks_on()
#                ax.tick_params(axis='y', which='minor')
                ax.yaxis.grid(b=True, which='minor',
                              linestyle=linestyles[i%len(linestyles)])

    def cap_start_end(self):
        """Limits start and end datetimes by loaded data extents."""
        ui = self.parent
        try:
            groups = ui.groups.values()
            data_start = min([group.data.index[0] for group in groups])
#            print(type(data_start), data_start)
#            print(type(self.start), self.start)
            self.start = max([data_start, self.start])
            data_end = max([group.data.index[-1] for group in groups])
            self.end = min([data_end, self.end])

            self.select_start.setMinimumDateTime(data_start)
            self.select_start.setMaximumDateTime(self.end)
            self.select_end.setMaximumDateTime(data_end)
            self.select_end.setMinimumDateTime(self.start)
        except ValueError:
            min_date = dt.datetime.strptime('2000-01-01 00:00:00',
                                            '%Y-%m-%d  %H:%M:%S')
            self.select_start.setMinimumDateTime(min_date)
            self.select_start.setMaximumDateTime(self.end)
            self.select_end.setMaximumDateTime(QDateTime.currentDateTime())
            self.select_end.setMinimumDateTime(self.start)
        return self.start, self.end

    def set_start_min(self):
        self.select_start.setDateTime(self.select_start.minimumDateTime())

    def set_end_max(self):
        self.select_end.setDateTime(self.select_end.maximumDateTime())

    def time_filter(self):
        """Determines major/minor x locators based on the timespan."""
        ui = self.parent
        af = ui.axes_frame
        self.start = self.select_start.dateTime().toPyDateTime()
        self.end = self.select_end.dateTime().toPyDateTime()
        self.start, self.end = self.cap_start_end()
        af.refresh_all()

    def reorder(self):
        """Reorders selected subplot up or down."""
        ui = self.parent
        af = ui.axes_frame
        sps = af.current_sps
        if len(sps) == 1:
            caller = QObject.sender(self)
            if caller == self.reorder_up:
                inc = -1
            if caller == self.reorder_down:
                inc = 1
            sp = sps[0]
            i = sp.index
            j = i+inc
            # if can be moved up/down
            if 0 <= j < len(af.subplots):
                af.weights[i], af.weights[j] = af.weights[j], af.weights[i]
                af.subplots[i], af.subplots[j] = af.subplots[j], af.subplots[i]
                af.current_sps = [af.subplots[i]]
                af.refresh_all()
        else:
            ui.statusBar().showMessage('Select one subplot to reorder')

    def insert_subplot(self):
        """Inserts blank subplot below selected subplot."""
        ui = self.parent
        af = ui.axes_frame
        sps = af.current_sps
        # Determine index at which to insert blank subplot
        if len(sps) != 1:
            index = len(af.subplots)-1
        else:
            index = sps[0].index
        # Insert blank Subplot_Manager at position below index
        af.subplots.insert(index+1, SubplotManager(ui, [None]))
        af.weights.insert(index+1, 1)
        af.refresh_all()

    def delete_subplot(self):
        """Deletes selected subplot(s) and returns contents to available."""
        ui = self.parent
        af = ui.axes_frame
        sps = af.current_sps
        if sps:
            sd = ui.series_display
            for i in reversed([sp.index for sp in sps]):
                if len(af.subplots) == 1:
                    self.clear_subplot(sps)
                else:
                # Delete associated info at selected indices
                    af.available_data.add(af.subplots[i].contents)
                    # add contents back into available tree
                    sd.populate_tree(af.available_data, sd.available)
                    del af.weights[i]
                    del af.subplots[i]
            af.current_sps = []  # deselect everything
            af.refresh_all()
        else:
            ui.statusBar().showMessage('Select one or more subplots to delete')

    def clear_subplot(self):
        """Clears selected subplots.
        Adds selected subplots' contents back into available tree."""
        ui = self.parent
        af = ui.axes_frame
        sps = af.current_sps
        if sps:
            sd = ui.series_display
            sd.plotted.clear()
            for sp in sps:
                af.available_data.add(sp.contents)
                sd.populate_tree(af.available_data, sd.available)
                w = sd.search_available
                w.textChanged.emit(w.text())
                sp.contents.clear()
                sp.order = [None]
                sp.plot(skeleton=True)
            af.refresh_all()
        else:
            ui.statusBar().showMessage('Select one or more subplots to clear')

    def color_coordinate(self):
        """Coordinates colors of selected subplot(s) by unit type (not unit).
        Each unit type gets its own color for lines, labels, and ticks."""
        ui = self.parent
        af = ui.axes_frame
        sps = af.current_sps
        if sps:
            if len(sps) == 1:
                sp = sps[0]
                sp.color_coord = not sp.color_coord
            else:
                any_coord = any([sp.color_coord for sp in sps])
                for sp in sps:
                    sp.color_coord = not any_coord
            af.refresh_all()
        else:
            ui.statusBar().showMessage(
                    'Select one or more subplots to toggle color coordination')

    def toggle_legend(self):
        """Toggles legend display of selected subplot(s)."""
        ui = self.parent
        af = ui.axes_frame
        sps = af.current_sps
        if sps:
            if len(sps) == 1:
                sp = sps[0]
                sp.legend = not sp.legend
            else:
                any_legend = any([sp.legend for sp in sps])
                for sp in sps:
                    sp.legend = not any_legend
            af.refresh_all()
        else:
            ui.statusBar().showMessage(
                    'Select one or more subplots to toggle legend')

    def set_legend_columns(self):
        ui = self.parent
        af = ui.axes_frame
        sps = af.current_sps
        for sp in sps:
            sp.ncols = self.legend_columns.value()
        af.refresh_all()

    def set_legend_location(self):
        ui = self.parent
        af = ui.axes_frame
        sps = af.current_sps
        for sp in sps:
            sp.location = self.legend_location.currentText()
        af.refresh_all()

    def cycle_subplot(self):
        """Cycles through unit order permutations of selected subplot(s)."""
        ui = self.parent
        af = ui.axes_frame
        sps = af.current_sps
        if sps:
            for sp in sps:
                sorted_perms = sorted(itertools.permutations(sp.order))
                perms = [list(p) for p in sorted_perms]
                i = perms.index(sp.order)
                sp.order = perms[(i+1)%len(perms)]
            af.refresh_all()
        else:
            ui.statusBar().showMessage(
                    'Select one or more subplots to cycle unit plotting order')

    def adjust_weights(self):
        """Adjusts subplot vertical aspect ratios.
        Sequence of digits between 1-9 are accepted.
        """
        if self.weights_edited:
            ui = self.parent
            af = ui.axes_frame
            weights = []
            for i in self.weights_edit.text():  # parse weighting input
                if i.isdigit():
                    weights.append(int(i))
                elif i in '0, []':  # ignore zero, commas, spaces, and brackets
                    continue
                else:
                    ui.statusBar().showMessage(
                            'Only integer inputs <10 allowed')
                    self.weights_edit.setText(str(af.weights))
                    return
            if len(weights) != len(af.subplots):
                ui.statusBar().showMessage(
                        'Figure has {} subplots but {} weights were provided'
                        .format(len(af.subplots), len(weights)))
                self.weights_edit.setText(str(af.weights))
                return
            af.weights = weights
            af.refresh_all()
            self.weights_edited = False

    def rename(self):
        """Renames figure."""
        if self.title_edited:
            ui = self.parent
            af = ui.axes_frame
            fs = ui.figure_settings
            # get rid of any backslashes or dots
            fig_title = re.sub('[\\\\.]', '', self.title_edit.text())
            if not fig_title:
                af.fig.suptitle('')
                fig_title = 'New_Figure'
            else:
                af.fig.suptitle(fig_title, fontsize=fs.title_size.value())
                ui.filename = fig_title
            af.draw()
            ui.saved = False
            self.title_edited = False
