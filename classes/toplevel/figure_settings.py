# -*- coding: utf-8 -*-
"""figure_settings.py - Contains FigureSettings class definition."""

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

import re
import math
import functools
import datetime as dt
import matplotlib.colors as mcolors
import matplotlib.dates as mdates

from PyQt5.QtWidgets import (QDockWidget, QWidget, QColorDialog, QInputDialog,
                             QGridLayout, QFormLayout,
                             QHBoxLayout, QVBoxLayout,
                             QGroupBox, QLabel, QCheckBox, QPushButton,
                             QRadioButton, QSpinBox, QDoubleSpinBox, QLineEdit,
                             QDateTimeEdit,
                             QHeaderView, QTableWidget, QTableWidgetItem)
from PyQt5.QtGui import QIcon, QColor
from PyQt5.QtCore import Qt, QObject, QDateTime, QDate

from ..internal.q_color_button import QColorButton

class FigureSettings(QDockWidget):
    """Contains options for controlling figure size and appearance."""

    def __init__(self, parent, title, saved=None):
        super().__init__(title)
        self.parent = parent
        ui = self.parent
        self.title_edited = False
        self.weights_edited = False
        # when color coordination is on,
        # use markers in this order to differentiate series
        self.markers = ['o', '+', 'x', 'D', 's', '^', 'v', '<', '>']
