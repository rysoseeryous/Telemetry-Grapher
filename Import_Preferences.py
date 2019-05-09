# -*- coding: utf-8 -*-
"""
Created on Mon May  6 15:02:27 2019

@author: seery
"""
from PyQt5.QtWidgets import *

class Import_Preferences(QDialog):
    def __init__(self, parent):
        super().__init__()
        self.parent = parent