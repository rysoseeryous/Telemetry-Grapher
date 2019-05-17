# -*- coding: utf-8 -*-
"""
Created on Wed May  8 11:26:02 2019

@author: seery
"""
class Configure_Tab(QWidget):
    def __init__(self, parent):
        super().__init__()
        self.parent = parent
        self.grid = QGridLayout()


        self.selectGroup = QComboBox()
        self.selectGroup.addItems(self.parent.groups.keys())
        self.selectGroup.currentIndexChanged.connect(self.display_header_info)
        self.grid.addWidget(self.selectGroup,0,0)

        self.settings = QPushButton('Unit Settings')
        self.settings.clicked.connect(self.open_settings)
        self.grid.addWidget(self.settings,1,0)

        self.hideRows = QCheckBox('Hide Unused Headers')
        self.hideRows.setChecked(True)
        self.hideRows.stateChanged.connect(self.display_header_info)
        self.grid.addWidget(self.hideRows,2,0)

        self.start = QLabel()
        self.grid.addWidget(self.start,3,0)

        self.end = QLabel()
        self.grid.addWidget(self.end,4,0)

        self.total_span = QLabel()
        self.grid.addWidget(self.total_span,5,0)

        self.sampling_rate = QLabel()
        self.grid.addWidget(self.sampling_rate,6,0)

        self.headerTable = QTableWidget()
        self.headerTable.setColumnCount(6)
        self.headerTable.setHorizontalHeaderLabels(['Keep','Original Header','Alias','Unit Type','Unit','Scale'])
        self.headerTable.horizontalHeader().setSectionResizeMode(0,QHeaderView.ResizeToContents)
        self.headerTable.horizontalHeader().setSectionResizeMode(1,QHeaderView.Stretch)
        self.headerTable.horizontalHeader().setSectionResizeMode(2,QHeaderView.Stretch)
        self.headerTable.horizontalHeader().setSectionResizeMode(3,QHeaderView.Fixed)
        self.headerTable.horizontalHeader().setSectionResizeMode(4,QHeaderView.Fixed)
        self.headerTable.horizontalHeader().setSectionResizeMode(5,QHeaderView.ResizeToContents)
        self.headerTable.verticalHeader().setSectionResizeMode(QHeaderView.Fixed)
        self.grid.addWidget(self.headerTable,0,1,8,1)

        row_weights = [1, 1, 1, 1, 1, 1, 1, 100]
        for i,rw in enumerate(row_weights):
            self.grid.setRowStretch(i,rw)
        col_weights = [1, 100]
        for i,cw in enumerate(col_weights):
            self.grid.setColumnStretch(i,cw)
        self.setLayout(self.grid)

        if self.selectGroup.currentText():
            self.display_header_info()
            self.parent.modified = False

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
        return start, end, totalspan, timeinterval

    def display_header_info(self):
        try:
            self.headerTable.cellChanged.disconnect(self.update_alias_scale)
        except TypeError:
            pass
        TG = self.parent.parent
        DM = self.parent
        selected = self.selectGroup.currentText()
        if selected:
            group = DM.groups[selected]
            df = group.data
            start, end, total_span, sampling_rate = self.df_span_info(df)
            self.start.setText('Data Start:\n    {}'.format(start.strftime('%Y-%m-%d  %H:%M:%S')))
            self.end.setText('Data End:\n    {}'.format(end.strftime('%Y-%m-%d  %H:%M:%S')))
            self.total_span.setText('Total Span:\n    {} days\n    {} hours\n    {} minutes'.format(*total_span))
            self.sampling_rate.setText('Sampling Rate:\n    {}s'.format(sampling_rate))

            if self.hideRows.isChecked():
                nKeep = 0
                for header in group.series:
                    if group.series[header].keep: nKeep += 1
            else:
                nKeep = len(group.series)
            self.headerTable.setRowCount(nKeep)

            i = 0
            for header in group.series:
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
#                self.headerTable.item(i, 1).setFlags(Qt.ItemIsSelectable)

                self.headerTable.setItem(i, 2, QTableWidgetItem(alias))

                type_combo = QComboBox()
                type_combo.addItem(None)
                type_combo.addItems(list(TG.unit_dict.keys()))
                type_combo.setCurrentText(unit_type)
                type_combo.setProperty("row", i)
                type_combo.currentIndexChanged.connect(self.update_unit_combo)
                self.headerTable.setCellWidget(i, 3, type_combo)

                unit_combo = QComboBox()
                if unit_type is not None:
                    unit_combo.addItems(list(TG.unit_dict[unit_type]))
                unit_combo.setCurrentText(unit)
                unit_combo.setProperty("row", i)
                unit_combo.currentIndexChanged.connect(self.update_series_unit)
                self.headerTable.setCellWidget(i, 4, unit_combo)

                self.headerTable.setItem(i, 5, QTableWidgetItem(str(group.series[header].scale)))
                i += 1
        else:
            self.headerTable.clear()
            self.headerTable.setRowCount(0)
            self.headerTable.setColumnCount(0)
        self.headerTable.cellChanged.connect(self.update_alias_scale)

    def update_alias_scale(self, row, column):
        """Updates the alias and scaling factor of series when one of those two fields is edited"""
        DM = self.parent
        group = DM.groups[self.selectGroup.currentText()]
        header = self.headerTable.item(row, 1).text()
        if column == 2:
            alias = self.headerTable.item(row, 2).text().strip()  # remove any trailing/leading whitespace
            def remove_key_by_value(dictionary, value):
                for key in dictionary:
                    if dictionary[key] == value:
                        del dictionary[key]
                        break
            if alias:
                if alias in group.alias_dict:
                    DM.feedback('Alias \"{}\" is already in use. Please choose a different alias.'.format(alias))
                    self.headerTable.blockSignals(True)
                    self.headerTable.setItem(row, 2, QTableWidgetItem(group.series[header].alias))
                    self.headerTable.blockSignals(False)
                    return
                if alias in group.data.columns:
                    DM.feedback('Alias \"{}\" is the name of an original header. Please choose a different alias.'.format(alias))
                    self.headerTable.blockSignals(True)
                    self.headerTable.setItem(row, 2, QTableWidgetItem(group.series[header].alias))
                    self.headerTable.blockSignals(False)
                    return
                group.series[header].alias = alias
                remove_key_by_value(group.alias_dict, header)
                group.alias_dict[alias] = header
            else:
                group.series[header].alias = ''
                remove_key_by_value(group.alias_dict, header)
            DM.modified = True
        elif column == 5:
            scale = self.headerTable.item(row, 5).text()
            try:
                scale = float(scale)
                if scale == 0: raise ValueError
                group.series[header].scale = scale
                DM.modified = True
            except ValueError:
                DM.feedback('\"{}\" is not a valid scaling factor. Only nonzero real numbers permitted.'.format(scale))
            self.headerTable.blockSignals(True)  # prevents infinite recursion when setItem would call this function again
            self.headerTable.setItem(row, 5, QTableWidgetItem(str(group.series[header].scale)))
            self.headerTable.blockSignals(False)

    def update_unit_combo(self):
        TG = self.parent.parent
        type_combo = QObject.sender(self)
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
        group = DM.groups[self.selectGroup.currentText()]
        unit_combo = QObject.sender(self)
        row = unit_combo.property("row")
        unit = unit_combo.currentText()
        header = self.headerTable.item(row, 1).text()
        group.series[header].unit = unit
        DM.modified = True

    def update_keep(self):
        DM = self.parent
        group = DM.groups[self.selectGroup.currentText()]
        keep_check = QObject.sender(self)
        row = keep_check.property("row")
        header = self.headerTable.item(row, 1).text()
        group.series[header].keep = keep_check.isChecked()
        self.display_header_info()
        DM.modified = True

    def open_settings(self):
        self.settings_dialog = Unit_Settings(self)
        self.settings_dialog.setModal(True)
        self.settings_dialog.show()
