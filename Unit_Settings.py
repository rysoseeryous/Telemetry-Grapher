# -*- coding: utf-8 -*-
"""
Created on Thu May  9 10:43:47 2019

@author: seery
"""
from PyQt5.QtWidgets import *

class Unit_Settings(QDialog):
    def __init__(self, parent):
        super().__init__()
        self.parent = parent
        TG = self.parent.parent.parent  # sheesh man

        self.set_defaults = {}
#        self.unit_types = [
#                'Position',
#                'Velocity',
#                'Acceleration',
#                'Angle',
#                'Temperature',
#                'Pressure',
#                'Heat',
#                'Voltage',
#                'Current',
#                'Resistance',
#                'Force',
#                'Torque',
#                'Power',
#                ]
        self.grid = QGridLayout()

        units = [u for u in TG.unit_dict.keys() if u is not None]
        for i,u in enumerate(units):
            self.set_defaults[i] = QComboBox()
            self.set_defaults[i].addItems(TG.unit_dict[u])
#            self.set_defaults[i].setCurrentText(TG.unit_defaults[u])
            self.grid.addWidget(QLabel(u), i, 0)
            self.grid.addWidget(self.set_defaults[i], i, 1)

        self.setLayout(self.grid)
