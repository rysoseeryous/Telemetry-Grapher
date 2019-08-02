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

import re
import os
import zipfile
import pandas as pd

from PyQt5.QtWidgets import (QWidget, QFileDialog,
                             QHBoxLayout, QVBoxLayout, QGroupBox,
                             QPushButton, QLabel, QCheckBox, QComboBox,
                             QTableView, QAbstractItemView, QHeaderView,
                             QTableWidget)
from PyQt5.QtCore import Qt, QSortFilterProxyModel

from ..internal.pandas_model import PandasModel
from ..internal.series_header_stack import SeriesHeaderStack

class ConfigureTab(QWidget):

    def __init__(self, parent):
        super().__init__()
        self.parent = parent
        dm = self.parent
        self.stacks = []

        vbox = QVBoxLayout()
        hbox = QHBoxLayout()

        self.select_group = QComboBox()
        self.select_group.addItems(dm.all_groups.keys())
        self.select_group.currentTextChanged.connect(self.display_header_info)
        vbox.addWidget(self.select_group)

        self.export = QPushButton('Export DataFrame')
        self.export.clicked.connect(self.export_data)
        vbox.addWidget(self.export)

        self.reparse = QPushButton('Reparse Headers')
        self.reparse.clicked.connect(self.reparse_units)
        vbox.addWidget(self.reparse)

        self.hide_unused = QCheckBox('Hide Unused Series')
        self.hide_unused.setChecked(True)
        self.hide_unused.stateChanged.connect(self.display_header_info)
        vbox.addWidget(self.hide_unused)

        vbox.addStretch(1)
        summary_group = QGroupBox('Data Summary')
        summary_group.setAlignment(Qt.AlignHCenter)
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
        h_header = w.horizontalHeader()
        h_header.sectionResized.connect(self.sync_col_width)
        h_header.setFixedHeight(23)
        w.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        v_header = w.verticalHeader()
        v_header.setFixedWidth(150)
        v_header.setDefaultSectionSize(23)
        v_header.setSectionResizeMode(QHeaderView.Fixed)
        w.setFixedHeight(140)
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
        v_header.setFixedWidth(150)
        vbox.addWidget(w)
        hbox.addLayout(vbox)
        self.setLayout(hbox)

        if self.select_group.currentText():
            self.display_header_info()
            self.parent.modified = False

    def sync_scroll(self, idx):
        self.header_table.horizontalScrollBar().setValue(idx)

    def sync_col_width(self, col, old_size, new_size):
        self.df_table.horizontalHeader().resizeSection(col, new_size)

    def display_header_info(self):
        self.summarize_data()
        self.populate_df_table()
        self.populate_header_table()

    def populate_df_table(self):
        dm = self.parent
        group_name = self.select_group.currentText()
        if not group_name:
            self.model = PandasModel(pd.DataFrame())
            self.proxy.setSourceModel(self.model)
            return
        group = dm.all_groups[group_name]
        df = group.data
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

    def days_hours_minutes(self, timedelta):
        return (timedelta.days,
                timedelta.seconds//3600,
                (timedelta.seconds//60)%60)

    def summarize_data(self):
        dm = self.parent
        group_name = self.select_group.currentText()
        if not group_name:
            self.summary.setText('')
            return
        group = dm.all_groups[group_name]
        df = group.data
        start = min(df.index)
        end = max(df.index)
        total_span = self.days_hours_minutes(end - start)
        sampling_rate = 0; i = 1
        while sampling_rate == 0:
            sampling_rate = (df.index[i]-df.index[i-1]).total_seconds()
            i += 1
        shape_info = ('Shape Info:\n    {} rows\n    {} columns'
                      .format(*df.shape))
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

    def populate_header_table(self):
        dm = self.parent
        group_name = self.select_group.currentText()
        self.header_table.clear()
        if not group_name:
            self.header_table.setRowCount(0)
            self.header_table.setColumnCount(0)
            return
        group = dm.all_groups[group_name]
        self.header_table.setRowCount(5)
        n = len(self.model._data.columns)
        self.header_table.setColumnCount(n)
        self.header_table.setVerticalHeaderLabels(
                ['Keep', 'Original Header', 'Alias', 'Unit Type', 'Unit']
                )
        if self.hide_unused.isChecked():
            which = lambda s: s.keep
        else:
            which = None  # denotes all series
        self.stacks = []
        for i, s in enumerate(group.series(which)):
            stack = SeriesHeaderStack(self, i, s)
            self.stacks.append(stack)
            for w in [stack.keep_widget,
                      stack.header_item,
                      stack.alias_item,
                      stack.type_combo,
                      stack.unit_combo]:
                self.header_table.setCellWidget(w.row, i, w)

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

        group = dm.all_groups[group_name]
        aliases = {}
        for s in group.series(lambda s: s.keep):
            alias = s.alias
            if not alias:
                alias = re.sub('\[{}\]'.format(s.unit), '', s.header).strip()
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

    def reparse_units(self):
        """Reruns header parsing algorithm for selected columns."""
        dm = self.parent
        gt = dm.groups_tab
        selected = self.header_table.selectedIndexes()
        cols = set([index.column() for index in selected])
        series = [self.stacks[col].s for col in cols]
        report = gt.parse_series(series)
        self.header_table.blockSignals(True)
        self.populate_header_table()
        self.header_table.blockSignals(False)
        gt.report_parse_error_log(report)
