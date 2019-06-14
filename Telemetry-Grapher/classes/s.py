# -*- coding: utf-8 -*-
"""
Created on Thu Jun 13 15:53:26 2019

@author: seery
"""

class Series():

    def __init__(self, alias='', unit=None, unit_type=None, scale=1.0, keep=True):
        self.alias = alias
        self.unit = unit
        self.unit_type = unit_type
        self.scale = scale
        self.keep = keep

    def summarize(self):
        return 'Alias: '+str(self.alias)+'  Unit: '+str(self.unit)+'  Scale: '+str(self.scale)+'  Keep: '+str(self.keep)