# -*- coding: utf-8 -*-
"""
Created on Thu Jun 13 15:51:56 2019

@author: seery
"""
import re
import pandas as pd

from PyQt5.QtWidgets import (QWidget, QFileDialog, QSizePolicy,
                             QHBoxLayout, QVBoxLayout, QGroupBox,
                             QPushButton, QLabel, QCheckBox, QComboBox,
                             QAbstractItemView, QHeaderView,
                             QTableView, QTableWidget, QTableWidgetItem)
from PyQt5.QtCore import Qt, QObject, QSortFilterProxyModel

from .unit_settings import Unit_Settings
from ..internal.pandas_model import Pandas_Model

class Configure_Tab(QWidget):

    def __init__(self, parent):
        super().__init__()
        self.parent = parent
        DM = self.parent
        AB = DM.parent
        vbox = QVBoxLayout()
        hbox = QHBoxLayout()

        self.selectGroup = QComboBox()
        self.selectGroup.addItems(AB.groups.keys())
        self.selectGroup.currentIndexChanged.connect(self.display_header_info)
        vbox.addWidget(self.selectGroup)

        self.export = QPushButton('Export DataFrame')
        self.export.clicked.connect(self.export_data)
        vbox.addWidget(self.export)

        self.settings = QPushButton('Unit Settings')
        self.settings.clicked.connect(self.open_settings)
        vbox.addWidget(self.settings)

        self.reparse = QPushButton('Reparse Headers')
        self.reparse.clicked.connect(self.reparse_units)
        vbox.addWidget(self.reparse)

        self.hideUnused = QCheckBox('Hide Unused Headers')
        self.hideUnused.setChecked(True)
        self.hideUnused.stateChanged.connect(self.display_header_info)
        vbox.addWidget(self.hideUnused)

        vbox.addStretch(1)
        summaryGroup = QGroupBox('DataFrame Summary')
        summaryGroup.setAlignment(Qt.AlignHCenter)
        summaryGroup.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Maximum)
        self.summary = QLabel()
        self.summary.setAlignment(Qt.AlignTop)
        summaryLayout = QVBoxLayout()
        summaryLayout.addWidget(self.summary)
        summaryGroup.setLayout(summaryLayout)
        vbox.addWidget(summaryGroup)
        hbox.addLayout(vbox)
        vbox = QVBoxLayout(spacing=0)

        self.headerTable = QTableWidget()
        self.headerTable.setRowCount(6)
        self.headerTable.horizontalHeader().sectionResized.connect(self.sync_col_width)
        self.headerTable.horizontalHeader().setFixedHeight(23)
        self.headerTable.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.headerTable.setVerticalHeaderLabels(['Keep','Scale','Original Header','Alias','Unit Type','Unit'])
        self.headerTable.verticalHeader().setFixedWidth(146)
        self.headerTable.verticalHeader().setDefaultSectionSize(23)
        self.headerTable.verticalHeader().setSectionResizeMode(QHeaderView.Fixed)
        self.headerTable.setFixedHeight(163)
        vbox.addWidget(self.headerTable)

        self.dfTable = QTableView()
        self.dfTable.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.dfTable.horizontalHeader().hide()
        self.dfTable.horizontalScrollBar().valueChanged.connect(self.sync_scroll)
        self.dfTable.verticalHeader().setDefaultSectionSize(self.dfTable.verticalHeader().minimumSectionSize())
        self.dfTable.verticalHeader().setSectionResizeMode(QHeaderView.Fixed)
        self.dfTable.verticalHeader().setFixedWidth(146)
        vbox.addWidget(self.dfTable)
        hbox.addLayout(vbox)
        self.setLayout(hbox)

        if self.selectGroup.currentText():
            self.display_header_info()
            self.parent.modified = False

    def reparse_units(self):
        """Reruns header parsing algorithm for selected columns."""
        DM = self.parent
        group_name = self.selectGroup.currentText()
        group = DM.groups[group_name]
        header_columns = [item.column() for item in self.headerTable.selectedItems()]
        headers = [self.headerTable.item(2, c).text() for c in set(header_columns)]
        DM.groups_tab.parse_series(group, headers)
        DM.configure_tab.headerTable.blockSignals(True)
        DM.configure_tab.populate_headerTable(group)
        DM.configure_tab.headerTable.blockSignals(False)

    def export_data(self):
        """Generate an Excel file for selected group, with only kept columns and aliases with units in square brackets."""
        DM = self.parent
        AB = DM.parent

        group_name = self.selectGroup.currentText()
        if group_name:
            savepath = str(QFileDialog.getExistingDirectory(self, "Save DataFrame as CSV"))
            if savepath:
                AB.save_dir = savepath  # store saving directory
                group = DM.groups[group_name]
                aliases = {}
                for header in group.series:
                    if group.series[header].keep:
                        alias = group.series[header].alias
                        unit = group.series[header].unit
                        if not alias:
                            alias = re.sub('\[{}\]'.format(unit), '', header).strip()
                        aliases[header] = ('{} [{}]'.format(alias, unit))
                df = group.data.loc[:, list(aliases.keys())]
                df.rename(columns=aliases, inplace=True)

                filename = savepath + '/' + group_name + '.csv'
                DM.feedback('Exporting DataFrame to {}... '.format(savepath))
                DM.messageLog.repaint()
                try:
                    with open(filename, 'w') as f:
                        df.to_csv(f, encoding='utf-8-sig')
                    DM.feedback('Done', mode='append')
                except PermissionError:
                    DM.feedback('Failed', mode='append')
                    DM.feedback('Permission denied. File {} is already open or is read-only.'.format(group_name + '.csv'))

    def sync_scroll(self, idx):
        self.headerTable.horizontalScrollBar().setValue(idx)

    def sync_col_width(self, col, old_size, new_size):
        self.dfTable.horizontalHeader().resizeSection(col, new_size)

    def days_hours_minutes(self, timedelta):
        return timedelta.days, timedelta.seconds//3600, (timedelta.seconds//60)%60

    def df_span_info(self, df):
        start = min(df.index)
        end = max(df.index)
        totalspan = self.days_hours_minutes(end - start)
        timeinterval = 0; i = 1
        while timeinterval == 0:
            timeinterval = (df.index[i]-df.index[i-1]).total_seconds()
            i += 1
        return df.shape, start, end, totalspan, timeinterval

    def populate_headerTable(self, group):
        DM = self.parent
        AB = DM.parent
        i = 0
        for header in group.series:
            keep = group.series[header].keep
            if self.hideUnused.isChecked():
                if not keep: continue
            alias = group.series[header].alias
            unit = group.series[header].unit
            unit_type = group.series[header].unit_type

            keep_check = QCheckBox()
            keep_check.setChecked(keep)
            keep_check.setProperty("col", i)
            keep_check.stateChanged.connect(self.update_keep)
            _widget = QWidget()
            _layout = QHBoxLayout(_widget)
            _layout.addWidget(keep_check)
            _layout.setAlignment(Qt.AlignCenter)
            _layout.setContentsMargins(0,0,0,0)
            self.headerTable.setCellWidget(0, i, _widget)

            self.headerTable.setItem(1, i, QTableWidgetItem(str(group.series[header].scale)))

            item = QTableWidgetItem(header)
            item.setFlags(Qt.ItemIsSelectable)
            self.headerTable.setItem(2, i, item)

            self.headerTable.setItem(3, i, QTableWidgetItem(alias))

            type_combo = QComboBox()
            all_units = {**AB.unit_dict, **AB.user_units}
            if AB.default_type and AB.default_type not in all_units:
                type_combo.addItem(AB.default_type)
            type_combo.addItem('')
            type_combo.addItems(list(all_units.keys()))
            type_combo.setCurrentText(unit_type)
            type_combo.setProperty("col", i)
            type_combo.currentIndexChanged.connect(self.update_unit_combo)
            self.headerTable.setCellWidget(4, i, type_combo)

            unit_combo = QComboBox()
            if unit_type:
                if unit_type in all_units:
                    unit_combo.addItems(list(all_units[unit_type]))
                else:
                    unit_combo.addItem(AB.default_unit)
            else:
                unit_combo.addItem(AB.default_unit)

            unit_combo.setCurrentText(unit)
            unit_combo.setProperty("col", i)
            unit_combo.currentIndexChanged.connect(self.update_series_unit)
            self.headerTable.setCellWidget(5, i, unit_combo)
            i += 1

    def populate_dfTable(self, group, df):
        shownRows = 20
        if len(df.index) > shownRows:
            upper_df = df.head(shownRows//2)
            lower_df = df.tail(shownRows//2)
            if self.hideUnused.isChecked():
                upper_df = upper_df.loc[:, [header for header in group.series if group.series[header].keep]]
                lower_df = lower_df.loc[:, [header for header in group.series if group.series[header].keep]]

            ellipses = pd.DataFrame(['...']*len(upper_df.columns),
                                    index=upper_df.columns,
                                    columns=['...']).T
            shown_df = upper_df.append(ellipses).append(lower_df)
        else:
            if self.hideUnused.isChecked():
                shown_df = df.loc[:, [header for header in group.series if group.series[header].keep]]
            else:
                shown_df = df
        shown_df.index = [ts.strftime('%Y-%m-%d  %H:%M:%S') if hasattr(ts, 'strftime') else '...' for ts in shown_df.index]

        self.model = Pandas_Model(shown_df)
        self.proxy = QSortFilterProxyModel()
        self.proxy.setSourceModel(self.model)
        self.dfTable.setModel(self.proxy)
        self.headerTable.setColumnCount(len(shown_df.columns))

    def summarize_data(self, df):
        shape, start, end, total_span, sampling_rate = self.df_span_info(df)
        shape_info = 'Shape Info:\n    {} rows\n    {} columns'.format(*shape)
        data_start = 'Data Start:\n    {}'.format(start.strftime('%Y-%m-%d  %H:%M:%S'))
        data_end = 'Data End:\n    {}'.format(end.strftime('%Y-%m-%d  %H:%M:%S'))
        span_info = 'Total Span:\n    {} days\n    {} hours\n    {} minutes'.format(*total_span)
        rate_info = 'Sampling Rate:\n    {} s'.format(sampling_rate)
        summary = shape_info + '\n' + data_start + '\n' + data_end + '\n' + span_info + '\n' + rate_info
        self.summary.setText(summary)

    def display_header_info(self):
        try:
            self.headerTable.cellChanged.disconnect(self.update_alias_scale)
        except TypeError:
            pass
        DM = self.parent
        group_name = self.selectGroup.currentText()
        if group_name:
            group = DM.groups[group_name]
            df = group.data
            self.summarize_data(df)
            self.populate_dfTable(group, df)
            self.headerTable.setRowCount(6)
            self.headerTable.setVerticalHeaderLabels(['Keep','Scale','Original Header','Alias','Unit Type','Unit'])
            self.populate_headerTable(group)
        else:
            self.headerTable.clear()
            self.headerTable.setRowCount(0)
            self.headerTable.setColumnCount(0)
            if hasattr(self, 'proxy'): self.proxy.deleteLater()
        self.headerTable.cellChanged.connect(self.update_alias_scale)

    def update_alias_scale(self, row, column):
        """Updates the alias and scaling factor of series when one of those two fields is edited"""
        DM = self.parent
        group = DM.groups[self.selectGroup.currentText()]
        header = self.headerTable.item(2, column).text()
        if row == 3:
            alias = self.headerTable.item(3, column).text().strip()  # remove any trailing/leading whitespace

            def remove_key_by_value(dictionary, value):
                for key in dictionary:
                    if dictionary[key] == value:
                        del dictionary[key]
                        break

            if alias and alias != group.series[header].alias:
                if alias in group.alias_dict:
                    DM.feedback('Alias "{}" is already in use. Please choose a different alias.'.format(alias))
                    self.headerTable.blockSignals(True)
                    self.headerTable.setItem(3, column, QTableWidgetItem(group.series[header].alias))
                    self.headerTable.blockSignals(False)
                    return
                if alias in group.data.columns:
                    DM.feedback('Alias "{}" is the name of an original header. Please choose a different alias.'.format(alias))
                    self.headerTable.blockSignals(True)
                    self.headerTable.setItem(3, column, QTableWidgetItem(group.series[header].alias))
                    self.headerTable.blockSignals(False)
                    return
                group.series[header].alias = alias
                remove_key_by_value(group.alias_dict, header)
                group.alias_dict[alias] = header
            else:
                group.series[header].alias = ''
                remove_key_by_value(group.alias_dict, header)
            DM.modified = True
        elif row == 1:
            scale = self.headerTable.item(1, column).text()
            try:
                scale = float(scale)
                if scale == 0: raise ValueError
                group.series[header].scale = scale
                DM.modified = True
            except ValueError:
                DM.feedback('"{}" is not a valid scaling factor. Only nonzero real numbers permitted.'.format(scale))
            self.headerTable.blockSignals(True)  # prevents infinite recursion when setItem would call this function again
            self.headerTable.setItem(1, column, QTableWidgetItem(str(group.series[header].scale)))
            self.headerTable.blockSignals(False)

    def update_unit_combo(self):
        DM = self.parent
        AB = DM.parent
        group = DM.groups[self.selectGroup.currentText()]
        type_combo = QObject.sender(self)
        col = type_combo.property("col")
        unit_type = type_combo.currentText()
        header = self.headerTable.item(2, col).text()
        group.series[header].unit_type = unit_type
        unit_combo = self.headerTable.cellWidget(5, col)
        unit_combo.clear()
        if unit_type in AB.user_units:
            unit_combo.addItems(list(AB.user_units[unit_type]))
        elif unit_type in AB.unit_dict:
            unit_combo.addItems(list(AB.unit_dict[unit_type]))
        elif AB.default_unit:
            unit_combo.addItem(AB.default_unit)
        DM.modified = True

    def update_series_unit(self):
        DM = self.parent
        group = DM.groups[self.selectGroup.currentText()]
        unit_combo = QObject.sender(self)
        col = unit_combo.property("col")
        unit = unit_combo.currentText()
        header = self.headerTable.item(2, col).text()
        group.series[header].unit = unit
        DM.modified = True

    def update_keep(self):
        DM = self.parent
        group = DM.groups[self.selectGroup.currentText()]
        keep_check = QObject.sender(self)
        header_columns = [keep_check.property("col")]
        header_columns.extend([item.column() for item in self.headerTable.selectedItems()])
        for c in set(header_columns):
            header = self.headerTable.item(2, c).text()
            group.series[header].keep = keep_check.isChecked()
        self.display_header_info()
        DM.modified = True

    def open_settings(self):
        self.settings_dialog = Unit_Settings(self)
        self.settings_dialog.setModal(True)
        self.settings_dialog.show()