# -*- coding: utf-8 -*-
"""
Created on Wed May  8 16:08:59 2019

@author: seery
"""
from PyQt5.QtWidgets import *

class DataFrames_Tab(QWidget):
    def __init__(self, parent):
        super().__init__()
        self.parent = parent
        self.grid = QGridLayout()

        self.selectGroup = QComboBox()
        self.selectGroup.addItems(self.parent.groups.keys())
        self.selectGroup.currentIndexChanged.connect(self.display_dataframe)
        self.dfTable = QTableWidget()


        widgets = [
                self.selectGroup,
                self.dfTable,
                ]

        positions = [
                (0,0,1,1),
                (0,1,3,1),
                ]

        for w, p in zip(widgets, positions):
            self.grid.addWidget(w, *p)
        self.setLayout(self.grid)

        if self.selectGroup.currentText():
            self.display_dataframe()

    def display_dataframe(self):
        DM = self.parent
        group = self.selectGroup.currentText()
        # need to work in renaming here
#        df = DM.groups[group].data

#        series_units = self.parent.data_dict[self.selectGroup.currentText()]
#        self.headerTable.setRowCount(len(series_units))
#
#
#        self.dfTable.setColumnCount(5)
#        # turn this into DM.read_qtable?
#
#        print()