# add to config.json?
        w = QWidget()
        vbox = QVBoxLayout()

        form = QFormLayout()
        self.title_edit = QLineEdit(ui.af_init['title'])
        self.title_edit.editingFinished.connect(self.rename)
        self.title_edit.textEdited.connect(self.tte)
        vbox.addWidget(self.title_edit)
        figure_group= QGroupBox('Figure Dimensions')
        figure_group.setAlignment(Qt.AlignHCenter)
        form = QFormLayout()
        self.upper_pad = QDoubleSpinBox()
        self.upper_pad.setRange(0, 0.5)
        self.upper_pad.setSingleStep(.01)
        self.upper_pad.setValue(ui.af_init['upper_pad'])
        self.upper_pad.valueChanged.connect(self.update_gs_kwargs)
        form.addRow('Upper Pad', self.upper_pad)
        self.lower_pad = QDoubleSpinBox()
        self.lower_pad.setRange(0, 0.5)
        self.lower_pad.setSingleStep(.01)
        self.lower_pad.setValue(ui.af_init['lower_pad'])
        self.lower_pad.valueChanged.connect(self.update_gs_kwargs)
        form.addRow('Lower Pad', self.lower_pad)
        self.left_pad = QDoubleSpinBox()
        self.left_pad.setRange(0, 0.5)
        self.left_pad.setSingleStep(.01)
        self.left_pad.setValue(ui.af_init['left_pad'])
        self.left_pad.valueChanged.connect(self.update_gs_kwargs)
        form.addRow('Left Pad', self.left_pad)
        self.right_pad = QDoubleSpinBox()
        self.right_pad.setRange(0, 0.5)
        self.right_pad.setSingleStep(.01)
        self.right_pad.setValue(ui.af_init['right_pad'])
        self.right_pad.valueChanged.connect(self.update_gs_kwargs)
        form.addRow('Right Pad', self.right_pad)
        self.spacing = QDoubleSpinBox()
        self.spacing.setRange(0, 1)
        self.spacing.setSingleStep(.01)
        self.spacing.setValue(.05)
        self.spacing.valueChanged.connect(self.update_gs_kwargs)
        form.addRow('Spacing', self.spacing)
        self.axis_offset = QDoubleSpinBox()
        self.axis_offset.setRange(0, 1)
        self.axis_offset.setDecimals(3)
        self.axis_offset.setSingleStep(.005)
        self.axis_offset.setValue(.05)
        self.axis_offset.valueChanged.connect(self.adjust_axes_offset)
        form.addRow('Axis Offset', self.axis_offset)
        self.weights_edit = QLineEdit('[1]')
        self.weights_edit.editingFinished.connect(self.adjust_weights)
        self.weights_edit.textEdited.connect(self.wte)
        form.addRow('Weights', self.weights_edit)
        figure_group.setLayout(form)
        vbox.addWidget(figure_group)

        grid_group = QGroupBox('Grid Settings')
        grid_group.setAlignment(Qt.AlignHCenter)
        grid = QGridLayout()
        self.major_x = QCheckBox('Major X')
        self.major_x.toggled.connect(self.update_grid)
        grid.addWidget(self.major_x, 0, 0)
        self.minor_x = QCheckBox('Minor X')
        self.minor_x.toggled.connect(self.update_grid)
        grid.addWidget(self.minor_x, 0, 1)
        self.major_y = QCheckBox('Major Y')
        self.major_y.toggled.connect(self.update_grid)
        grid.addWidget(self.major_y, 1, 0)
        self.minor_y = QCheckBox('Minor Y')
        self.minor_y.toggled.connect(self.update_grid)
        grid.addWidget(self.minor_y, 1, 1)
        grid_group.setLayout(grid)
        vbox.addWidget(grid_group)

        plot_group = QGroupBox('Plot Settings')
        plot_group.setAlignment(Qt.AlignHCenter)
        grid = QGridLayout()
        self.scatter = QRadioButton('Scatter')
        self.scatter.setChecked(True)
        self.scatter.toggled.connect(self.update_plots)
        grid.addWidget(self.scatter, 0, 0)
        self.line = QRadioButton('Line')
        self.line.toggled.connect(self.update_plots)
        grid.addWidget(self.line, 0, 1)
        grid.addWidget(QLabel('Marker Size'), 1, 0)
        self.dot_size = QDoubleSpinBox()
        self.dot_size.setRange(0, 5)
        self.dot_size.setSingleStep(.1)
        self.dot_size.setValue(0.5)
        self.dot_size.valueChanged.connect(self.update_plots)
        grid.addWidget(self.dot_size, 1, 1)
        grid.addWidget(QLabel('Plot Density'), 2, 0)
        self.density = QSpinBox()
        self.density.setRange(1, 100)
        self.density.setSingleStep(5)
        self.density.setValue(100)
        self.density.setSuffix('%')
        self.density.valueChanged.connect(self.update_plots)
        grid.addWidget(self.density, 2, 1)
        grid.addWidget(QLabel('Plot Start:'), 3, 0)
        self.min_timestamp = QPushButton('Min')
        self.min_timestamp.clicked.connect(self.set_start_min)
        grid.addWidget(self.min_timestamp, 3, 1)
        self.select_start = QDateTimeEdit()
        self.select_start.setDisplayFormat('yyyy-MM-dd hh:mm:ss')
        self.select_start.dateTimeChanged.connect(self.adjust_start_end)
        grid.addWidget(self.select_start, 4, 0, 1, 2)
        grid.addWidget(QLabel('Plot End:'), 5, 0)
        self.max_timestamp = QPushButton('Max')
        self.max_timestamp.clicked.connect(self.set_end_max)
        grid.addWidget(self.max_timestamp, 5, 1)
        self.select_end = QDateTimeEdit(QDate.currentDate())
        self.select_end.setDisplayFormat('yyyy-MM-dd hh:mm:ss')
        self.select_end.dateTimeChanged.connect(self.adjust_start_end)
        grid.addWidget(self.select_end, 6, 0, 1, 2)
        plot_group.setLayout(grid)
        vbox.addWidget(plot_group)

        text_group = QGroupBox('Text Settings')
        text_group.setAlignment(Qt.AlignHCenter)
        form = QFormLayout()
        self.title_size = QSpinBox()
        self.title_size.setRange(0, 60)
        self.title_size.setValue(ui.af_init['title_size'])
        self.title_size.valueChanged.connect(self.update_fonts)
        form.addRow('Title', self.title_size)
        self.label_size = QSpinBox()
        self.label_size.setRange(0, 30)
        self.label_size.setValue(12)
        self.label_size.valueChanged.connect(self.update_fonts)
        form.addRow('Axis Labels', self.label_size)
        self.tick_size = QSpinBox()
        self.tick_size.setRange(0, 20)
        self.tick_size.setValue(10)
        self.tick_size.valueChanged.connect(self.update_fonts)
        form.addRow('Tick Size', self.tick_size)
        self.tick_rot = QSpinBox()
        self.tick_rot.setRange(0, 90)
        self.tick_rot.setValue(45)
        self.tick_rot.valueChanged.connect(self.update_fonts)
        form.addRow('Tick Rotation', self.tick_rot)
        self.tsf = QPushButton('Timestamp Format')
        self.tsf.clicked.connect(self.edit_timestamp_format)
        form.addRow(self.tsf)
        text_group.setLayout(form)
        vbox.addWidget(text_group)

        self.unit_table = QTableWidget()
        self.unit_table.setColumnCount(2)
        h_header = self.unit_table.horizontalHeader()
        h_header.setSectionResizeMode(0, QHeaderView.Stretch)
        h_header.setSectionResizeMode(1, QHeaderView.ResizeToContents)
        h_header.hide()
        v_header = self.unit_table.verticalHeader()
        v_header.hide()
        v_header.setDefaultSectionSize(v_header.minimumSectionSize())
        v_header.setSectionResizeMode(QHeaderView.Fixed)
        self.unit_table.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        vbox.addWidget(self.unit_table)
        w.setLayout(vbox)
        self.setWidget(w)

        self.dlg = QColorDialog()
        self.dlg.setWindowIcon(QIcon('rc/satellite.png'))
        default_color = ui.current_rcs['axes.labelcolor']
        self.color_dict = {None:default_color, '':default_color}
        self.update_unit_table()

    def rename(self):
        """Renames figure."""
        ui = self.parent
        af = ui.axes_frame
        if self.title_edited:
            # get rid of any backslashes or dots
            fig_title = re.sub('[\\\\.]', '', self.title_edit.text())
            if not fig_title:
                af.fig.suptitle('')
                fig_title = ui.af_init['title']
            else:
                af.fig.suptitle(fig_title, fontsize=self.title_size.value())
                ui.filename = fig_title
            af.draw()
            ui.saved = False
            self.title_edited = False

    def tte(self):
        self.title_edited = True

    def update_gs_kwargs(self):
        ui = self.parent
        af = ui.axes_frame
        af.update_gridspec()
        af.draw()

    def adjust_axes_offset(self):
        ui = self.parent
        af = ui.axes_frame
        for sp in af.subplots:
            sp.arrange_axes()
            sp.show_legend()
        af.update_gridspec()
        af.draw()

    def adjust_weights(self):
        """Adjusts subplot vertical aspect ratios.
        Sequence of digits between 1-9 are accepted.
        """
        if self.weights_edited:
            ui = self.parent
            af = ui.axes_frame
            nplots = af.nplots()
            new_weights = []
            for i in self.weights_edit.text():
                if i in '0, []':  # ignore zero, commas, spaces, and brackets
                    continue
                elif i.isdigit():
                    new_weights.append(int(i))
                else:
                    ui.statusBar().showMessage(
                            'Only integer inputs <10 allowed')
                    self.weights_edit.setText(str(af.weights()))
                    return
            if len(new_weights) != nplots:
                ui.statusBar().showMessage(
                        'Figure has {} subplots but {} weights were provided'
                        .format(nplots, len(new_weights)))
                self.weights_edit.setText(str(af.weights()))
                return

            g = functools.reduce(math.gcd, new_weights)
            # simplify weights by their greatest common denominator
            # (eg [2,2,4] -> [1,1,2])
            weights = [x//g for x in new_weights]
            self.weights_edit.setText(str(weights))
            self.weights_edited = False
            af.update_gridspec(nplots, weights)
            af.draw()

    def wte(self):
        self.weights_edited = True

    def update_grid(self):
        ui = self.parent
        af = ui.axes_frame
        af.format_axes()
        af.draw()

    def update_plots(self):
        ui = self.parent
        af = ui.axes_frame
        af.replot()
        af.draw()

    def set_start_min(self):
        self.select_start.setDateTime(self.select_start.minimumDateTime())

    def set_end_max(self):
        self.select_end.setDateTime(self.select_end.maximumDateTime())

    def adjust_start_end(self):
        """Limits start and end datetimes by loaded data extents."""
        ui = self.parent
        af = ui.axes_frame
        try:
            groups = ui.groups.values()
            data_start = min([group.data.index[0] for group in groups])
            data_end = max([group.data.index[-1] for group in groups])
        except ValueError:
            data_start = dt.datetime.strptime('2000-01-01 00:00:00',
                                              '%Y-%m-%d  %H:%M:%S')
            data_end = QDateTime.currentDateTime()
        user_start = self.select_start.dateTime().toPyDateTime()
        user_end = self.select_end.dateTime().toPyDateTime()
        af.start = max([data_start, user_start])
        af.end = min([data_end, user_end])

        af.timespan = af.end - af.start
        if af.timespan >= dt.timedelta(days=4):
            af.major_locator = mdates.DayLocator()
            af.minor_locator = mdates.HourLocator(interval=12)
        elif (af.timespan >= dt.timedelta(days=2) and
              af.timespan < dt.timedelta(days=4)):
            af.major_locator = mdates.DayLocator()
            af.minor_locator = mdates.HourLocator(interval=12)
        else:
            af.major_locator = mdates.HourLocator(interval=2)
            af.minor_locator = mdates.HourLocator(interval=1)

        self.select_start.setMinimumDateTime(data_start)
        self.select_start.setMaximumDateTime(af.end)
        self.select_end.setMaximumDateTime(data_end)
        self.select_end.setMinimumDateTime(af.start)
        af.replot(legend=False)
        af.draw()

    def update_fonts(self):
        ui = self.parent
        af = ui.axes_frame
        af.format_axes()
        af.draw()

    def edit_timestamp_format(self):
        ui = self.parent
        af = ui.axes_frame
        tsf_dlg = QInputDialog()
        codes = (
                ('Code', 'Description', 'Values'),
                ('', '', ''),
                ('%d', 'Day of month', '[1-31]'),
                ('%-d', 'Day of month', '[01-31]'),
                ('%b', 'Short month', '[Jan-Dec]'),
                ('%B', 'Long month', '[January-December]'),
                ('%m', 'Month zero-pad', '[01-12]'),
                ('%-m', 'Month\t', '[1-12]'),
                ('%y', 'Short year', '[00-99]'),
                ('%Y', 'Year with century', '[2000-2099]'),
                ('%H', '24-Hour zero-pad', '[00-23]'),
                ('%-H', '24-Hour\t', '[0-23]'),
                ('%I', '12-Hour zero-pad', '[01-12]'),
                ('%-I', '12-Hour\t', '[1-12]'),
                ('%M', 'Minute zero-pad', '[00-59]'),
                ('%S', 'Second zero-pad', '[00-59]'),
                )
        reference = ''
        for code in codes:
            reference += '{}\t{}\t{}\n'.format(*code)
#            reference += code + '\t' + ex + '\n'
        reference += '\nSee strftime.org for more details'
        text, ok = tsf_dlg.getText(self, 'Edit Timestamp Format',
                                   reference, text=af.timestamp_format)
        if ok:
            try:
                dt.datetime.now().strftime(text)
                af.timestamp_format = text
                af.format_axes()
                af.draw()
            except ValueError:
                self.edit_timestamp_format()

    def update_unit_table(self):
        """Updates table associating unit types with colors."""
        ui = self.parent
        all_units = {**ui.unit_dict, **ui.user_units}
        self.unit_table.setRowCount(len(all_units))
        for i, unit_type in enumerate(all_units):
            if unit_type not in self.color_dict:
                self.color_dict.update({unit_type:'C'+str(i%10)})
        for i, unit_type in enumerate(all_units):
            color = QColor(mcolors.to_hex(self.color_dict[unit_type]))
            self.dlg.setCustomColor(i, color)
        for i, unit_type in enumerate(all_units):
            item = QTableWidgetItem(unit_type)
            item.setFlags(Qt.ItemIsSelectable)
            self.unit_table.setItem(i, 0, item)
            color = mcolors.to_hex(self.color_dict[unit_type])
            colorButton = QColorButton(self, color, unit_type)
            colorButton.clicked.connect(self.pick_color)
            _widget = QWidget()
            _layout = QHBoxLayout(_widget)
            _layout.addWidget(colorButton)
            _layout.setAlignment(Qt.AlignCenter)
            _layout.setContentsMargins(0,0,0,0)
            self.unit_table.setCellWidget(i, 1, _widget)

    def pick_color(self):
        """Opens a color picker dialog and assigns it to the unit type."""
        color_button = QObject.sender(self)
        unit_type = color_button.unit_type
        if color_button.color:
            self.dlg.setCurrentColor(QColor(color_button.color))

        if self.dlg.exec_():
            color_button.color = self.dlg.currentColor().name()
            color_button.setStyleSheet(
                    "background-color:{};".format(color_button.color))
            self.color_dict[unit_type] = color_button.color
            ui = self.parent
            af = ui.axes_frame
            af.replot()
            af.draw()