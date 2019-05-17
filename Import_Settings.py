# -*- coding: utf-8 -*-
"""
Created on Mon May  6 15:02:27 2019

@author: seery
"""
class Import_Settings(QDialog):
    def __init__(self, parent):
        super().__init__()
        self.parent = parent
        TG = self.parent.parent.parent
        self.resize(750,532)
        self.setWindowTitle('File-Specific Import Settings')

        grid = QGridLayout()
        self.kwargTable = QTableWidget()
        self.kwargTable.verticalHeader().setDefaultSectionSize(self.kwargTable.verticalHeader().minimumSectionSize())
        self.kwargTable.verticalHeader().setSectionResizeMode(QHeaderView.Fixed)
        self.previewTable = QTableView()
        self.previewTable.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.previewTable.verticalHeader().setDefaultSectionSize(self.previewTable.verticalHeader().minimumSectionSize())
        self.previewTable.verticalHeader().setSectionResizeMode(QHeaderView.Fixed)
        grid.addWidget(self.kwargTable, 0, 0)
        grid.addWidget(self.previewTable, 1, 0)
        self.setLayout(grid)

        self.kwargTable.setColumnCount(4)
        files = [self.parent.foundFiles.item(i).text() for i in range(self.parent.foundFiles.count())]
        self.kwargTable.setRowCount(len(files))
        self.kwargTable.setHorizontalHeaderLabels(['File', 'Header Row', 'Index Column', 'Skip Rows'])
        for i, file in enumerate(files):
            kwargs = TG.path_kwargs[self.parent.path_dict[file]]
            self.kwargTable.setItem(i, 0, QTableWidgetItem(file))
            self.kwargTable.item(i,0).setFlags(Qt.ItemIsSelectable)
            self.kwargTable.setItem(i, 1, QTableWidgetItem(str(kwargs['header'])))
            self.kwargTable.setItem(i, 2, QTableWidgetItem(str(kwargs['index_col'])))
            self.kwargTable.setItem(i, 3, QTableWidgetItem(str(kwargs['skiprows'])))
        self.kwargTable.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        self.kwargTable.horizontalHeader().setSectionResizeMode(1, QHeaderView.Fixed)
        self.kwargTable.horizontalHeader().setSectionResizeMode(2, QHeaderView.Fixed)
        self.kwargTable.horizontalHeader().setSectionResizeMode(3, QHeaderView.Fixed)
        self.kwargTable.cellChanged.connect(self.update_parse_kwargs)
        self.kwargTable.itemSelectionChanged.connect(self.preview_df)

    def update_parse_kwargs(self, row, column):
        DM = self.parent.parent
        TG = DM.parent
        pick_kwargs = {1:'header', 2:'index_col', 3:'skiprows'}
        kwarg = pick_kwargs[column]
        file = self.kwargTable.item(row, 0).text()
        path = self.parent.path_dict[file]
        text = self.kwargTable.item(row, column).text()

        ### input permissions
        if kwarg == 'skiprows':
            value = []
            for i in text:
                if text == 'None':
                    value = text
                else:
                    if i.isdigit() and i not in value:  # admit only unique digits
                        if int(i) != 0: value.append(int(i))  # silently disallow zero
                    elif i in ', []':  # ignore commas, spaces, and brackets
                        continue
                    else:
                        DM.feedback('Only list of unique nonzero integers or \"None\" allowed.')
                        self.kwargTable.blockSignals(True)
                        self.kwargTable.setItem(row, column, QTableWidgetItem(str(TG.path_kwargs[path][kwarg])))
                        self.kwargTable.blockSignals(False)
                        return
            self.kwargTable.blockSignals(True)
            self.kwargTable.setItem(row, column, QTableWidgetItem(str(value)))
            self.kwargTable.blockSignals(False)
        else:
            if text.isdigit():
                value = int(text)
            elif text.lower() == 'auto':
                value = 'Auto'
            else:
                DM.feedback('Only integers or \"Auto\" allowed.')
                self.kwargTable.blockSignals(True)
                self.kwargTable.setItem(row, column, QTableWidgetItem(str(TG.path_kwargs[path][kwarg])))
                self.kwargTable.blockSignals(False)
                return
        self.kwargTable.blockSignals(True)
        self.kwargTable.setItem(row, column, QTableWidgetItem(str(value)))
        self.kwargTable.blockSignals(False)
        TG.path_kwargs[path][kwarg] = value
        self.preview_df()


    def preview_df(self):
        TG = self.parent.parent.parent
        selection = self.kwargTable.selectedIndexes()
        if selection:
            rows = sorted(index.row() for index in selection)
            if all(x==rows[0] for x in rows):  # can only preview one row at a time.

                # Populate preview table with selected 10x10 df preview
                row = selection[0].row()
                file = self.kwargTable.item(row, 0).text()
                if file.endswith('xls') or file.endswith('xlsx'):
                    read_func = pd.read_excel
                elif file.endswith('csv') or file.endswith('zip'):
                    read_func = pd.read_csv
                path = self.parent.path_dict[file]
                df, r, c = self.parent.parse_df_origin(path, read_func)
                df.columns = [str(i) for i in range(len(df.columns))]
                self.model = PandasModel(df)
                self.proxy = QSortFilterProxyModel()
                self.proxy.setSourceModel(self.model)
                self.previewTable.setModel(self.proxy)

                # Highlight selected rows/columns according to parse_kwargs
                header = TG.path_kwargs[path]['header']
                index_col = TG.path_kwargs[path]['index_col']
                skiprows = TG.path_kwargs[path]['skiprows']

                if index_col == 'Auto': index_col = c
                if header == 'Auto': header = r

                if index_col is not None:
                    for r in range(len(df.index)):
                        self.model.setData(self.model.index(r,int(index_col)), QBrush(QColor.fromRgb(255, 170, 0)), Qt.BackgroundRole)
                if header is not None:
                    for c in range(len(df.columns)):
                        self.model.setData(self.model.index(int(header),c), QBrush(QColor.fromRgb(0, 170, 255)), Qt.BackgroundRole)
                if skiprows is not None:
                    for r in skiprows:
                        for c in range(len(df.columns)):
                            self.model.setData(self.model.index(r,c), QBrush(Qt.darkGray), Qt.BackgroundRole)
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
