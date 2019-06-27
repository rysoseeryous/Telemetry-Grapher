# -*- coding: utf-8 -*-
"""
Created on Thu Jun 13 15:48:55 2019

@author: seery
"""
import datetime as dt
from matplotlib import colors as mcolors

from PyQt5.QtWidgets import (QDockWidget, QWidget, QColorDialog, QInputDialog,
                             QGridLayout, QFormLayout,
                             QHBoxLayout, QVBoxLayout,
                             QGroupBox, QLabel, QCheckBox, QPushButton,
                             QRadioButton, QSpinBox, QDoubleSpinBox,
                             QHeaderView, QTableWidget, QTableWidgetItem)
from PyQt5.QtGui import QIcon, QColor
from PyQt5.QtCore import Qt, QObject

from ..internal.q_color_button import QColorButton

class FigureSettings(QDockWidget):
    """Contains options for controlling figure size and appearance."""

    def __init__(self, parent, title, saved=None):
        super().__init__(title)
        self.parent = parent
        ui = self.parent
        # when color coordination is on,
        # use markers in this order to differentiate series
        self.markers = ['o', '+', 'x', 'D', 's', '^', 'v', '<', '>']
# add to config.json?
        w = QWidget()
        vbox = QVBoxLayout()

        figure_group= QGroupBox('Figure Dimensions')
        figure_group.setAlignment(Qt.AlignHCenter)
        form = QFormLayout()
        self.upper_pad = QDoubleSpinBox()
        self.upper_pad.setRange(0, 0.5)
        self.upper_pad.setSingleStep(.01)
        self.upper_pad.setValue(0.07)
        form.addRow('Upper Pad', self.upper_pad)
        self.lower_pad = QDoubleSpinBox()
        self.lower_pad.setRange(0, 0.5)
        self.lower_pad.setSingleStep(.01)
        self.lower_pad.setValue(0.08)
        form.addRow('Lower Pad', self.lower_pad)
        self.left_pad = QDoubleSpinBox()
        self.left_pad.setRange(0, 0.5)
        self.left_pad.setSingleStep(.01)
        self.left_pad.setValue(0.05)
        form.addRow('Left Pad', self.left_pad)
        self.right_pad = QDoubleSpinBox()
        self.right_pad.setRange(0, 0.5)
        self.right_pad.setSingleStep(.01)
        self.right_pad.setValue(0.05)
        form.addRow('Right Pad', self.right_pad)
        self.spacing = QDoubleSpinBox()
        self.spacing.setRange(0, 1)
        self.spacing.setSingleStep(.01)
        self.spacing.setValue(.05)
        form.addRow('Spacing', self.spacing)
        self.axis_offset = QDoubleSpinBox()
        self.axis_offset.setRange(0, 1)
        self.axis_offset.setDecimals(3)
        self.axis_offset.setSingleStep(.005)
        self.axis_offset.setValue(.05)
        form.addRow('Axis Offset', self.axis_offset)
        figure_group.setLayout(form)
        vbox.addWidget(figure_group)

        grid_group = QGroupBox('Grid Settings')
        grid_group.setAlignment(Qt.AlignHCenter)
        grid = QGridLayout()
        self.major_x = QCheckBox('Major X')
        grid.addWidget(self.major_x, 0, 0)
        self.minor_x = QCheckBox('Minor X')
        grid.addWidget(self.minor_x, 0, 1)
        self.major_y = QCheckBox('Major Y')
        grid.addWidget(self.major_y, 1, 0)
        self.minor_y = QCheckBox('Minor Y')
        grid.addWidget(self.minor_y, 1, 1)
        grid_group.setLayout(grid)
        vbox.addWidget(grid_group)

        plot_group = QGroupBox('Plot Settings')
        plot_group.setAlignment(Qt.AlignHCenter)
        grid = QGridLayout()
        self.line = QRadioButton('Line')
        grid.addWidget(self.line, 0, 0)
        self.scatter = QRadioButton('Scatter')
        self.scatter.setChecked(True)
        grid.addWidget(self.scatter, 0, 1)
        grid.addWidget(QLabel('Marker Size'), 1, 0)
        self.dot_size = QDoubleSpinBox()
        self.dot_size.setRange(0, 5)
        self.dot_size.setSingleStep(.1)
        self.dot_size.setValue(0.5)
        grid.addWidget(self.dot_size, 1, 1)
        grid.addWidget(QLabel('Plot Density'), 2, 0)
        self.density = QSpinBox()
        self.density.setRange(1, 100)
        self.density.setSingleStep(5)
        self.density.setValue(100)
        self.density.setSuffix('%')
        grid.addWidget(self.density, 2, 1)
        plot_group.setLayout(grid)
        vbox.addWidget(plot_group)

        text_group = QGroupBox('Text Settings')
        text_group.setAlignment(Qt.AlignHCenter)
        form = QFormLayout()
        self.title_size = QSpinBox()
        self.title_size.setRange(0, 60)
        self.title_size.setValue(30)
        form.addRow('Title', self.title_size)
        self.label_size = QSpinBox()
        self.label_size.setRange(0, 30)
        self.label_size.setValue(12)
        form.addRow('Axis Labels', self.label_size)
        self.tick_size = QSpinBox()
        self.tick_size.setRange(0, 20)
        self.tick_size.setValue(10)
        form.addRow('Tick Size', self.tick_size)
        self.tick_rot = QSpinBox()
        self.tick_rot.setRange(0, 90)
        self.tick_rot.setValue(45)
        form.addRow('Tick Rotation', self.tick_rot)
        self.tsf = QPushButton('Timestamp Format')
        self.tsf.clicked.connect(self.edit_timestamp_format)
        self.timestamp_format = '%b %d, %H:%M'
        form.addRow(self.tsf)
        text_group.setLayout(form)
        vbox.addWidget(text_group)

        self.unit_table = QTableWidget()
        self.unit_table.setFixedWidth(123)
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

    def edit_timestamp_format(self):
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
                                   reference, text=self.timestamp_format)
        if ok:
            try:
                dt.datetime.now().strftime(text)
                self.timestamp_format = text
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
            self.unit_table.setItem(i, 0, QTableWidgetItem(unit_type))
            color = mcolors.to_hex(self.color_dict[unit_type])
            colorButton = QColorButton(self, color, unit_type)
            colorButton.clicked.connect(self.pick_color)
            _widget = QWidget()
            _layout = QHBoxLayout(_widget)
            _layout.addWidget(colorButton)
            _layout.setAlignment(Qt.AlignCenter)
            _layout.setContentsMargins(0,0,0,0)
            self.unit_table.setCellWidget(i, 1, _widget)

    def connect_widgets(self, container):
        """Connects widgets to refresh_all() in Axes Frame.
        Called by Application Base after Axes Frame has been instantiated."""
        widgets = [  # spin boxes
                self.upper_pad,
                self.lower_pad,
                self.left_pad,
                self.right_pad,
                self.spacing,
                self.axis_offset,
                self.dot_size,
                self.title_size,
                self.label_size,
                self.tick_size,
                self.tick_rot,
                self.density,
                ]
        for w in widgets:
            w.valueChanged.connect(container.refresh_all)

        widgets = [  # check boxes
                self.major_x,
                self.minor_x,
                self.major_y,
                self.minor_y,
                self.line,
                self.scatter,
                ]
        for w in widgets:
            w.toggled.connect(container.refresh_all)

        self.tsf.clicked.connect(container.refresh_all)

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
            af.refresh_all()
