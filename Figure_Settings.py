# -*- coding: utf-8 -*-
"""
Created on Mon May 13 12:27:59 2019

@author: seery
"""
class QColorButton(QPushButton):
        def __init__(self, parent, color, unit_type):
            super(QColorButton, self).__init__()
            self.parent = parent
            self.color = color
            self.setStyleSheet("background-color:{};".format(color))
            self.unit_type = unit_type


class Figure_Settings(QWidget):
    def __init__(self, parent, saved=None):
        super().__init__()
        self.parent = parent
        TG = self.parent
### ALSO INCLUDE START/END TIME FOR PLOTTING


        # Read saved values from .txt file

        grid = QGridLayout()
        figBounds = QLabel('Figure Dimensions')
        figUpper = QLabel('Top')
        self.figUpper = QSpinBox()
        figLower = QLabel('Bottom')
        self.figLower = QSpinBox()
        figLeft = QLabel('Left')
        self.figLeft = QSpinBox()
        figRight = QLabel('Right')
        self.figRight = QSpinBox()
        hspace = QLabel('Spacing')
        self.hspace = QSpinBox()
        parOffset = QLabel('Secondary Axis Offset')
        self.parOffset = QSpinBox()
        legendOffset = QLabel('Legend Offset')
        self.legendOffset = QSpinBox()
        tickRot = QLabel('Tick Rotation')
        self.tickRot = QSpinBox()

        gridToggles = QLabel('Axes Settings')
        self.majorXgrid = QCheckBox('Major X')
        self.minorXgrid = QCheckBox('Minor X')
        self.majorYgrid = QCheckBox('Major Y')
        self.minorYgrid = QCheckBox('Minor Y')

        labelSettings = QLabel('Text Settings')
        self.font = QPushButton('Font')
        labelSize = QLabel('Axis Label Size')
        self.labelSize = QComboBox()
        titleSize = QLabel('Title Size')
        self.titleSize = QComboBox()
        tickSize = QLabel('Tick Size')
        self.tickSize = QComboBox()

        self.dlg = QColorDialog()
        for i, unit_type in enumerate(TG.unit_dict):
            self.dlg.setCustomColor(i, QColor(mcolors.to_hex(TG.color_dict[unit_type])))

        self.unit_table = QTableWidget()
        self.unit_table.setColumnCount(2)
        self.unit_table.setRowCount(len(TG.unit_dict))

        for i, unit_type in enumerate(TG.unit_dict):
            self.unit_table.setItem(i, 0, QTableWidgetItem(unit_type))
            colorButton = QColorButton(self, mcolors.to_hex(TG.color_dict[unit_type]), unit_type)
            colorButton.clicked.connect(self.pick_color)
            self.unit_table.setCellWidget(i, 1, colorButton)

        widgets = [
                figBounds,
                hspace,
                self.hspace,
                figUpper,
                self.figUpper,
                figLower,
                self.figLower,
                figLeft,
                self.figLeft,
                figRight,
                self.figRight,
                parOffset,
                self.parOffset,
                legendOffset,
                self.legendOffset,
                tickRot,
                self.tickRot,
                gridToggles,
                self.majorXgrid,
                self.minorXgrid,
                self.majorYgrid,
                self.minorYgrid,
                labelSettings,
                self.font,
                labelSize,
                self.labelSize,
                titleSize,
                self.titleSize,
                tickSize,
                self.tickSize,
                self.unit_table,
                ]

        positions = [
                (0,0,1,2),  # Figure Dimensions
                (1,0,1,1),
                (1,1,1,1),
                (2,0,1,1),
                (2,1,1,1),
                (3,0,1,1),
                (3,1,1,1),
                (4,0,1,1),
                (4,1,1,1),
                (5,0,1,1),
                (5,1,1,1),
                (6,0,1,1),
                (6,1,1,1),
                (7,0,1,1),
                (7,1,1,1),
                (8,0,1,1),
                (8,1,1,1),
                (9,0,1,2),  # Axes Settings
                (10,0,1,2),
                (11,0,1,2),
                (12,0,1,2),
                (13,0,1,2),
                (14,0,1,2),  # Text Settings
                (15,0,1,1),
                (15,1,1,1),
                (16,0,1,1),
                (16,1,1,1),
                (17,0,1,1),
                (17,1,1,1),
                (18,0,1,1),
                (18,1,1,1),
                (19,0,1,2),
                ]

        for w, p in zip(widgets, positions):
            grid.addWidget(w, *p)
        self.setLayout(grid)

    def pick_color(self):
        colorButton = QObject.sender(self)
        unit_type = colorButton.unit_type
        if colorButton.color:
            self.dlg.setCurrentColor(QColor(colorButton.color))

        if self.dlg.exec_():
            colorButton.color = self.dlg.currentColor().name()
            colorButton.setStyleSheet("background-color:{};".format(colorButton.color))
            self.color_dict[unit_type] = colorButton.color





