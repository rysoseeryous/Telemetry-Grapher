# -*- coding: utf-8 -*-
"""
Created on Thu Jun 13 15:48:55 2019

@author: seery
"""
from matplotlib import colors as mcolors

from PyQt5.QtWidgets import (QWidget, QColorDialog,
                             QGridLayout, QFormLayout,
                             QHBoxLayout, QVBoxLayout,
                             QGroupBox, QLabel, QCheckBox,
                             QRadioButton, QSpinBox, QDoubleSpinBox,
                             QHeaderView, QTableWidget, QTableWidgetItem)
from PyQt5.QtGui import QIcon, QColor
from PyQt5.QtCore import Qt, QObject

from .qcb import QColorButton

class Figure_Settings(QWidget):
    """Contains options for controlling figure size and appearance."""

    def __init__(self, parent, saved=None):
        super().__init__()
        self.parent = parent
        AB = self.parent
        self.markers = [  # when color coordination is on, use markers in this order to differentiate series
                'o',
                '+',
                'x',
                'D',
                's',
                '^',
                'v',
                '<',
                '>',
            ]
# Read saved values from .txt file?

        vbox = QVBoxLayout()

        figureGroup= QGroupBox('Figure Dimensions')
        figureGroup.setAlignment(Qt.AlignHCenter)
        form = QFormLayout()
        self.upperPad = QDoubleSpinBox()
        self.upperPad.setRange(0, 0.5)
        self.upperPad.setSingleStep(.01)
        self.upperPad.setValue(0.07)
        form.addRow('Upper Pad',self.upperPad)
        self.lowerPad = QDoubleSpinBox()
        self.lowerPad.setRange(0, 0.5)
        self.lowerPad.setSingleStep(.01)
        self.lowerPad.setValue(0.08)
        form.addRow('Lower Pad',self.lowerPad)
        self.leftPad = QDoubleSpinBox()
        self.leftPad.setRange(0, 0.5)
        self.leftPad.setSingleStep(.01)
        self.leftPad.setValue(0.05)
        form.addRow('Left Pad',self.leftPad)
        self.rightPad = QDoubleSpinBox()
        self.rightPad.setRange(0, 0.5)
        self.rightPad.setSingleStep(.01)
        self.rightPad.setValue(0.05)
        form.addRow('Right Pad',self.rightPad)
        self.hspace = QDoubleSpinBox()
        self.hspace.setRange(0, 1)
        self.hspace.setSingleStep(.01)
        self.hspace.setValue(.05)
        form.addRow('Spacing',self.hspace)
        self.parOffset = QDoubleSpinBox()
        self.parOffset.setRange(0, 1)
        self.parOffset.setDecimals(3)
        self.parOffset.setSingleStep(.005)
        self.parOffset.setValue(.05)
        form.addRow('Axis Offset',self.parOffset)
        figureGroup.setLayout(form)
        vbox.addWidget(figureGroup)


        gridGroup = QGroupBox('Grid Settings')
        gridGroup.setAlignment(Qt.AlignHCenter)
        grid = QGridLayout()
        self.majorXgrid = QCheckBox('Major X')
        grid.addWidget(self.majorXgrid, 0, 0)
        self.minorXgrid = QCheckBox('Minor X')
        grid.addWidget(self.minorXgrid, 0, 1)
        self.majorYgrid = QCheckBox('Major Y')
        grid.addWidget(self.majorYgrid, 1, 0)
        self.minorYgrid = QCheckBox('Minor Y')
        grid.addWidget(self.minorYgrid, 1, 1)
        gridGroup.setLayout(grid)
        vbox.addWidget(gridGroup)

        plotGroup = QGroupBox('Plot Settings')
        plotGroup.setAlignment(Qt.AlignHCenter)
        grid = QGridLayout()
        self.line = QRadioButton('Line')
        grid.addWidget(self.line, 0, 0)
        self.scatter = QRadioButton('Scatter')
        self.scatter.setChecked(True)
        grid.addWidget(self.scatter, 0, 1)
        grid.addWidget(QLabel('Marker Size'), 1, 0)
        self.dotsize = QDoubleSpinBox()
        self.dotsize.setRange(0, 5)
        self.dotsize.setSingleStep(.1)
        self.dotsize.setValue(0.5)
        grid.addWidget(self.dotsize, 1, 1)
        grid.addWidget(QLabel('Plot Density'), 2, 0)
        self.density = QSpinBox()
        self.density.setRange(0, 100)
        self.density.setSingleStep(5)
        self.density.setValue(100)
        self.density.setSuffix('%')
        grid.addWidget(self.density, 2, 1)
        plotGroup.setLayout(grid)
        vbox.addWidget(plotGroup)

        textGroup = QGroupBox('Text Settings')
        textGroup.setAlignment(Qt.AlignHCenter)
        form = QFormLayout()
        self.titleSize = QSpinBox()
        self.titleSize.setRange(0, 60)
        self.titleSize.setValue(30)
        form.addRow('Title', self.titleSize)
        self.labelSize = QSpinBox()
        self.labelSize.setRange(0, 30)
        self.labelSize.setValue(12)
        form.addRow('Axis Labels', self.labelSize)
        self.tickSize = QSpinBox()
        self.tickSize.setRange(0, 20)
        self.tickSize.setValue(10)
        form.addRow('Tick Size', self.tickSize)
        self.tickRot = QSpinBox()
        self.tickRot.setRange(0, 90)
        self.tickRot.setValue(45)
        form.addRow('Tick Rotation', self.tickRot)
        textGroup.setLayout(form)
        vbox.addWidget(textGroup)

        self.unit_table = QTableWidget()
        self.unit_table.setFixedWidth(123)
        self.unit_table.setColumnCount(2)
        self.unit_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        self.unit_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeToContents)
        self.unit_table.horizontalHeader().hide()
        self.unit_table.verticalHeader().hide()
        self.unit_table.verticalHeader().setDefaultSectionSize(self.unit_table.verticalHeader().minimumSectionSize())
        self.unit_table.verticalHeader().setSectionResizeMode(QHeaderView.Fixed)
        self.unit_table.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        vbox.addWidget(self.unit_table)
        self.setLayout(vbox)

        self.dlg = QColorDialog()
        self.dlg.setWindowIcon(QIcon('rc/satellite.png'))
        default_color = AB.current_rcs['axes.labelcolor']
        self.color_dict = {None:default_color, '':default_color}
        self.update_unit_table()

    def update_unit_table(self):
        """Updates table associating unit types with colors."""
        AB = self.parent
        all_units = {**AB.unit_dict, **AB.user_units}
        self.unit_table.setRowCount(len(all_units))
        for i, unit_type in enumerate(all_units):
            if unit_type not in self.color_dict:
                self.color_dict.update({unit_type:'C'+str(i%10)})
        for i, unit_type in enumerate(all_units):
            self.dlg.setCustomColor(i, QColor(mcolors.to_hex(self.color_dict[unit_type])))
        for i, unit_type in enumerate(all_units):
            self.unit_table.setItem(i, 0, QTableWidgetItem(unit_type))
            colorButton = QColorButton(self, mcolors.to_hex(self.color_dict[unit_type]), unit_type)
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
        widgets = [
                self.upperPad,
                self.lowerPad,
                self.leftPad,
                self.rightPad,
                self.hspace,
                self.parOffset,
                self.dotsize,
                self.titleSize,
                self.labelSize,
                self.tickSize,
                self.tickRot,
                self.density,
                ]
        for w in widgets:
            w.valueChanged.connect(container.refresh_all)

        widgets = [
                self.majorXgrid,
                self.minorXgrid,
                self.majorYgrid,
                self.minorYgrid,
                self.line,
                self.scatter,
                ]
        for w in widgets:
            w.toggled.connect(container.refresh_all)

    def pick_color(self):
        """Opens a color picker dialog and assigns it to the associated unit type."""
        colorButton = QObject.sender(self)
        unit_type = colorButton.unit_type
        if colorButton.color:
            self.dlg.setCurrentColor(QColor(colorButton.color))

        if self.dlg.exec_():
            colorButton.color = self.dlg.currentColor().name()
            colorButton.setStyleSheet("background-color:{};".format(colorButton.color))
            self.color_dict[unit_type] = colorButton.color
            AB = self.parent
            AF = AB.axes_frame
            AF.refresh_all()