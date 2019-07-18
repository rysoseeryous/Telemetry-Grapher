# -*- coding: utf-8 -*-
"""import_settings.py - Contains ImportSettings class definition."""

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

import io
import csv
import copy
import pandas as pd

from PyQt5.QtWidgets import (QApplication, QDialog,
                             QVBoxLayout,
                             QDialogButtonBox, QSplitter,
                             QPushButton, QLabel,
                             QAbstractItemView, QHeaderView,
                             QTableView, QTableWidget, QTableWidgetItem)
from PyQt5.QtGui import QKeySequence, QIcon, QBrush, QColor
from PyQt5.QtCore import Qt, QSortFilterProxyModel

from ..internal.pandas_model import PandasModel

class ImportSettings(QDialog):

    def __init__(self, parent, group_files):
        super().__init__()
        self.parent = parent
        self.setWindowTitle('Review Import Settings')
        self.setWindowIcon(QIcon('rc/satellite.png'))
        gt = self.parent
        dm = gt.parent
        ui = dm.parent
        self.resize(1000,500)
        self.group_files = group_files
        vbox = QVBoxLayout()
        splitter = QSplitter(Qt.Vertical)

        self.kwargTable = QTableWidget()
        w = self.kwargTable
        v_header = w.verticalHeader()
        v_header.setDefaultSectionSize(v_header.minimumSectionSize())
        v_header.setSectionResizeMode(QHeaderView.Fixed)
        w.setRowCount(len(self.group_files))
        w.setColumnCount(5)
        w.setHorizontalHeaderLabels(['File',
                                     'Datetime Format',
                                     'Header Row',
                                     'Index Column',
                                     'Skip Rows'])
        h_header = w.horizontalHeader()
        h_header.setSectionResizeMode(0, QHeaderView.Stretch)
        h_header.setSectionResizeMode(1, QHeaderView.Fixed)
        h_header.setSectionResizeMode(2, QHeaderView.Fixed)
        h_header.setSectionResizeMode(3, QHeaderView.Fixed)
        h_header.setSectionResizeMode(4, QHeaderView.Fixed)
        w.itemSelectionChanged.connect(self.preview_df)
        w.cellChanged.connect(self.update_path_kwargs)
        splitter.addWidget(w)

        self.previewTable = QTableView()
        self.proxy = QSortFilterProxyModel()
        self.model = PandasModel(pd.DataFrame())
        self.proxy.setSourceModel(self.model)
        self.previewTable.setModel(self.proxy)
        self.previewTable.setEditTriggers(QAbstractItemView.NoEditTriggers)
        v_header = self.previewTable.verticalHeader()
        v_header.setDefaultSectionSize(v_header.minimumSectionSize())
        v_header.hide()
        splitter.addWidget(self.previewTable)

        self.buttonBox = QDialogButtonBox()
        self.autoDetect = QPushButton('Auto-Detect')
        self.autoDetect.clicked.connect(self.auto_detect)
        self.buttonBox.addButton(self.autoDetect, QDialogButtonBox.ResetRole)
        self.buttonBox.setStandardButtons(QDialogButtonBox.Reset |
                                          QDialogButtonBox.Ok |
                                          QDialogButtonBox.Cancel)
        self.buttonBox.accepted.connect(self.accept)
        self.buttonBox.accepted.connect(self.apply_kwargs)
