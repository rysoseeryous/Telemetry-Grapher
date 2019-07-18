# -*- coding: utf-8 -*-
"""configure_tab.py - Contains ConfigureTab class definition."""

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

import os
import zipfile
import pandas as pd

from PyQt5.QtWidgets import (QWidget, QFileDialog, QSizePolicy,
                             QHBoxLayout, QVBoxLayout, QGroupBox,
                             QPushButton, QLabel, QCheckBox, QComboBox,
                             QAbstractItemView, QHeaderView,
                             QTableView, QTableWidget, QTableWidgetItem)
from PyQt5.QtCore import Qt, QObject, QSortFilterProxyModel

from .unit_settings import UnitSettings
from ..internal.pandas_model import PandasModel

class ConfigureTab(QWidget):

    def __init__(self, parent):
        super().__init__()
        self.parent = parent
        dm = self.parent
        ui = dm.parent
        vbox = QVBoxLayout()
        hbox = QHBoxLayout()

        self.select_group = QComboBox()
        self.select_group.addItems(ui.groups.keys())
        self.select_group.currentIndexChanged.connect(self.display_header_info)
        vbox.addWidget(self.select_group)

        self.export = QPushButton('Export DataFrame')
        self.export.clicked.connect(self.export_data)
        vbox.addWidget(self.export)

        self.settings = QPushButton('Unit Settings')
        self.settings.clicked.connect(self.open_settings)
        vbox.addWidget(self.settings)

        self.reparse = QPushButton('Reparse Headers')
        self.reparse.clicked.connect(self.reparse_units)
        vbox.addWidget(self.reparse)

        self.hide_unused = QCheckBox('Hide Unused Headers')
        self.hide_unused.setChecked(True)
        self.hide_unused.stateChanged.connect(self.display_header_info)
        vbox.addWidget(self.hide_unused)

        vbox.addStretch(1)
        summary_group = QGroupBox('DataFrame Summary')
        summary_group.setAlignment(Qt.AlignHCenter)
