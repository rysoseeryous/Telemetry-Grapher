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

        mpl.rc('font', family='serif')  # controlable later maybe
        # Read saved values from .txt file

        grid = QGridLayout()

        figBounds = QLabel('Figure Dimensions')
        figBounds.setAlignment(Qt.AlignCenter)
        figHeight = QLabel('Height')
        self.figHeight = QDoubleSpinBox()
        self.figHeight.setRange(0, 1)
        self.figHeight.setSingleStep(.01)
        self.figHeight.setValue(.90)
        figWidth = QLabel('Width')
        self.figWidth = QDoubleSpinBox()
        self.figWidth.setRange(0, 1)
        self.figWidth.setSingleStep(.01)
        self.figWidth.setValue(.90)
        hspace = QLabel('V Offset')
        self.hspace = QDoubleSpinBox()
        self.hspace.setRange(0, 1)
        self.hspace.setSingleStep(.01)
        self.hspace.setValue(.05)
        parOffset = QLabel('H Offset')
        self.parOffset = QDoubleSpinBox()
        self.parOffset.setRange(0, 1)
        self.parOffset.setSingleStep(.01)
        self.parOffset.setValue(.05)
        legendOffset = QLabel('Legend Offset')
        self.legendOffset = QDoubleSpinBox()
        self.legendOffset.setRange(0, 1)
        self.legendOffset.setSingleStep(.01)
        self.legendOffset.setValue(.1)

        gridToggles = QLabel('Grid Settings')
        gridToggles.setAlignment(Qt.AlignCenter)
        self.majorXgrid = QCheckBox('Major X')
        self.minorXgrid = QCheckBox('Minor X')
        self.majorYgrid = QCheckBox('Major Y')
        self.minorYgrid = QCheckBox('Minor Y')

        textSettings = QLabel('Text Settings')
        textSettings.setAlignment(Qt.AlignCenter)
        titleSize = QLabel('Title')
        self.titleSize = QSpinBox()
        self.titleSize.setRange(0, 60)
        self.titleSize.setValue(20)
        labelSize = QLabel('Axis Labels')
        self.labelSize = QSpinBox()
        self.labelSize.setRange(0, 60)
        self.labelSize.setValue(12)
        tickSize = QLabel('Tick Size')
        self.tickSize = QSpinBox()
        self.tickSize.setRange(0, 20)
        self.tickSize.setValue(10)
        tickRot = QLabel('Tick Rotation')
        self.tickRot = QSpinBox()
        self.tickRot.setRange(0, 90)
        self.tickRot.setValue(50)

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
                figHeight,
                self.figHeight,
                figWidth,
                self.figWidth,
                hspace,
                self.hspace,
                parOffset,
                self.parOffset,
                legendOffset,
                self.legendOffset,

                gridToggles,
                self.majorXgrid,
                self.minorXgrid,
                self.majorYgrid,
                self.minorYgrid,

                textSettings,
                titleSize,
                self.titleSize,
                labelSize,
                self.labelSize,
                tickSize,
                self.tickSize,
                tickRot,
                self.tickRot,

                self.unit_table,
                ]

        positions = [
                (4,0,1,2),  # Figure Dimensions
                (5,0,1,1),
                (5,1,1,1),
                (6,0,1,1),
                (6,1,1,1),
                (7,0,1,1),
                (7,1,1,1),
                (8,0,1,1),
                (8,1,1,1),
                (9,0,1,1),
                (9,1,1,1),

                (11,0,1,2),  # Grid Settings
                (12,0,1,1),
                (12,1,1,1),
                (13,0,1,1),
                (13,1,1,1),

                (15,0,1,2),  # Text Settings
                (16,0,1,1),
                (16,1,1,1),
                (17,0,1,1),
                (17,1,1,1),
                (18,0,1,1),
                (18,1,1,1),
                (19,0,1,1),
                (19,1,1,1),

                (21,0,1,2),  # Color Palette
                ]

        for w, p in zip(widgets, positions):
            grid.addWidget(w, *p)
        self.setLayout(grid)

    def connect_widgets(self, container):
        widgets = [
                self.figHeight,
                self.figWidth,
                self.hspace,
                self.parOffset,
                self.legendOffset,

                self.majorXgrid,
                self.minorXgrid,
                self.majorYgrid,
                self.minorYgrid,

                self.titleSize,
                self.labelSize,
                self.tickSize,
                self.tickRot,

                self.unit_table,
                ]
        for w in widgets[0:5]:
            w.valueChanged.connect(container.refresh_all)
        for w in widgets[9:13]:
            w.valueChanged.connect(container.refresh_all)

    def pick_color(self):
        colorButton = QObject.sender(self)
        unit_type = colorButton.unit_type
        if colorButton.color:
            self.dlg.setCurrentColor(QColor(colorButton.color))

        if self.dlg.exec_():
            colorButton.color = self.dlg.currentColor().name()
            colorButton.setStyleSheet("background-color:{};".format(colorButton.color))
            self.color_dict[unit_type] = colorButton.color





