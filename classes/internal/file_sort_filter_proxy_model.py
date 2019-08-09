# -*- coding: utf-8 -*-
"""
Created on Mon Aug  5 10:07:49 2019

@author: seery
"""
import re
import datetime as dt

from PyQt5.QtCore import QSortFilterProxyModel

class FileSortFilterProxyModel(QSortFilterProxyModel):

    def __init__(self, parent):
        QSortFilterProxyModel.__init__(self, parent)

    def file_size_to_bytes(self, size):
        num, suffix = re.split(' ', size)
        num = re.sub(',', '', num)
        n = self.parent().suffixes.index(suffix)
        return int(num)*1000**n

    def lessThan(self, source_left, source_right):
        left = self.sourceModel().data(source_left)
        right = self.sourceModel().data(source_right)
        if source_left.column() == 1:
            left_size = self.file_size_to_bytes(left)
            right_size = self.file_size_to_bytes(right)
            return left_size < right_size
        elif source_left.column() == 2:
            left_date = dt.datetime.strptime(left, self.parent().date_format)
            right_date = dt.datetime.strptime(right, self.parent().date_format)
            return left_date < right_date
        else:
            return left < right
