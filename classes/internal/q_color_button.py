# -*- coding: utf-8 -*-
"""
Created on Thu Jun 13 15:48:18 2019

@author: seery
"""
from PyQt5.QtWidgets import QPushButton

class QColorButton(QPushButton):
    """Associates unit type with color."""

    def __init__(self, parent, color, unit_type):
        super(QColorButton, self).__init__()
        self.setFixedSize(20,20)
        self.parent = parent
        self.color = color
        self.setStyleSheet("background-color:{};".format(color))
        self.unit_type = unit_type