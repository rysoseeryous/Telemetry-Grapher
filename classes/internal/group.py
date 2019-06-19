# -*- coding: utf-8 -*-
"""
Created on Thu Jun 13 15:53:02 2019

@author: seery
"""
from .series import Series

class Group():

    def __init__(self, df, source_files=[], source_paths=[], density=100):
        self.data = df  # maybe copy needed
        self.series = {key:Series(self) for key in self.data.columns}
        self.alias_dict = {}
        self.source_files = source_files
        self.source_paths = source_paths
#EG: AB.groups[name].series[header].alias

    def summarize(self):
        print('Source Paths')
        for path in self.source_paths:
            print('\t'+path)
        print('\nHeaders')
        for header in self.series:
            print('\t{}\n\t\t{}'.format(header,self.series[header].summarize()))
        print('\nAssigned Aliases')
        print('\t{}'.format(self.alias_dict))