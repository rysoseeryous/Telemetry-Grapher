# -*- coding: utf-8 -*-
"""
Created on Wed May 15 11:30:32 2019

@author: seery
"""
class PandasModel(QStandardItemModel):
    def __init__(self, data, parent=None):
        QStandardItemModel.__init__(self, parent)
        self._data = data
        for row in data.values.tolist():
            data_row = [QStandardItem(str(x)) for x in row]
            self.appendRow(data_row)
        return

    def rowCount(self, parent=None):
        return len(self._data.values)

    def columnCount(self, parent=None):
        return self._data.columns.size

    def headerData(self, x, orientation, role):
        if orientation == Qt.Horizontal and role == Qt.DisplayRole:
            return self._data.columns[x]
        if orientation == Qt.Vertical and role == Qt.DisplayRole:
            return self._data.index[x]
        return None