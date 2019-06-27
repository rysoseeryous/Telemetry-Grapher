# -*- coding: utf-8 -*-
"""
Created on Wed Jun 19 14:09:14 2019

@author: seery
"""

class ContentsDict(dict):
    """Hierarchical dictionary.
    {group1: headers1, group2: headers2...}
    group -> string
    headers -> list of strings"""

    def __init__(self, *args):
        dict.__init__(self, args)

    def add(self, to_add):
        for group in to_add:
            if group in self:
                self[group].extend(to_add[group])
            else:
                self[group] = to_add[group]

    def remove(self, to_remove):
        for group in to_remove:
#            if group in contents:  # this should always be true
            for alias in to_remove[group]:
                self[group].remove(alias)
            if not self[group]:
                del self[group]
