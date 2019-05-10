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
        self.selectGroup.addItems(self.parent.groups.keys())
        self.selectGroup.currentIndexChanged.connect(self.display_header_info)
        self.settings = QPushButton('Unit Settings')
        self.settings.clicked.connect(self.open_settings)
        self.hideRows = QCheckBox('Hide Unused Headers')
        self.hideRows.setChecked(True)
        self.hideRows.stateChanged.connect(self.display_header_info)
        self.headerTable = QTableWidget()
        self.headerTable.setColumnCount(6)
        self.headerTable.setHorizontalHeaderLabels(['Keep','Original Header','Alias','Unit Type','Unit','Scaling Factor'])

        widgets = [
                self.selectGroup,
                self.settings,
                self.hideRows,
                self.headerTable,
                ]

        positions = [
                (0,0,1,1),
                (1,0,1,1),
                (2,0,1,1),
                (0,1,4,1),
                ]

        for w, p in zip(widgets, positions):
            self.grid.addWidget(w, *p)
        self.setLayout(self.grid)

        if self.selectGroup.currentText():
            self.display_header_info()
            self.parent.modified = False

    def display_header_info(self):
        try:
            self.headerTable.cellChanged.disconnect(self.update_alias_scale)
        except TypeError:
            pass
        TG = self.parent.parent
        DM = self.parent
        group = DM.groups[self.selectGroup.currentText()]
        if self.hideRows.isChecked():
            nKeep = 0
            for header in group.series:
                if group.series[header].keep: nKeep += 1
        else:
            nKeep = len(group.series)
        self.headerTable.setRowCount(nKeep)

        i = 0
        for header in group.series:  # iterates over index, key
            keep = group.series[header].keep
            if self.hideRows.isChecked():
                if not keep: continue
            alias = group.series[header].alias
            unit = group.series[header].unit
            unit_type = TG.get_unit_type(unit)

            keep_check = QCheckBox()
            keep_check.setChecked(keep)
            keep_check.setProperty("row", i)
            keep_check.stateChanged.connect(self.update_keep)
            self.headerTable.setCellWidget(i, 0, keep_check)

            self.headerTable.setItem(i, 1, QTableWidgetItem(header))

            self.headerTable.setItem(i, 2, QTableWidgetItem(alias))

            type_combo = QComboBox()
            type_combo.addItems(list(TG.unit_dict.keys()))
            type_combo.setCurrentText(unit_type)
            type_combo.setProperty("row", i)
            type_combo.currentIndexChanged.connect(self.update_unit_combo)
            self.headerTable.setCellWidget(i, 3, type_combo)

            unit_combo = QComboBox()
            unit_combo.addItems(list(TG.unit_dict[unit_type]))
            unit_combo.setCurrentText(unit)
            unit_combo.setProperty("row", i)
            unit_combo.currentIndexChanged.connect(self.update_series_unit)
            self.headerTable.setCellWidget(i, 4, unit_combo)

            self.headerTable.setItem(i, 5, QTableWidgetItem(str(group.series[header].scale)))
            i += 1
        self.headerTable.cellChanged.connect(self.update_alias_scale)

    def update_alias_scale(self, row, column):
        """Updates the alias and scaling factor of series when one of those two fields is edited"""
        DM = self.parent
        group = self.selectGroup.currentText()
        header = self.headerTable.item(row, 1).text()
        if column == 2:
            alias = self.headerTable.item(row, 2).text()
            def remove_key_by_value(dictionary, value):
                for key in dictionary:
                    if dictionary[key] == value:
                        del dictionary[key]
                        break
            if alias:
                DM.groups[group].series[header].alias = alias
                remove_key_by_value(DM.groups[group].alias_dict, header)
                DM.groups[group].alias_dict[alias] = header
            else:
                DM.groups[group].series[header].alias = None
                remove_key_by_value(DM.groups[group].alias_dict, header)
            DM.modified = True
        elif column == 5:
            scale = self.headerTable.item(row, 5).text()
            try:
                scale = float(scale)
                if scale == 0: raise ValueError
                DM.groups[group].series[header].scale = scale
                DM.modified = True
            except ValueError:
                DM.feedback('\"{}\" is not a valid scaling factor. Only nonzero real numbers permitted.'.format(scale))
                self.headerTable.setItem(row, 5, QTableWidgetItem(str(DM.groups[group].series[header].scale)))

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
        DM = self.parent
        group = self.selectGroup.currentText()
        unit_combo = QObject.sender(self)
        row = unit_combo.property("row")
        unit = unit_combo.currentText()
        header = self.headerTable.item(row, 1).text()
        DM.groups[group].series[header].unit = unit
        DM.modified = True

    def update_keep(self):
        DM = self.parent
        group = self.selectGroup.currentText()
        keep_check = QObject.sender(self)
        row = keep_check.property("row")
        header = self.headerTable.item(row, 1).text()
        DM.groups[group].series[header].keep = keep_check.isChecked()
        self.display_header_info()
        DM.modified = True

    def open_settings(self):
        self.settings_dialog = Unit_Settings(self)
        self.settings_dialog.setModal(True)
        self.settings_dialog.show()
