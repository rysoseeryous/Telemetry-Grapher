# -*- coding: utf-8 -*-
"""
Created on Thu Jun 13 15:51:06 2019

@author: seery
"""
import io
import csv
import copy

from PyQt5.QtWidgets import (QApplication, QDialog,
                             QVBoxLayout,
                             QDialogButtonBox, QSplitter,
                             QPushButton, QLabel,
                             QAbstractItemView, QHeaderView,
                             QTableView, QTableWidget, QTableWidgetItem)
from PyQt5.QtGui import QKeySequence, QIcon, QBrush, QColor
from PyQt5.QtCore import Qt, QSortFilterProxyModel

from .pm import Pandas_Model

class Import_Parameters(QDialog):

    def __init__(self, parent, group_files):
        super().__init__()
        self.parent = parent
        self.setWindowTitle('Review Import Parameters')
        self.setWindowIcon(QIcon('rc/satellite.png'))
        GT = self.parent
        DM = GT.parent
        AB = DM.parent
        self.resize(1000,500)
        self.group_files = group_files
        vbox = QVBoxLayout()
        splitter = QSplitter(Qt.Vertical)

        self.kwargTable = QTableWidget()
        self.kwargTable.verticalHeader().setDefaultSectionSize(self.kwargTable.verticalHeader().minimumSectionSize())
        self.kwargTable.verticalHeader().setSectionResizeMode(QHeaderView.Fixed)
        self.kwargTable.setRowCount(len(self.group_files))
        self.kwargTable.setColumnCount(5)
        self.kwargTable.setHorizontalHeaderLabels(['File', 'Datetime Format', 'Header Row', 'Index Column', 'Skip Rows'])
        self.kwargTable.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        self.kwargTable.horizontalHeader().setSectionResizeMode(1, QHeaderView.Fixed)
        self.kwargTable.horizontalHeader().setSectionResizeMode(2, QHeaderView.Fixed)
        self.kwargTable.horizontalHeader().setSectionResizeMode(3, QHeaderView.Fixed)
        self.kwargTable.horizontalHeader().setSectionResizeMode(4, QHeaderView.Fixed)
        self.kwargTable.itemSelectionChanged.connect(self.preview_df)
        self.kwargTable.cellChanged.connect(self.update_path_kwargs)
        splitter.addWidget(self.kwargTable)

        self.previewTable = QTableView()
        self.previewTable.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.previewTable.verticalHeader().setDefaultSectionSize(self.previewTable.verticalHeader().minimumSectionSize())
        self.previewTable.verticalHeader().hide()
        splitter.addWidget(self.previewTable)

        self.buttonBox = QDialogButtonBox()
        self.autoDetect = QPushButton('Auto-Detect')
        self.autoDetect.clicked.connect(self.auto_detect)
        self.buttonBox.addButton(self.autoDetect, QDialogButtonBox.ResetRole)
        self.buttonBox.setStandardButtons(QDialogButtonBox.Reset | QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        self.buttonBox.accepted.connect(self.accept)
        self.buttonBox.accepted.connect(self.apply_kwargs)
#        self.buttonBox.button(QDialogButtonBox.Ok).setAutoDefault(True)
        self.buttonBox.rejected.connect(self.reject)
        self.buttonBox.button(QDialogButtonBox.Reset).clicked.connect(self.reset)
        self.feedback = QLabel()
        layout = self.buttonBox.layout()
        layout.insertWidget(2, self.feedback)
        self.buttonBox.setLayout(layout)

        vbox.addWidget(splitter)
        vbox.addWidget(self.buttonBox)
        self.setLayout(vbox)

        self.original_kwargs = copy.deepcopy(AB.path_kwargs)
        self.current_kwargs = copy.deepcopy(self.original_kwargs)
        for i, file in enumerate(self.group_files):
            kwargs = self.current_kwargs[GT.path_dict[file]]
            self.kwargTable.setItem(i, 0, QTableWidgetItem(file))
            self.kwargTable.item(i, 0).setFlags(Qt.ItemIsSelectable)
            self.update_row_kwargs(i, kwargs)
        self.kwargTable.setCurrentCell(0, 1)

    def update_row_kwargs(self, row, kwargs):
        self.kwargTable.setItem(row, 1, QTableWidgetItem(str(kwargs['format'])))
        self.kwargTable.setItem(row, 2, QTableWidgetItem(str(kwargs['header'])))
        self.kwargTable.setItem(row, 3, QTableWidgetItem(str(kwargs['index_col'])))
        self.kwargTable.setItem(row, 4, QTableWidgetItem(str(kwargs['skiprows'])))

    def auto_detect(self):
        GT = self.parent
        selection = self.kwargTable.selectedIndexes()
        rows = set(sorted(index.row() for index in selection))
        for row in rows:
            file = self.kwargTable.item(row, 0).text()
            path = GT.path_dict[file]
            dtf, r, c, skiprows = GT.interpret_data(path)
            kwargs = {'format':dtf, 'header':r, 'index_col':c, 'skiprows':skiprows}
            self.update_row_kwargs(row, kwargs)

    def reset(self):
        GT = self.parent
        for i, file in enumerate(self.group_files):
            kwargs = self.original_kwargs[GT.path_dict[file]]
            self.kwargTable.setItem(i, 0, QTableWidgetItem(file))
            self.kwargTable.item(i, 0).setFlags(Qt.ItemIsSelectable)
            self.update_row_kwargs(i, kwargs)

    def update_path_kwargs(self, row, column):
        GT = self.parent
        pick_kwargs = {1:'format', 2:'header', 3:'index_col', 4:'skiprows'}
        if column not in pick_kwargs: return
        kwarg = pick_kwargs[column]
        file = self.kwargTable.item(row, 0).text()
        path = GT.path_dict[file]
        text = self.kwargTable.item(row, column).text().strip()

        ### input permissions
        # NO INPUT CONTROL ON FORMAT FIELD, SO YOU BETTER KNOW WHAT YOU'RE DOING
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
                    self.feedback.setText('Header row must be declared as an integer less than 9 or left undefined.')
                    self.kwargTable.setItem(row, column, QTableWidgetItem(str(self.current_kwargs[path][kwarg])))
                    self.kwargTable.blockSignals(False)
        elif kwarg == 'index_col':
            try:
                value = int(text)
            except ValueError:
                self.feedback.setText('Index column must be identified as an integer.')
                self.kwargTable.setItem(row, column, QTableWidgetItem(str(self.current_kwargs[path][kwarg])))
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
                        self.feedback.setText('Only list of integers from 0-9 or "None" allowed.')
                        self.kwargTable.setItem(row, column, QTableWidgetItem(str(self.current_kwargs[path][kwarg])))
                        self.kwargTable.blockSignals(False)
                        return
                value = sorted(value)
            if not value: value = None

        self.feedback.setText('')
        self.kwargTable.setItem(row, column, QTableWidgetItem(str(value)))
        self.kwargTable.blockSignals(False)
        self.current_kwargs[path][kwarg] = value
        self.preview_df()

    def preview_df(self):
        GT = self.parent
        selection = self.kwargTable.selectedIndexes()
        if selection:
            rows = sorted(index.row() for index in selection)
            if all(x==rows[0] for x in rows):  # can only preview one row at a time.
                # Populate preview table with preview of selected
                row = selection[0].row()
                file = self.kwargTable.item(row, 0).text()
                path = GT.path_dict[file]
                shown_df = GT.df_preview[path]
                self.model = Pandas_Model(shown_df)
                self.proxy = QSortFilterProxyModel()
                self.proxy.setSourceModel(self.model)
                self.previewTable.setModel(self.proxy)
                self.previewTable.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeToContents)

                # Highlight selected rows/columns according to parse_kwargs
                header = self.current_kwargs[path]['header']
                index_col = self.current_kwargs[path]['index_col']
                skiprows = self.current_kwargs[path]['skiprows']

