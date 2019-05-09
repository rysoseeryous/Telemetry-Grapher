# -*- coding: utf-8 -*-
"""
Created on Wed May  8 11:26:02 2019

@author: seery
"""
from PyQt5.QtWidgets import *

class Configure_Tab(QWidget):
    def __init__(self, parent):
        super().__init__()
        self.parent = parent
        self.grid = QGridLayout()

        self.selectGroup = QComboBox()
#        self.selectGroup.addItem('(select)')
        self.selectGroup.addItems(self.parent.groups.keys())
        self.selectGroup.currentIndexChanged.connect(self.display_header_info)
        self.settings = QPushButton('Unit Settings')
        self.settings.clicked.connect(self.open_settings)
        # Not doing a delete button here. All that control should stay in Import Tab
        self.headerTable = QTableWidget()
        self.headerTable.setColumnCount(5)
        self.headerTable.setHorizontalHeaderLabels(['Keep','Original Header','Header to Display','Unit Type','Unit'])

        widgets = [
                self.selectGroup,
                self.settings,
                self.headerTable,
                ]

        positions = [
                (0,0,1,1),
                (1,0,1,1),
                (0,1,3,1),
                ]

        for w, p in zip(widgets, positions):
            self.grid.addWidget(w, *p)
        self.setLayout(self.grid)

    def display_header_info(self):
        TG = self.parent.parent
        DM = self.parent
        name = self.selectGroup.currentText()
        group = DM.groups[name]
        series_units = DM.data_dict[name]
        self.headerTable.setRowCount(len(series_units))

        for i, series in enumerate(series_units):
            unit_type = TG.get_unit_type(series_units[series])
            self.headerTable.setCellWidget(i, 0, QCheckBox())
            self.headerTable.setItem(i, 1, QTableWidgetItem(series))

            self.headerTable.setItem(i, 2, QTableWidgetItem(group.alias_dict[series]))

            type_combo = QComboBox()
            type_combo.addItems(list(TG.unit_dict.keys()))
            type_combo.setCurrentText(unit_type)
            type_combo.setProperty("row", i)
            type_combo.currentIndexChanged.connect(self.update_unit_combo)
            self.headerTable.setCellWidget(i, 3, type_combo)

            unit_combo = QComboBox()
            unit_combo.addItems(list(TG.unit_dict[unit_type]))
            unit_combo.setCurrentText(series_units[series])
            unit_combo.setProperty("row", i)
            unit_combo.currentIndexChanged.connect(self.update_series_unit)
            self.headerTable.setCellWidget(i, 4, unit_combo)
        self.headerTable.cellChanged.connect(self.update_alias_dict)

    def update_alias_dict(self, row, column):
        DM = self.parent
        name = self.selectGroup.currentText()
        series = self.headerTable.item(row, 1).text()
        alias = self.headerTable.item(row, column).text()
        DM.groups[name].alias_dict[series] = alias
        DM.modified = True

    def update_unit_combo(self):
        TG = self.parent.parent
        type_combo = QObject.sender(self)  # WOW this would have been nice to know.
        row = type_combo.property("row")
        unit_combo = self.headerTable.cellWidget(row, 4)
        unit_type = type_combo.currentText()
        unit_combo.clear()
        try:
            unit_combo.addItems(list(TG.unit_dict[unit_type]))
        except KeyError:
            pass

    def update_series_unit(self):
        TG = self.parent.parent
        DM = self.parent
        name = self.selectGroup.currentText()
        unit_combo = QObject.sender(self)
        row = unit_combo.property("row")
        unit = unit_combo.currentText()
        series = self.headerTable.item(row, 1).text()
        DM.data_dict[name][series] = unit
        DM.modified = True

    def open_settings(self):
        self.settings_dialog = Unit_Settings(self)
        self.settings_dialog.setModal(True)
        self.settings_dialog.show()
