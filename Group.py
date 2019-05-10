# -*- coding: utf-8 -*-
"""
Created on Mon May  6 15:02:04 2019

@author: seery
"""

class Group():
    def __init__(self, df, source_files, source_paths):
        self.data = df  # maybe copy needed
        self.series = {key:Series() for key in self.data.columns}  # import as 1 to 1 header:alias
        self.alias_dict = {}
        self.source_files = source_files
        self.source_paths = source_paths
#EG: TG.groups[name].series['mySeries'].alias

class Series():
    def __init__(self, alias=None, unit=None, scale=1.0, keep=True):
        self.alias = alias
        self.unit = unit
        self.scale = scale
        self.keep = keep