# -*- coding: utf-8 -*-
"""
Created on Thu Jun 27 09:43:28 2019

@author: seery
"""

class AxisManager():
    def __init__(self, parent, ax, unit_type=None, unit=None, scale=1.0, color='b'):
        super().__init__()
        self.parent = parent
        self.ax = ax
        self.unit_type = unit_type
        self.unit = unit
        self.scale = scale
        self.log = False
        self.color = color

    def reset_limits(self):
        pass