#        self.buttonBox.button(QDialogButtonBox.Ok).setAutoDefault(True)
        self.buttonBox.rejected.connect(self.reject)
        resetButton = self.buttonBox.button(QDialogButtonBox.Reset)
        resetButton.clicked.connect(self.reset)
        self.feedback = QLabel()
        layout = self.buttonBox.layout()
        layout.insertWidget(2, self.feedback)
        self.buttonBox.setLayout(layout)

        vbox.addWidget(splitter)
        vbox.addWidget(self.buttonBox)
        self.setLayout(vbox)

        self.original_kwargs = copy.deepcopy(ui.path_kwargs)
        self.current_kwargs = copy.deepcopy(self.original_kwargs)
        for i, file in enumerate(self.group_files):
            kwargs = self.current_kwargs[gt.path_dict[file]]
            self.kwargTable.setItem(i, 0, QTableWidgetItem(file))
            self.kwargTable.item(i, 0).setFlags(Qt.ItemIsSelectable)
            self.update_row_kwargs(i, kwargs)
        self.kwargTable.setCurrentCell(0, 1)

        if self.parent.parent.debug:
            self.accept()

    def update_row_kwargs(self, row, kwargs):
        w = self.kwargTable
        w.setItem(row, 1, QTableWidgetItem(str(kwargs['format'])))
        w.setItem(row, 2, QTableWidgetItem(str(kwargs['header'])))
        w.setItem(row, 3, QTableWidgetItem(str(kwargs['index_col'])))
        w.setItem(row, 4, QTableWidgetItem(str(kwargs['skiprows'])))

    def auto_detect(self):
        gt = self.parent
        selection = self.kwargTable.selectedIndexes()
        rows = set(sorted(index.row() for index in selection))
        for row in rows:
            file = self.kwargTable.item(row, 0).text()
            path = gt.path_dict[file]
            dtf, r, c, skiprows = gt.interpret_data(path)
            kwargs = {'format':dtf,
                      'header':r,
                      'index_col':c,
                      'skiprows':skiprows}
            self.update_row_kwargs(row, kwargs)

    def reset(self):
        gt = self.parent
        for i, file in enumerate(self.group_files):
            kwargs = self.original_kwargs[gt.path_dict[file]]
            self.kwargTable.setItem(i, 0, QTableWidgetItem(file))
            self.kwargTable.item(i, 0).setFlags(Qt.ItemIsSelectable)
            self.update_row_kwargs(i, kwargs)

    def update_path_kwargs(self, row, col):
        gt = self.parent
        pick_kwargs = {1:'format', 2:'header', 3:'index_col', 4:'skiprows'}
        if col not in pick_kwargs: return
        kwarg = pick_kwargs[col]
        file = self.kwargTable.item(row, 0).text()
        path = gt.path_dict[file]
        text = self.kwargTable.item(row, col).text().strip()

        ### input permissions
        # NO INPUT CONTROL ON FORMAT FIELD, SO YOU BETTER KNOW WHAT YOU'RE DOIN
        self.kwargTable.blockSignals(True)
        if kwarg == 'format':
            value = text
        elif kwarg == 'header':
            if not text or text.lower() == 'none':
                value = None
            else:
                try:
                    value = int(text)
                except ValueError:
                    self.feedback.setText('Header row must be an integer'
                                          'less than 9 or left blank.')
                    self.kwargTable.setItem(row, col, QTableWidgetItem(
                            str(self.current_kwargs[path][kwarg])))
                    self.kwargTable.blockSignals(False)
        elif kwarg == 'index_col':
            try:
                value = int(text)
            except ValueError:
                self.feedback.setText('Index column must be an integer.')
                self.kwargTable.setItem(row, col, QTableWidgetItem(
                        str(self.current_kwargs[path][kwarg])))
                self.kwargTable.blockSignals(False)
                return
        elif kwarg == 'skiprows':
            if text.lower() == 'none':
                value = []
            else:
                value = []
                for i in text:
                    if i.isdigit() and int(i) not in value:
                        value.append(int(i))
                    elif i in ', []':  # ignore commas, spaces, and brackets
                        continue
                    else:
                        self.feedback.setText('Only list of integers from 0-9'
                                              'or "None" allowed.')
                        self.kwargTable.setItem(row, col, QTableWidgetItem(
                                str(self.current_kwargs[path][kwarg])))
                        self.kwargTable.blockSignals(False)
                        return
                value = sorted(value)
            if not value: value = None

        self.feedback.setText('')
        self.kwargTable.setItem(row, col, QTableWidgetItem(str(value)))
        self.kwargTable.blockSignals(False)
        self.current_kwargs[path][kwarg] = value
        self.preview_df()

    def preview_df(self):
        gt = self.parent
        selection = self.kwargTable.selectedIndexes()
        if selection:
            rows = sorted(index.row() for index in selection)
            # can only preview one row at a time.
            if all(x==rows[0] for x in rows):
                # Populate preview table with preview of selected
                row = selection[0].row()
                file = self.kwargTable.item(row, 0).text()
                path = gt.path_dict[file]
                shown_df = gt.df_preview[path]
                self.model = PandasModel(shown_df)
                self.proxy.setSourceModel(self.model)
                h_header = self.previewTable.horizontalHeader()
                h_header.setSectionResizeMode(0, QHeaderView.ResizeToContents)

                # Highlight selected rows/columns according to parse_kwargs
                header = self.current_kwargs[path]['header']
                index_col = self.current_kwargs[path]['index_col']
                skiprows = self.current_kwargs[path]['skiprows']

