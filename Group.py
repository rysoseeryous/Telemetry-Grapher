# -*- coding: utf-8 -*-
"""
Created on Mon May  6 15:02:04 2019

@author: seery
"""

class Group():
    def __init__(self, df, og_headers, source_files, source_paths):
        self.data = df
        self.og_headers = og_headers
        self.alias_dict = {key:None for key in og_headers}
        self.source_files = source_files
        self.source_paths = source_paths