#                if skiprows == 'None': skiprows = None

                if index_col is not None:
                    for r in range(len(shown_df.index)):
                        self.model.setData(self.model.index(r,int(index_col)), QBrush(QColor.fromRgb(255, 170, 0)), Qt.BackgroundRole)
                if skiprows is not None:
                    for r in skiprows:
                        for c in range(len(shown_df.columns)):
                            self.model.setData(self.model.index(r,c), QBrush(Qt.darkGray), Qt.BackgroundRole)
                if header is not None:
                    for r in range(int(header)):
                        for c in range(len(shown_df.columns)):
                            self.model.setData(self.model.index(r,c), QBrush(Qt.darkGray), Qt.BackgroundRole)
                    for c in range(len(shown_df.columns)):
                        self.model.setData(self.model.index(int(header),c), QBrush(QColor.fromRgb(0, 170, 255)), Qt.BackgroundRole)
            else:
                if hasattr(self, 'proxy'): self.proxy.deleteLater()
        else:
            if hasattr(self, 'proxy'): self.proxy.deleteLater()

    def keyPressEvent(self, event):
        """Enables single row copy to multirow paste, as long as column dimensions are the same, using Ctrl+C/V."""
        if event.matches(QKeySequence.Copy):
            selection = self.kwargTable.selectedIndexes()
            if selection:
                rows = sorted(index.row() for index in selection)
                if all(x==rows[0] for x in rows):  # can only copy one row at a time.
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
                        model.setData(model.index(index.row(), index.column()), arr[column])

        # Close dialog from escape key.
        if event.key() == Qt.Key_Escape:
            self.close()

    def apply_kwargs(self):
        GT = self.parent
        DM = GT.parent
        AB = DM.parent
        # read current kwargs into AB.path_kwargs
        for file in self.group_files:
            path = GT.path_dict[file]
            if self.current_kwargs[path]['skiprows']:
                self.current_kwargs[path]['skiprows'] = [i for i in self.current_kwargs[path]['skiprows'] if i > self.current_kwargs[path]['header']]
            for kwarg in ('format', 'header', 'index_col', 'skiprows'):
                AB.path_kwargs[path][kwarg] = self.current_kwargs[path][kwarg]