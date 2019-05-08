# -*- coding: utf-8 -*-
"""
Created on Mon May  6 15:02:04 2019

@author: seery
"""

class Group():
    def __init__(self, name, df, source_files, source_paths):
        self.name = name
        self.data = df
        self.source_files = source_files
        self.source_paths = source_paths