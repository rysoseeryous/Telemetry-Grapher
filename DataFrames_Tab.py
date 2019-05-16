# -*- coding: utf-8 -*-
"""
Created on Wed May  8 16:08:59 2019

@author: seery
"""
class DataFrames_Tab(QWidget):
    def __init__(self, parent):
        super().__init__()
        self.parent = parent
        self.grid = QGridLayout()

        self.selectGroup = QComboBox()
        self.selectGroup.addItems(self.parent.groups.keys())
        self.selectGroup.currentIndexChanged.connect(self.display_dataframe)
        self.export = QPushButton('Export DataFrames')
        self.export.clicked.connect(self.export_data)
        self.dfTable = QTableView()
        self.dfTable.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.dfTable.verticalHeader().setDefaultSectionSize(self.dfTable.verticalHeader().minimumSectionSize())
        self.dfTable.verticalHeader().setSectionResizeMode(QHeaderView.Fixed)

        widgets = [
                self.selectGroup,
                self.export,
                self.dfTable,
                ]

        positions = [
                (0,0,1,1),
                (1,0,1,1),
                (0,1,3,1),
                ]

        for w, p in zip(widgets, positions):
            self.grid.addWidget(w, *p)
        self.setLayout(self.grid)

        if self.selectGroup.currentText():
            self.display_dataframe()

    def display_dataframe(self):
        DM = self.parent
        TG = DM.parent
        selected = self.selectGroup.currentText()
        if selected:
            group = DM.groups[selected]
            df = group.data

            # Prepare table to display only headers kept in Configure tab (first 20 lines)
            shown = 20
            kept_df = df.head(shown).loc[:,[header for header in group.series if group.series[header].keep]]
            kept_df.index = kept_df.index.astype('str')
            if len(df.index) > shown:
                ellipses = pd.DataFrame(['...']*len(kept_df.columns),
                                        index=kept_df.columns,
                                        columns=['...']).T
                kept_df = kept_df.append(ellipses)

            # Use Aliases, Type, Unit, as column headers
            kept_df_headers = []
            for header in kept_df.columns:
                alias = group.series[header].alias
                unit = group.series[header].unit
                unit_type = TG.get_unit_type(unit)
                if not alias: alias = header
                if unit:
                    kept_df_headers.append('{}\n{} [{}]'.format(alias, unit_type, unit))
                else:
                    kept_df_headers.append('{}\n(no units)'.format(alias))
            kept_df.columns = kept_df_headers

            # Display kept_df in table
            self.model = PandasModel(kept_df)
            self.proxy = QSortFilterProxyModel()
            self.proxy.setSourceModel(self.model)
            self.dfTable.setModel(self.proxy)
            for i in range(self.model.columnCount()):
                self.dfTable.horizontalHeader().setSectionResizeMode(i, QHeaderView.ResizeToContents)

        else:
            if hasattr(self, 'proxy'): self.proxy.deleteLater()

    def export_data(self):
        """Generate an Excel sheet with kept dataframes, one per sheet/tab"""
        pass
