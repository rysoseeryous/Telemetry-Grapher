# -*- coding: utf-8 -*-
"""
Created on Thu Jun 13 15:53:02 2019

@author: seery
"""
from .series import Series

class Group():

    def __init__(self, df):
        self.data = df
        self.series_dict = {header: Series(self, header, '')
                            for header in self.data.columns}
        self.alias_dict = {}
#EG: AB.groups[name].series(header).alias

    def series(self, which=None):
        if which is None:
            return (s for s in self.series_dict.values())
        else:
            try:
                return self.series_dict[which]
            except TypeError:
                return (self.series_dict[header] for header in which)

    def kept(self):
        return (s for s in self.series_dict.values() if s.keep)

    def summarize(self):
        print('Headers')
        for series in self.series():
            print('\t{}\n\t\t{}'.format(series.header, series.summarize()))
        print('\nAssigned Aliases')
        print('\t{}'.format(self.alias_dict))