#        summary_group.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Maximum)
        self.summary = QLabel()
        self.summary.setAlignment(Qt.AlignTop)
        summary_layout = QVBoxLayout()
        summary_layout.addWidget(self.summary)
        summary_group.setLayout(summary_layout)
        vbox.addWidget(summary_group)
        hbox.addLayout(vbox)
        vbox = QVBoxLayout(spacing=0)

        self.header_table = QTableWidget()
        w = self.header_table
        w.setRowCount(6)
        h_header = w.horizontalHeader()
        h_header.sectionResized.connect(self.sync_col_width)
        h_header.setFixedHeight(23)
        w.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        w.setVerticalHeaderLabels(['Keep',
                                   'Scale',
                                   'Original Header',
                                   'Alias',
                                   'Unit Type',
                                   'Unit'])
        v_header = w.verticalHeader()
        v_header.setFixedWidth(146)
        v_header.setDefaultSectionSize(23)
        v_header.setSectionResizeMode(QHeaderView.Fixed)
        w.setFixedHeight(163)
        vbox.addWidget(w)

        self.df_table = QTableView()
        self.proxy = QSortFilterProxyModel()
        self.df_table.setModel(self.proxy)
        w = self.df_table
        w.setEditTriggers(QAbstractItemView.NoEditTriggers)
        w.horizontalHeader().hide()
        w.horizontalScrollBar().valueChanged.connect(self.sync_scroll)
        v_header = w.verticalHeader()
        v_header.setDefaultSectionSize(v_header.minimumSectionSize())
        v_header.setSectionResizeMode(QHeaderView.Fixed)
        v_header.setFixedWidth(146)
        vbox.addWidget(w)
        hbox.addLayout(vbox)
        self.setLayout(hbox)

        if self.select_group.currentText():
            self.display_header_info()
            self.parent.modified = False

    def reparse_units(self):
        """Reruns header parsing algorithm for selected columns."""
        dm = self.parent
        group_name = self.select_group.currentText()
        group = dm.groups[group_name]
        cols = [item.column() for item in self.header_table.selectedItems()]
        headers = [self.header_table.item(2, c).text() for c in set(cols)]
        dm.groups_tab.parse_series(group.series(headers))
        dm.configure_tab.header_table.blockSignals(True)
        dm.configure_tab.populate_header_table(group)
        dm.configure_tab.header_table.blockSignals(False)

    def export_data(self):
        """Generate an CSV file for selected group.
        Only kept columns and aliases with units in square brackets."""
        dm = self.parent
        ui = dm.parent

        group_name = self.select_group.currentText()
        if not group_name: return

        dlg = QFileDialog()
        dlg.setFileMode(QFileDialog.AnyFile)
        dlg.setViewMode(QFileDialog.Detail)
        dlg_out = dlg.getSaveFileName(self, 'Save DataFrame as CSV',
                                      ui.df_dir + '/' + group_name,
                                      'CSV File (*.csv);;ZIP File (*.zip)')
        if not dlg_out[0]: return
        dm.feedback('Exporting DataFrame to {}... '.format(dlg_out[0]))
        dm.message_log.repaint()

        ui.df_dir, local = os.path.split(dlg_out[0])
        filename, ext = os.path.splitext(local)

        group = dm.groups[group_name]
        aliases = {}
        for s in group.series(lambda s: s.keep):
            alias = dm.derive_alias(s)
            aliases[s.header] = ('{} [{}]'.format(alias, s.unit))
        df = group.data.loc[:, list(aliases.keys())]
        df.rename(columns=aliases, inplace=True)
        df.dropna(axis=0, how='all', inplace=True)

        try:
            if ext=='.csv':
                with open(dlg_out[0], 'w') as f:
                    df.to_csv(f, encoding='utf-8-sig')
            elif ext=='.zip':
                csvname = filename + '.csv'
                if csvname in os.listdir(ui.df_dir):
                    ok = ui.popup('"{}" already exists.\n'
                                  'This will overwrite the current file '
                                  'and add it to the zip file.\n'
                                  'Continue?'.format(csvname),
                                  title='Export DataFrame',
                                  mode='confirm')
                    if not ok:
                        dm.feedback('Cancelled', mode='append')
                        self.export_data()
                        return
                reset_dir = os.getcwd()
                os.chdir(ui.df_dir)
                with open(csvname, 'w') as f:
                    df.to_csv(f, encoding='utf-8-sig')
                    with zipfile.ZipFile(local, 'w') as zf:
                        zf.write(csvname, compress_type=zipfile.ZIP_DEFLATED)
                os.remove(csvname)
                os.chdir(reset_dir)

            dm.feedback('Done', mode='append')
        except PermissionError as e:
            dm.feedback('Failed', mode='append')
            dm.feedback('Permission denied. {}'.format(e))

    def sync_scroll(self, idx):
        self.header_table.horizontalScrollBar().setValue(idx)

    def sync_col_width(self, col, old_size, new_size):
        self.df_table.horizontalHeader().resizeSection(col, new_size)

    def days_hours_minutes(self, timedelta):
        return (timedelta.days,
                timedelta.seconds//3600,
                (timedelta.seconds//60)%60)

    def df_span_info(self, df):
        start = min(df.index)
        end = max(df.index)
        total_span = self.days_hours_minutes(end - start)
        time_interval = 0; i = 1
        while time_interval == 0:
            time_interval = (df.index[i]-df.index[i-1]).total_seconds()
            i += 1
        return df.shape, start, end, total_span, time_interval

    def populate_header_table(self, group):
        dm = self.parent
        ui = dm.parent
        if self.hide_unused.isChecked():
            f = lambda s: s.keep
        else:
            f = None
        for i, s in enumerate(group.series(f)):
            keep_check = QCheckBox()
            keep_check.setChecked(s.keep)
            keep_check.setProperty("col", i)
            keep_check.stateChanged.connect(self.update_keep)
            _widget = QWidget()
            _layout = QHBoxLayout(_widget)
            _layout.addWidget(keep_check)
            _layout.setAlignment(Qt.AlignCenter)
            _layout.setContentsMargins(0, 0, 0, 0)
            self.header_table.setCellWidget(0, i, _widget)

            self.header_table.setItem(1, i, QTableWidgetItem(str(s.scale)))

            item = QTableWidgetItem(s.header)
            item.setFlags(Qt.ItemIsSelectable)
            self.header_table.setItem(2, i, item)

            self.header_table.setItem(3, i, QTableWidgetItem(s.alias))

            type_combo = QComboBox()
            all_units = {**ui.unit_dict, **ui.user_units}
            if ui.default_type and ui.default_type not in all_units:
                type_combo.addItem(ui.default_type)
            type_combo.addItem('')
            type_combo.addItems(list(all_units.keys()))
            type_combo.setCurrentText(s.unit_type)
            type_combo.setProperty("col", i)
            type_combo.currentIndexChanged.connect(self.update_unit_combo)
            self.header_table.setCellWidget(4, i, type_combo)

            unit_combo = QComboBox()
            if s.unit_type:
                if s.unit_type in all_units:
                    unit_combo.addItems(list(all_units[s.unit_type]))
                else:
                    unit_combo.addItem(ui.default_unit)
            else:
                unit_combo.addItem(ui.default_unit)

            unit_combo.setCurrentText(s.unit)
            unit_combo.setProperty("col", i)
            unit_combo.currentIndexChanged.connect(self.update_series_unit)
            self.header_table.setCellWidget(5, i, unit_combo)

    def populate_df_table(self, group, df):
        shown_rows = 20
        headers = [s.header for s in group.series(lambda s: s.keep)]
        if len(df.index) > shown_rows:
            upper_df = df.head(shown_rows//2)
            lower_df = df.tail(shown_rows//2)
            if self.hide_unused.isChecked():
                upper_df = upper_df.loc[:, headers]
                lower_df = lower_df.loc[:, headers]
            ellipses = pd.DataFrame(['...']*len(upper_df.columns),
                                    index=upper_df.columns,
                                    columns=['...']).T
            shown_df = upper_df.append(ellipses).append(lower_df)
        else:
            if self.hide_unused.isChecked():
                shown_df = df.loc[:, headers]
            else:
                shown_df = df
        new_index = []
        for ts in shown_df.index:
            if hasattr(ts, 'strftime'):
                new_index.append(ts.strftime('%Y-%m-%d  %H:%M:%S'))
            else:
                new_index.append('...')
        shown_df.index = new_index

        self.model = PandasModel(shown_df)
        self.proxy.setSourceModel(self.model)
        self.header_table.setColumnCount(len(shown_df.columns))

    def summarize_data(self, df):
        shape, start, end, total_span, sampling_rate = self.df_span_info(df)
        shape_info = ('Shape Info:\n    {} rows\n    {} columns'
                      .format(*shape))
        data_start = ('Data Start:\n    {}'
                      .format(start.strftime('%Y-%m-%d  %H:%M:%S')))
        data_end = ('Data End:\n    {}'
                    .format(end.strftime('%Y-%m-%d  %H:%M:%S')))
        span_info = ('Total Span:\n    {} days\n    {} hours\n    {} minutes'
                     .format(*total_span))
        rate_info = ('Sampling Rate:\n    {} s'
                     .format(sampling_rate))
        summary = (shape_info + '\n' +
                   data_start + '\n' +
                   data_end + '\n' +
                   span_info + '\n' +
                   rate_info)
        self.summary.setText(summary)

    def display_header_info(self):
        try:
            self.header_table.cellChanged.disconnect(self.update_alias_scale)
        except TypeError:
            pass
        dm = self.parent
        group_name = self.select_group.currentText()
        if group_name:
            group = dm.groups[group_name]
            df = group.data
            self.summarize_data(df)
            self.populate_df_table(group, df)
            self.header_table.setRowCount(6)
            self.header_table.setVerticalHeaderLabels(['Keep',
                                                       'Scale',
                                                       'Original Header',
                                                       'Alias',
                                                       'Unit Type',
                                                       'Unit'])
            self.populate_header_table(group)
        else:
            self.summary.setText('')
            self.header_table.clear()
            self.header_table.setRowCount(0)
            self.header_table.setColumnCount(0)
            self.model = PandasModel(pd.DataFrame())
            self.proxy.setSourceModel(self.model)
        self.header_table.cellChanged.connect(self.update_alias_scale)

    def update_alias_scale(self, row, col):
        """Updates the alias and scaling factor of series."""
        dm = self.parent
        group = dm.groups[self.select_group.currentText()]
        header = self.header_table.item(2, col).text()
        s = group.series(header)
        if row == 3:
            # remove any trailing/leading whitespace
            alias = self.header_table.item(3, col).text().strip()

            def remove_key_by_value(dictionary, value):
                for key in dictionary:
                    if dictionary[key] == value:
                        del dictionary[key]
                        break

            if alias and alias != s.alias:
                accept = True
                if alias in group.alias_dict:
                    dm.feedback('Alias "{}" is already in use.'
                                'Please choose a different alias.'
                                .format(alias))
                    accept = False
                if alias in group.data.columns:
                    dm.feedback('Alias "{}" is the name of an original header.'
                                'Please choose a different alias.'
                                .format(alias))
                    accept = False
                if not accept:
                    self.header_table.blockSignals(True)
                    reset = s.alias
                    self.header_table.setItem(3, col, QTableWidgetItem(reset))
                    self.header_table.blockSignals(False)
                    return
                s.alias = alias
                remove_key_by_value(group.alias_dict, header)
                group.alias_dict[alias] = header
            else:
                s.alias = ''
                remove_key_by_value(group.alias_dict, header)
            dm.modified = True
        elif row == 1:
            scale = self.header_table.item(1, col).text()
            try:
                scale = float(scale)
                if scale == 0: raise ValueError
                s.scale = scale
                dm.modified = True
            except ValueError:
                dm.feedback('"{}" is not a valid scaling factor.'
                            'Only nonzero real numbers permitted.'
                            .format(scale))
            # prevents infinite recursion because of setItem
            self.header_table.blockSignals(True)
            self.header_table.setItem(1, col, QTableWidgetItem(str(s.scale)))
            self.header_table.blockSignals(False)

    def update_unit_combo(self):
        dm = self.parent
        ui = dm.parent
        group = dm.groups[self.select_group.currentText()]
        type_combo = QObject.sender(self)
        col = type_combo.property("col")
        unit_type = type_combo.currentText()
        header = self.header_table.item(2, col).text()
        s = group.series(header)
        s.unit_type = unit_type
        unit_combo = self.header_table.cellWidget(5, col)
        unit_combo.clear()
        if unit_type in ui.user_units:
            unit_combo.addItems(list(ui.user_units[unit_type]))
        elif unit_type in ui.unit_dict:
            unit_combo.addItems(list(ui.unit_dict[unit_type]))
        elif ui.default_unit:
            unit_combo.addItem(ui.default_unit)
        dm.modified = True

    def update_series_unit(self):
        dm = self.parent
        group = dm.groups[self.select_group.currentText()]
        unit_combo = QObject.sender(self)
        col = unit_combo.property("col")
        unit = unit_combo.currentText()
        header = self.header_table.item(2, col).text()
        s = group.series(header)
        s.unit = unit
        dm.modified = True

    def update_keep(self):
        dm = self.parent
        group = dm.groups[self.select_group.currentText()]
        keep_check = QObject.sender(self)
        selected = self.header_table.selectedItems()
        columns = [keep_check.property("col")]
        columns.extend([item.column() for item in selected])
        for c in set(columns):
            header = self.header_table.item(2, c).text()
            s = group.series(header)
            s.keep = keep_check.isChecked()
        self.display_header_info()
        dm.modified = True

    def open_settings(self):
        self.dlg = UnitSettings(self)
        self.dlg.setModal(True)
        self.dlg.show()
