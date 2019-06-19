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

class Unit_Settings(QDialog):

    def __init__(self, parent):
        super().__init__()
        self.parent = parent
        self.setWindowTitle('Unit Settings')
        self.setWindowIcon(QIcon('rc/satellite.png'))
#        self.setFixedSize(200,333)
        CT = self.parent
        DM = CT.parent
        AB = DM.parent

        vbox = QVBoxLayout()

        form = QFormLayout()
        self.autoParseCheck = QCheckBox('Automatically parse units from headers')
        self.autoParseCheck.setChecked(AB.auto_parse)
        self.autoParseCheck.stateChanged.connect(self.toggle_auto_parse)
        form.addRow(self.autoParseCheck)

        self.baseType = QComboBox()
        self.baseType.addItems(list(AB.unit_dict.keys()))
        self.baseType.currentIndexChanged.connect(self.update_pht)
        form.addRow('Base Unit Types', self.baseType)

        self.newType = QLineEdit()
        self.update_pht()
        self.newType.editingFinished.connect(self.add_user_type)
        form.addRow(self.newType)
        self.userUnits = QComboBox()
        entries = []
        for userType in AB.user_units:
            for baseType in AB.unit_dict:
                if AB.user_units[userType] == AB.unit_dict[baseType]:
                    entries.append('{} ({})'.format(userType, baseType))
                    break
        self.userUnits.addItems(entries)
        self.delete = QPushButton('Delete User Type')
        self.delete.clicked.connect(self.delete_user_type)
        form.addRow(self.delete, self.userUnits)
        self.defaultType = QLineEdit()
        self.defaultType.setPlaceholderText('None')
        if AB.default_type: self.defaultType.setText(AB.default_type)
        form.addRow('Set Default Type', self.defaultType)
        self.defaultUnit = QLineEdit()
        self.defaultUnit.setPlaceholderText('None')
        if AB.default_unit: self.defaultUnit.setText(AB.default_unit)
        form.addRow('Set Default Unit', self.defaultUnit)
        vbox.addLayout(form)

        self.clarified = QTableWidget()
        self.clarified.setColumnCount(2)
        self.clarified.setHorizontalHeaderLabels(['Parsed', 'Interpreted'])
        self.clarified.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
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
        CT = self.parent
        DM = CT.parent
        AB = DM.parent
        AB.auto_parse = self.autoParseCheck.isChecked()

    def update_pht(self):
        baseType = self.baseType.currentText()
        self.newType.setPlaceholderText('New unit type ({})'.format(baseType))

    def add_user_type(self):
        CT = self.parent
        DM = CT.parent
        AB = DM.parent
        newType = self.newType.text().strip()
        baseType = self.baseType.currentText()
        all_units = {**AB.unit_dict, **AB.user_units}
        if newType and newType not in all_units:
            AB.user_units.update({newType: AB.unit_dict[baseType]})
            entry = '{} ({})'.format(newType, baseType)
            self.userUnits.addItem(entry)
            self.userUnits.setCurrentText(entry)

    def delete_user_type(self):
        CT = self.parent
        DM = CT.parent
        AB = DM.parent
        entry = self.userUnits.currentText()
        userType = entry[:entry.rindex('(')-1]
        del AB.user_units[userType]
        self.userUnits.removeItem(self.userUnits.currentIndex())

    def populate_clarified(self):
        CT = self.parent
        DM = CT.parent
        AB = DM.parent
        self.clarified.setRowCount(len(AB.unit_clarify))
        for r, key in enumerate(AB.unit_clarify):
            self.clarified.setItem(r, 0, QTableWidgetItem(key))
            key_clar = QComboBox()
            key_clar.addItems([x for unit_list in AB.unit_dict.values() for x in unit_list])
            key_clar.setCurrentText(AB.unit_clarify[key])
            self.clarified.setCellWidget(r, 1, key_clar)

    def add_clarified_row(self):
        CT = self.parent
        DM = CT.parent
        AB = DM.parent
        self.clarified.setRowCount(self.clarified.rowCount()+1)
        key_clar = QComboBox()
        key_clar.addItems([x for unit_list in AB.unit_dict.values() for x in unit_list])
        self.clarified.setCellWidget(self.clarified.rowCount()-1, 1, key_clar)

    def delete_clarified_row(self):
        rows_to_delete = set([item.row() for item in self.clarified.selectedIndexes()])
        for r in sorted(rows_to_delete, reverse=True):
            self.clarified.removeRow(r)

    def reset_background(self, row, column):
        CT = self.parent
        DM = CT.parent
        AB = DM.parent
        if AB.current_rcs == AB.dark_rcs:
            bg = QColor.fromRgb(35, 38, 41)
        else:
            bg = QColor.fromRgb(255, 255, 255)
        self.clarified.item(row, column).setBackground(QBrush(bg))

    def closeEvent(self, event):
        CT = self.parent
        DM = CT.parent
        AB = DM.parent
        keys, values = [], []
        ok = True
        for r in range(self.clarified.rowCount()):
            try:
                key = self.clarified.item(r, 0).text()
                if key.strip():
                    if key not in keys:
                        keys.append(key)
                        values.append(self.clarified.cellWidget(r, 1).currentText())
                    else:
                        self.clarified.blockSignals(True)
                        # have it just select the duplicates instead of highlighting red?
                        self.clarified.item(r, 0).setBackground(QBrush(QColor.fromRgb(255, 50, 50)))
                        self.clarified.blockSignals(False)
                        ok = False
            except AttributeError:
                continue
        if ok:
            AB.unit_clarify = dict(zip(keys,values))
            AB.default_type = self.defaultType.text().strip()
            AB.default_unit = self.defaultUnit.text().strip()
            AB.figure_settings.update_unit_table()

# some strange behavior with this code. Leave out if not necessary. User now needs to explicitly click 'reparse units'.
#            group_name = CT.selectGroup.currentText()
#            if group_name:
#                group = DM.groups[group_name]
#                DM.configure_tab.populate_headerTable(group)

            event.accept()
        else:
            event.ignore()

    def keyPressEvent(self, event):
        """Enables dialog closure by escape key."""
        if event.key() == Qt.Key_Escape:
            self.close()