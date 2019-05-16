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
    def summarize(self):
        print('Source Paths')
        for path in self.source_paths:
            print('\t'+path)
        print('\nHeaders')
        for header in self.series:
            print('\t{}\n\t\t{}'.format(header,self.series[header].summarize()))
        print('\nAssigned Aliases')
        print('\t{}'.format(self.alias_dict))


class Series():
    def __init__(self, alias='', unit=None, scale=1.0, keep=True):
        self.alias = alias
        self.unit = unit
        self.scale = scale
        self.keep = keep

    def summarize(self):
        return 'Alias: '+str(self.alias)+'  Unit: '+str(self.unit)+'  Scale: '+str(self.scale)+'  Keep: '+str(self.keep)
