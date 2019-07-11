# -*- coding: utf-8 -*-
"""
Created on Thu Jun 13 15:53:26 2019

@author: seery
"""

class Series():

    def __init__(self, parent, header, alias,
                 unit=None, unit_type=None, keep=True):  #scale=1.0,
        self.parent = parent
        self.header = header
        self.alias = alias
        self.unit_type = unit_type
        self.unit = unit
        self.scale = scale
        self.keep = keep

    def summarize(self):
        return ('Header: '+str(self.header),
                'Alias: '+str(self.alias),
                'Unit Type: '+str(self.unit_type),
                'Unit: '+str(self.unit),
                'Scale: '+str(self.scale),
                'Keep: '+str(self.keep))
