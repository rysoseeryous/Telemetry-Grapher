# -*- coding: utf-8 -*-
"""
Created on Thu Jun 13 15:52:24 2019

@author: seery
"""
from PyQt5.QtWidgets import (QDialog,
                             QFormLayout, QHBoxLayout, QVBoxLayout,
                             QPushButton, QLineEdit, QCheckBox, QComboBox,
                             QHeaderView, QTableWidget, QTableWidgetItem)
from PyQt5.QtGui import QIcon, QBrush, QColor
from PyQt5.QtCore import Qt

class UnitSettings(QDialog):

    def __init__(self, parent):
        super().__init__()
        self.parent = parent
        self.setWindowTitle('Unit Settings')
        self.setWindowIcon(QIcon('rc/satellite.png'))
#        self.setFixedSize(200,333)
        ct = self.parent
        dm = ct.parent
        ui = dm.parent

        vbox = QVBoxLayout()

        form = QFormLayout()
        self.autoParseCheck = QCheckBox('Automatically parse'
                                        'units from headers')
        self.autoParseCheck.setChecked(ui.auto_parse)
        self.autoParseCheck.stateChanged.connect(self.toggle_auto_parse)
        form.addRow(self.autoParseCheck)

        self.baseType = QComboBox()
        self.baseType.addItems(list(ui.unit_dict.keys()))
        self.baseType.currentIndexChanged.connect(self.update_pht)
        form.addRow('Base Unit Types', self.baseType)

        self.newType = QLineEdit()
        self.update_pht()
        self.newType.editingFinished.connect(self.add_user_type)
        form.addRow(self.newType)
        self.userUnits = QComboBox()
        entries = []
        for userType in ui.user_units:
            for baseType in ui.unit_dict:
                if ui.user_units[userType] == ui.unit_dict[baseType]:
                    entries.append('{} ({})'.format(userType, baseType))
                    break
        self.userUnits.addItems(entries)
        self.delete = QPushButton('Delete User Type')
        self.delete.clicked.connect(self.delete_user_type)
        form.addRow(self.delete, self.userUnits)
        self.defaultType = QLineEdit()
        self.defaultType.setPlaceholderText('None')
        if ui.default_type: self.defaultType.setText(ui.default_type)
        form.addRow('Set Default Type', self.defaultType)
        self.defaultUnit = QLineEdit()
        self.defaultUnit.setPlaceholderText('None')
        if ui.default_unit: self.defaultUnit.setText(ui.default_unit)
        form.addRow('Set Default Unit', self.defaultUnit)
        vbox.addLayout(form)

        self.clarified = QTableWidget()
        self.clarified.setColumnCount(2)
        self.clarified.setHorizontalHeaderLabels(['Parsed', 'Interpreted'])
        h_header = self.clarified.horizontalHeader()
        h_header.setSectionResizeMode(QHeaderView.Stretch)
        self.clarified.verticalHeader().hide()
        self.clarified.cellChanged.connect(self.reset_background)
        self.populate_clarified()
        vbox.addWidget(self.clarified)

        hbox = QHBoxLayout()
        self.addRow = QPushButton('Add')
        self.addRow.clicked.connect(self.add_clarified_row)
        self.addRow.setDefault(True)
        hbox.addWidget(self.addRow)
        self.deleteRow = QPushButton('Delete')
        self.deleteRow.clicked.connect(self.delete_clarified_row)
        hbox.addWidget(self.deleteRow )
        vbox.addLayout(hbox)

        self.setLayout(vbox)

    def toggle_auto_parse(self):
        ct = self.parent
        dm = ct.parent
        ui = dm.parent
        ui.auto_parse = self.autoParseCheck.isChecked()

    def update_pht(self):
        baseType = self.baseType.currentText()
        self.newType.setPlaceholderText('New unit type ({})'.format(baseType))

    def add_user_type(self):
        ct = self.parent
        dm = ct.parent
        ui = dm.parent
        newType = self.newType.text().strip()
        baseType = self.baseType.currentText()
        all_units = {**ui.unit_dict, **ui.user_units}
        if newType and newType not in all_units:
            ui.user_units.update({newType: ui.unit_dict[baseType]})
            entry = '{} ({})'.format(newType, baseType)
            self.userUnits.addItem(entry)
            self.userUnits.setCurrentText(entry)

    def delete_user_type(self):
        ct = self.parent
        dm = ct.parent
        ui = dm.parent
        entry = self.userUnits.currentText()
        userType = entry[:entry.rindex('(')-1]
        del ui.user_units[userType]
        self.userUnits.removeItem(self.userUnits.currentIndex())

    def populate_clarified(self):
        ct = self.parent
        dm = ct.parent
        ui = dm.parent
        self.clarified.setRowCount(len(ui.unit_clarify))
        for r, key in enumerate(ui.unit_clarify):
            self.clarified.setItem(r, 0, QTableWidgetItem(key))
            key_clar = QComboBox()
            items = [u for units in ui.unit_dict.values() for u in units]
            key_clar.addItems(items)
            key_clar.setCurrentText(ui.unit_clarify[key])
            self.clarified.setCellWidget(r, 1, key_clar)

    def add_clarified_row(self):
        ct = self.parent
        dm = ct.parent
        ui = dm.parent
        self.clarified.setRowCount(self.clarified.rowCount()+1)
        key_clar = QComboBox()
        items = [u for units in ui.unit_dict.values() for u in units]
        key_clar.addItems(items)
        self.clarified.setCellWidget(self.clarified.rowCount()-1, 1, key_clar)

    def delete_clarified_row(self):
        all_rows = [item.row() for item in self.clarified.selectedIndexes()]
        for r in sorted(set(all_rows), reverse=True):
            self.clarified.removeRow(r)

    def reset_background(self, row, column):
        ct = self.parent
        dm = ct.parent
        ui = dm.parent
        if ui.current_rcs == ui.dark_rcs:
            bg = QColor.fromRgb(35, 38, 41)
        else:
            bg = QColor.fromRgb(255, 255, 255)
        self.clarified.item(row, column).setBackground(QBrush(bg))

    def closeEvent(self, event):
        ct = self.parent
        dm = ct.parent
        ui = dm.parent
        keys, values = [], []
        ok = True
        for r in range(self.clarified.rowCount()):
            try:
                key = self.clarified.item(r, 0).text()
                if key.strip():
                    if key not in keys:
                        keys.append(key)
                        value = self.clarified.cellWidget(r, 1).currentText()
                        values.append(value)
                    else:
                        self.clarified.blockSignals(True)
                        # select the duplicates instead of highlighting red?
                        self.clarified.item(r, 0).setBackground(QBrush(
                                QColor.fromRgb(255, 50, 50)))
                        self.clarified.blockSignals(False)
                        ok = False
            except AttributeError:
                continue
        if ok:
            ui.unit_clarify = dict(zip(keys,values))
            ui.default_type = self.defaultType.text().strip()
            ui.default_unit = self.defaultUnit.text().strip()
            ui.figure_settings.update_unit_table()  #???
            event.accept()
        else:
            event.ignore()

    def keyPressEvent(self, event):
        """Enables dialog closure by escape key."""
        if event.key() == Qt.Key_Escape:
            self.close()
