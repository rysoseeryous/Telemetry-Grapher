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

import math
import functools
import datetime as dt
import matplotlib.colors as mcolors

from PyQt5.QtWidgets import (QDockWidget, QWidget, QColorDialog, QInputDialog,
                             QGridLayout, QFormLayout ,QVBoxLayout, QGroupBox,
                             QSpinBox, QDoubleSpinBox, QLineEdit,
                             QCheckBox, QLabel, QSlider, QScrollArea,
                             QRadioButton, QPushButton, QDateTimeEdit,
                             QHeaderView, QTableWidget, QTableWidgetItem)
from PyQt5.QtGui import QIcon, QColor
from PyQt5.QtCore import Qt, QObject

from telemetry_grapher.classes.internal.q_color_button import QColorButton

class FigureSettings(QDockWidget):
    """Contains options for controlling figure size and appearance."""

    def __init__(self, parent, title):
        super().__init__(title)
        self.parent = parent
        ui = self.parent
        self.weights_edited = False
        msg = 'All minor periods do not have the same length'
        len0 = len(ui.m_steps[0])
        assert all([len(m_Ts) == len0 for m_Ts in ui.m_steps]), msg

        w = QWidget()
        vbox = QVBoxLayout()

        figure_group= QGroupBox('Figure Dimensions')
        figure_group.setAlignment(Qt.AlignHCenter)
        form = QFormLayout()
        self.upper_pad = QDoubleSpinBox()
        self.upper_pad.setRange(0, 0.5)
        self.upper_pad.setSingleStep(.01)
        self.upper_pad.valueChanged.connect(self.update_gs_kwargs)
        form.addRow('Upper Pad', self.upper_pad)
        self.lower_pad = QDoubleSpinBox()
        self.lower_pad.setRange(0, 0.5)
        self.lower_pad.setSingleStep(.01)
        self.lower_pad.valueChanged.connect(self.update_gs_kwargs)
        form.addRow('Lower Pad', self.lower_pad)
        self.left_pad = QDoubleSpinBox()
        self.left_pad.setRange(0, 0.5)
        self.left_pad.setSingleStep(.01)
        self.left_pad.valueChanged.connect(self.update_gs_kwargs)
        form.addRow('Left Pad', self.left_pad)
        self.right_pad = QDoubleSpinBox()
        self.right_pad.setRange(0, 0.5)
        self.right_pad.setSingleStep(.01)
        self.right_pad.valueChanged.connect(self.update_gs_kwargs)
        form.addRow('Right Pad', self.right_pad)
        self.spacing = QDoubleSpinBox()
        self.spacing.setRange(0, 1)
        self.spacing.setSingleStep(.01)
        self.spacing.valueChanged.connect(self.update_gs_kwargs)
        form.addRow('Spacing', self.spacing)
        self.axis_offset = QDoubleSpinBox()
        self.axis_offset.setRange(0, 1)
        self.axis_offset.setDecimals(3)
        self.axis_offset.setSingleStep(.005)
        self.axis_offset.valueChanged.connect(self.adjust_axes_offset)
        form.addRow('Axis Offset', self.axis_offset)
        self.weights_edit = QLineEdit()
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
        self.major_T = QLabel()
        grid.addWidget(self.major_T, 2, 0, 1, 2)
        self.major_slider = QSlider(Qt.Horizontal)
        self.major_slider.setMaximum(len(ui.M_steps)-1)
        self.major_slider.setPageStep(1)
        self.major_slider.valueChanged.connect(self.update_grid)
        grid.addWidget(self.major_slider, 3, 0, 1, 2)
        self.minor_T = QLabel()
        grid.addWidget(self.minor_T, 4, 0, 1, 2)
        self.minor_slider = QSlider(Qt.Horizontal)
        self.minor_slider.setPageStep(1)
        self.minor_slider.valueChanged.connect(self.update_grid)
        grid.addWidget(self.minor_slider, 5, 0, 1, 2)
        grid_group.setLayout(grid)
        vbox.addWidget(grid_group)

        plot_group = QGroupBox('Plot Settings')
        plot_group.setAlignment(Qt.AlignHCenter)
        grid = QGridLayout()
        self.scatter = QRadioButton('Scatter')
        self.scatter.toggled.connect(self.update_plots)
        grid.addWidget(self.scatter, 0, 0)
        self.line = QRadioButton('Line')
        self.line.toggled.connect(self.update_plots)
        grid.addWidget(self.line, 0, 1)
        grid.addWidget(QLabel('Marker Size'), 1, 0)
        self.dot_size = QDoubleSpinBox()
        self.dot_size.setRange(0, 10)
        self.dot_size.setSingleStep(.1)
        self.dot_size.valueChanged.connect(self.update_plots)
        grid.addWidget(self.dot_size, 1, 1)
        grid.addWidget(QLabel('Plot Density'), 2, 0)
        self.density = QSpinBox()
        self.density.setRange(1, 100)
        self.density.setSingleStep(5)
        self.density.setSuffix('%')
        self.density.valueChanged.connect(self.update_plots)
        grid.addWidget(self.density, 2, 1)

        grid.addWidget(QLabel('X Margin'), 3, 0)
        self.x_margin = QDoubleSpinBox()
        self.x_margin.setRange(0, 0.5)
        self.x_margin.setSingleStep(0.01)
        self.x_margin.valueChanged.connect(self.update_plots)
        grid.addWidget(self.x_margin, 3, 1)

        grid.addWidget(QLabel('Plot Start:'), 4, 0)
        self.min_timestamp = QPushButton('Min')
        self.min_timestamp.clicked.connect(self.set_start_min)
        grid.addWidget(self.min_timestamp, 4, 1)
        self.select_start = QDateTimeEdit()
        self.select_start.setDisplayFormat('yyyy-MM-dd hh:mm:ss')
        self.select_start.dateTimeChanged.connect(self.update_start)
        grid.addWidget(self.select_start, 5, 0, 1, 2)
        grid.addWidget(QLabel('Plot End:'), 6, 0)
        self.max_timestamp = QPushButton('Max')
        self.max_timestamp.clicked.connect(self.set_end_max)
        grid.addWidget(self.max_timestamp, 6, 1)
        self.select_end = QDateTimeEdit()#dt.datetime.now())

        self.select_end.setDisplayFormat('yyyy-MM-dd hh:mm:ss')
        self.select_end.dateTimeChanged.connect(self.update_end)
        grid.addWidget(self.select_end, 7, 0, 1, 2)
        plot_group.setLayout(grid)
        vbox.addWidget(plot_group)

        text_group = QGroupBox('Text Settings')
        text_group.setAlignment(Qt.AlignHCenter)
        form = QFormLayout()
        self.title_size = QSpinBox()
        self.title_size.setRange(0, 100)
        self.title_size.valueChanged.connect(self.update_fonts)
        form.addRow('Title', self.title_size)
        self.label_size = QSpinBox()
        self.label_size.setRange(0, 60)
        self.label_size.valueChanged.connect(self.update_fonts)
        form.addRow('Axis Labels', self.label_size)
        self.tick_size = QSpinBox()
        self.tick_size.setRange(0, 40)
        self.tick_size.valueChanged.connect(self.update_fonts)
        form.addRow('Tick Size', self.tick_size)
        self.tick_rot = QSpinBox()
        self.tick_rot.setRange(0, 90)
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
        self.unit_table.setMinimumHeight(450)
        vbox.addWidget(self.unit_table)

        w.setLayout(vbox)
        scroll = QScrollArea()
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        scroll.setWidgetResizable(True)
        scroll.setWidget(w)
        self.setWidget(scroll)

        self.dlg = QColorDialog()
        self.dlg.setWindowIcon(QIcon('rc/satellite.png'))
        self.update_unit_table()

    def update_gs_kwargs(self):
        ui = self.parent
        cf = ui.get_current_figure()
        cf.upper_pad = self.upper_pad.value()
        cf.lower_pad = self.lower_pad.value()
        cf.left_pad = self.left_pad.value()
        cf.right_pad = self.right_pad.value()
        cf.spacing = self.spacing.value()
        cf.update_gridspec()
        cf.draw()

    def adjust_axes_offset(self):
        ui = self.parent
        cf = ui.get_current_figure()
        cf.axis_offset = self.axis_offset.value()
        for sp in cf.subplots:
            sp.arrange_axes()
            sp.show_legend()
        cf.update_gridspec()
        cf.draw()

    def adjust_weights(self):
        """Adjusts subplot vertical aspect ratios.
        Sequence of digits between 1-9 are accepted.
        """
        if self.weights_edited:
            ui = self.parent
            cf = ui.get_current_figure()
            nplots = cf.nplots()
            new_weights = []
            for i in self.weights_edit.text():
                if i in '0, []':  # ignore zero, commas, spaces, and brackets
                    continue
                elif i.isdigit():
                    new_weights.append(int(i))
                else:
                    ui.statusBar().showMessage(
                            'Only integer inputs <10 allowed')
                    self.weights_edit.setText(str(cf.weights()))
                    return
            if len(new_weights) != nplots:
                ui.statusBar().showMessage(
                        'Figure has {} subplots but {} weights were provided'
                        .format(nplots, len(new_weights)))
                self.weights_edit.setText(str(cf.weights()))
                return

            g = functools.reduce(math.gcd, new_weights)
            # simplify weights by their greatest common denominator
            # (eg [2,2,4] -> [1,1,2])
            weights = [x//g for x in new_weights]
            self.weights_edit.setText(str(weights))
            self.weights_edited = False
            cf.update_gridspec(nplots, weights)
            cf.draw()

    def wte(self):
        self.weights_edited = True

    def update_grid(self):
        ui = self.parent
        cf = ui.get_current_figure()
        cf.MX = self.major_x.isChecked()
        cf.mx = self.minor_x.isChecked()
        cf.MY = self.major_y.isChecked()
        cf.my = self.minor_y.isChecked()

        M_i = self.major_slider.value()
        m_i = self.minor_slider.value()
        M_T = ui.M_steps[M_i] # in hours
        m_T = ui.m_steps[M_i][m_i] # in minutes
        if not cf.verify_ticks(M_T, m_T):
            M_i = self.major_slider.value()
            m_i = self.minor_slider.value()
            if m_i != 0:
                self.minor_slider.setValue(m_i-1)
            else:
                self.major_slider.setValue(M_i-1)
                self.minor_slider.setMaximum(len(ui.m_steps[M_i])-1)
            ui.statusBar().showMessage('Tick density too high.')
        else:
            self.update_freq_labels(M_T, m_T)
            cf.M_T = M_T
            cf.m_T = m_T
            cf.format_axes()
            cf.draw()

    def update_freq_labels(self, M_T, m_T):
        if M_T%24 == 0:
            self.major_T.setText('Major X Tick: 1 day')
        elif M_T != 1:
            self.major_T.setText('Major X Tick: {} hrs'.format(M_T))
        else:
            self.major_T.setText('Major X Tick: 1 hr')

        if m_T%1440 == 0:
            self.minor_T.setText('Minor X Tick: 1 day')
        elif 60 < m_T:
            self.minor_T.setText('Minor X Tick: {} hrs'
                                          .format(m_T//60))
        elif m_T == 60:
            self.minor_T.setText('Minor X Tick: 1 hr')
        else:
            self.minor_T.setText('Minor X Tick: {} mins'.format(m_T))

    def update_plots(self):
        ui = self.parent
        cf = ui.get_current_figure()
        cf.scatter = self.scatter.isChecked()
        cf.dot_size = self.dot_size.value()
        cf.density = self.density.value()
        cf.x_margin = self.x_margin.value()
        cf.replot()
        cf.draw()

    def set_start_min(self):
        self.select_start.setDateTime(self.select_start.minimumDateTime())

    def set_end_max(self):
        self.select_end.setDateTime(self.select_end.maximumDateTime())

    def update_start(self, start):
        ui = self.parent
        cf = ui.get_current_figure()
        cf.start = start.toPyDateTime()
        self.cap_start_end()
        cf.draw()

    def update_end(self, end):
        ui = self.parent
        cf = ui.get_current_figure()
        cf.end = end.toPyDateTime()
        self.cap_start_end()
        cf.draw()

    def cap_start_end(self, cf=None):
        """Limits start and end datetimes by loaded data extents."""
        ui = self.parent
        if cf is None:
            cf = ui.get_current_figure()
        groups = [ui.all_groups[group_name] for group_name in cf.groups]
        if groups:
            data_start = min([group.data.index[0] for group in groups])
            data_end = max([group.data.index[-1] for group in groups])
            cf.start = max([data_start, cf.start])
            cf.end = min([data_end, cf.end])
        else:
            data_start = dt.datetime.strptime('2000-01-01 00:00:00',
                                            '%Y-%m-%d  %H:%M:%S')
            data_end = dt.datetime.now()
        self.select_start.setMinimumDateTime(data_start)
        self.select_start.setMaximumDateTime(cf.end)
        self.select_end.setMaximumDateTime(data_end)
        self.select_end.setMinimumDateTime(cf.start)

        if not cf.verify_ticks(cf.M_T, cf.m_T):
            M_i = self.major_slider.value()
            m_i = self.minor_slider.value()
            if m_i != 0:
                self.minor_slider.setValue(m_i-1)
            else:
                self.major_slider.setValue(M_i-1)
                self.minor_slider.setMaximum(len(ui.m_steps[M_i])-1)
            ui.statusBar().showMessage('Tick density too high.')
        else:
            cf.replot()

    def update_fonts(self):
        ui = self.parent
        cf = ui.get_current_figure()
        cf.title_size = self.title_size.value()
        cf.label_size = self.label_size.value()
        cf.tick_size = self.tick_size.value()
        cf.tick_rot = self.tick_rot.value()
        cf.format_axes()
        cf.draw()

    def edit_timestamp_format(self):
        ui = self.parent
        cf = ui.get_current_figure()
        codes = (
                ('Code', 'Description', 'Values'),
                ('', '', ''),
                ('%d', 'Day of month\t', '[01-31]'),
            #    ('%-d', 'Day of month\t', '[1-31]'),
                ('%b', 'Short month\t', '[Jan-Dec]'),
                ('%B', 'Long month\t', '[January-December]'),
                ('%m', 'Month zero-pad', '[01-12]'),
            #    ('%-m', 'Month\t', '[1-12]'),
                ('%y', 'Short year\t', '[00-99]'),
                ('%Y', 'Year with century', '[2000-2099]'),
                ('%H', '24-Hour zero-pad', '[00-23]'),
            #    ('%-H', '24-Hour\t', '[0-23]'),
                ('%I', '12-Hour zero-pad', '[01-12]'),
            #    ('%-I', '12-Hour\t', '[1-12]'),
                ('%M', 'Minute zero-pad', '[00-59]'),
                ('%S', 'Second zero-pad', '[00-59]'),
                )
        reference = ''
        for code in codes:
            reference += '{}\t{}\t{}\n'.format(*code)
        reference += '\nSee strftime.org for more details'
        
        tsf_dlg = QInputDialog(self)
        tsf_dlg.setWindowTitle('Edit Timestamp Format')
        tsf_dlg.setLabelText(reference)
        tsf_dlg.setTextValue(cf.tsf)
        ok = tsf_dlg.exec()
        if ok:
            text = tsf_dlg.textValue()
            try:
                dt.datetime.now().strftime(text)
            except ValueError:
                self.edit_timestamp_format()
            else:
                cf.tsf = text
                cf.format_axes()
                cf.draw()

    def update_unit_table(self):
        """Updates table associating unit types with colors."""
        ui = self.parent
        self.unit_table.setRowCount(len(ui.all_units()))
        for i, unit_type in enumerate(ui.all_units()):
            if unit_type not in ui.color_dict:
                ui.color_dict.update({unit_type:'C'+str(i%10)})
            color = QColor(mcolors.to_hex(ui.color_dict[unit_type]))
            self.dlg.setCustomColor(i, color)
            item = QTableWidgetItem(unit_type)
            item.setFlags(Qt.ItemIsSelectable)
            self.unit_table.setItem(i, 0, item)
            color = mcolors.to_hex(ui.color_dict[unit_type])
            colorButton = QColorButton(self, color, unit_type)
            colorButton.clicked.connect(self.pick_color)
            _widget = QWidget()
            _layout = QVBoxLayout(_widget)
            _layout.addWidget(colorButton)
            _layout.setAlignment(Qt.AlignCenter)
            _layout.setContentsMargins(0,0,0,0)
            self.unit_table.setCellWidget(i, 1, _widget)
        all_types = [unit_type for unit_type in ui.color_dict.keys()]
        for unit_type in all_types:
            if unit_type not in ui.all_units():
                del ui.color_dict[unit_type]

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
            ui = self.parent
            ui.color_dict[unit_type] = color_button.color
            cf = ui.get_current_figure()
            cf.replot()
            cf.draw()

    def update_fields(self, cf):
        ui = self.parent
        widgets = self.findChildren(QWidget)
        for w in widgets: w.blockSignals(True)
        self.upper_pad.setValue(cf.upper_pad)
        self.lower_pad.setValue(cf.lower_pad)
        self.left_pad.setValue(cf.left_pad)
        self.right_pad.setValue(cf.right_pad)
        self.spacing.setValue(cf.spacing)
        self.axis_offset.setValue(cf.axis_offset)
        self.weights_edit.setText(str(cf.weights()))
        self.major_x.setChecked(cf.MX)
        self.minor_x.setChecked(cf.mx)
        self.major_y.setChecked(cf.MY)
        self.minor_y.setChecked(cf.my)
        M_i = ui.M_steps.index(cf.M_T)
        m_i = ui.m_steps[M_i].index(cf.m_T)
        self.major_slider.setValue(M_i)
        self.minor_slider.setMaximum(len(ui.m_steps[M_i])-1)
        self.minor_slider.setValue(m_i)
        self.update_freq_labels(cf.M_T, cf.m_T)
        self.scatter.setChecked(cf.scatter)
        self.line.setChecked(not cf.scatter)
        self.dot_size.setValue(cf.dot_size)
        self.density.setValue(cf.density)
        self.x_margin.setValue(cf.x_margin)
        self.title_size.setValue(cf.title_size)
        self.label_size.setValue(cf.label_size)
        self.tick_size.setValue(cf.tick_size)
        self.tick_rot.setValue(cf.tick_rot)
        self.cap_start_end()
        self.select_start.setDateTime(cf.start)
        self.select_end.setDateTime(cf.end)
        for w in widgets: w.blockSignals(False)