#                if skiprows == 'None': skiprows = None

                if index_col is not None:
                    for r in range(len(shown_df.index)):
                        self.model.setData(self.model.index(r,int(index_col)),
                                           QBrush(QColor.fromRgb(255, 170, 0)),
                                           Qt.BackgroundRole)
                if skiprows is not None:
                    for r in skiprows:
                        for c in range(len(shown_df.columns)):
                            self.model.setData(self.model.index(r,c),
                                               QBrush(Qt.darkGray),
                                               Qt.BackgroundRole)
                if header is not None:
                    for r in range(int(header)):
                        for c in range(len(shown_df.columns)):
                            self.model.setData(self.model.index(r,c),
                                               QBrush(Qt.darkGray),
                                               Qt.BackgroundRole)
                    for c in range(len(shown_df.columns)):
                        self.model.setData(self.model.index(int(header),c),
                                           QBrush(QColor.fromRgb(0, 170, 255)),
                                           Qt.BackgroundRole)
            else:
                self.model = PandasModel(pd.DataFrame())
                self.proxy.setSourceModel(self.model)
#                if hasattr(self, 'proxy'): self.proxy.deleteLater()
        else:
            self.model = PandasModel(pd.DataFrame())
            self.proxy.setSourceModel(self.model)
#            if hasattr(self, 'proxy'): self.proxy.deleteLater()

    def keyPressEvent(self, event):
        """Enables single row copy to multirow paste.
        Column dimensions must be the same, using Ctrl+C/V."""
        if event.matches(QKeySequence.Copy):
            selection = self.kwargTable.selectedIndexes()
            if selection:
                rows = sorted(index.row() for index in selection)
                # can only copy one row at a time.
                if all(x==rows[0] for x in rows):
                    columns = sorted(index.column() for index in selection)
                    selection_col_span = columns[-1] - columns[0] + 1
                    table = [[''] * selection_col_span]
                    for index in selection:
                        column = index.column() - columns[0]
                        table[0][column] = index.data()
                    stream = io.StringIO()
                    csv.writer(stream).writerows(table)
                    QApplication.clipboard().setText(stream.getvalue())

        if event.matches(QKeySequence.Paste):
            selection = self.kwargTable.selectedIndexes()
            if selection:
                model = self.kwargTable.model()
                buffer = QApplication.clipboard().text()
                rows = sorted(index.row() for index in selection)
                columns = sorted(index.column() for index in selection)
                selection_col_span = columns[-1] - columns[0] + 1
                reader = csv.reader(io.StringIO(buffer), delimiter='\t')
                arr = [row[0].split(',') for row in reader]
                arr = arr[0]
                if selection_col_span == len(arr):
                    for index in selection:
                        column = index.column() - columns[0]
                        model.setData(model.index(index.row(), index.column()),
                                      arr[column])

        # Close dialog from escape key.
        if event.key() == Qt.Key_Escape:
            self.close()

    def apply_kwargs(self):
        gt = self.parent
        dm = gt.parent
        ui = dm.parent
        # read current kwargs into ui.path_kwargs
        for file in self.group_files:
            path = gt.path_dict[file]
            k = self.current_kwargs[path]
            if k['skiprows']:
                k['skiprows'] = [i for i in k['skiprows'] if i > k['header']]
            for kwarg in ('format', 'header', 'index_col', 'skiprows'):
                ui.path_kwargs[path][kwarg] = self.current_kwargs[path][kwarg]
