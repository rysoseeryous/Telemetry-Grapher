# -*- coding: utf-8 -*-
"""
Created on Mon May  6 14:57:32 2019

@author: seery
"""
from PyQt5.QtWidgets import *

class Series_Frame(QWidget):
    """Manages imported data. Shows hierarchically the series (with assigned units) available to plot and the series plotted in the selected subplot(s)."""

    def __init__(self, parent):
        super().__init__()
        self.parent = parent
#         self.resize(300,parent.height)
        grid = QGridLayout()
        w = QWidget()
        ncols = 2
        self.available = QTreeWidget(w)
        self.available.setSelectionMode(QTreeWidget.ExtendedSelection)
        self.available.setHeaderLabels(["Available Series", "Unit"])
        self.available.setColumnCount(ncols)
        self.plotted = QTreeWidget(w)
        self.plotted.setSelectionMode(QTreeWidget.ExtendedSelection)
        self.plotted.setHeaderLabels(["Plotted Series", "Unit"])
        self.available.setColumnCount(ncols)
        self.add = QPushButton('Add')
        self.add.clicked.connect(lambda: self.transfer('Add'))
        self.remove = QPushButton('Remove')
        self.remove.clicked.connect(lambda: self.transfer('Remove'))
        self.searchAvailable = QLineEdit()
        self.searchAvailable.setPlaceholderText('Search')
        self.searchAvailable.textChanged.connect(lambda: self.search(self.searchAvailable, self.available, self.parent.axes_frame.available_data))
        self.searchPlotted = QLineEdit()
        self.searchPlotted.setPlaceholderText('Search')
        self.searchPlotted.textChanged.connect(lambda: self.search(self.searchPlotted, self.plotted, self.get_sp_contents()))

        grid.addWidget(self.searchAvailable, 0, 0)
        grid.addWidget(self.searchPlotted, 0, 1)
        grid.addWidget(self.available, 1, 0)
        grid.addWidget(self.plotted, 1, 1)
        grid.addWidget(self.add, 2, 0)
        grid.addWidget(self.remove, 2, 1)
        self.setLayout(grid)

        self.populate_tree(parent.axes_frame.available_data, self.available)
        self.available.expandAll()
        self.available.resizeColumnToContents(0)

    def cleanup(self):
        """Sorts both trees and deletes any dataframe references that contain no series."""
        for tree in [self.available, self.plotted]:
            tree.sortItems(0,0)  # sort by column 0 in ascending order
            to_delete = []
            for i in range(tree.topLevelItemCount()):
                if tree.topLevelItem(i).childCount() == 0:
                    to_delete.append(i)
                else:
                    tree.topLevelItem(i).sortChildren(0,0)
            for x in to_delete:
                tree.takeTopLevelItem(x)

#    def read_tree(self, tree):
#        """Reads tree into standard contents format {name: {series:units}}."""
#        level0s = [tree.topLevelItem(i) for i in range(tree.topLevelItemCount())]
#        if level0s:
#            names = [n.text(0) for n in level0s]
#            series = [[level0.child(i).text(0) for i in range(level0.childCount())] for level0 in level0s]
#            units = [[level0.child(i).text(1) for i in range(level0.childCount())] for level0 in level0s]
#            contents = {}
#            for n,s,u in zip(names, series, units):
#                contents[n] = dict(zip(s,u))
#        else:
#            contents = {}
#        return contents

    def add_to_contents(self, contents, to_add):
        for name, series_units in to_add.items():
            if name in contents:
                for series, units in series_units.items():
                    contents[name].update({series:units})
            else:
                contents.update({name: series_units})
        return contents

    def remove_from_contents(self, contents, to_remove):
        for name, series_units in to_remove.items():
            if name in contents:
                for series, units in series_units.items():
                    del contents[name][series]
                if not contents[name]:
                    del contents[name]
        return contents

    def populate_tree(self, contents, target_tree):
        """Clears target_tree and repopulates with contents"""
        # populate tree with contents
        target_tree.clear()
        if contents:
            for name, series_units in contents.items():
                level0 = QTreeWidgetItem([name])
                target_tree.addTopLevelItem(level0)
                for series, unit in series_units.items():  # add series/units to their corresponding level0 entry
                    level1 = QTreeWidgetItem([series, unit])
                    level0.addChild(level1)
                level0.setExpanded(True)
            target_tree.resizeColumnToContents(0)

            self.cleanup()

#        """Adds contents to target_tree with no repeats and sorts. Manages available/plotted datasets."""

#        if contents:
#            target_level0 = [target_tree.topLevelItem(i) for i in range(target_tree.topLevelItemCount())]
#            target_names = [n.text(0) for n in target_level0]
#            for name, series_units in contents.items():
#                if name in target_names:  # if dataframe already exists in target_tree, get its level0 entry
#                    i = target_names.index(name)
#                    level0 = target_level0[i]
#                else:  # if not, create it and add it
#                    level0 = QTreeWidgetItem([name])
#                    target_tree.addTopLevelItem(level0)
#                for series, unit in series_units.items():  # add series/units to their corresponding level0 entry
#                    level1 = QTreeWidgetItem([series, unit])
#                    level0.addChild(level1)
#                level0.setExpanded(True)
#            target_tree.resizeColumnToContents(0)
#
#            self.cleanup()

    def update_subplot_contents(self, sp, contents):
        """Updates selected subplots' contents and order."""
        all_units = []
        for series_units in contents.values():
            all_units.extend(series_units.values())
        sp.order = [u for u in sp.order if u in all_units]
        if not sp.order: sp.order = [None]
        sp.contents = copy.deepcopy(contents)
        # Deep copy seems like it should be unnecessary but it prevents sp.contents from being carried over between instances.
        # Can probably remove at full rollout. See also deep copies of data and data_dict in Figure Window __init__()
        # Probably takes a lot of memory

    def transfer(self, caller):
        """Swaps series or entire dataframe references from available to plotted or vice versa."""
        TG = self.parent
        AF = TG.axes_frame
        selected_sps = AF.current_sps
        if not selected_sps:
            TG.statusBar().showMessage('Select a subplot to add or remove series')
        elif len(selected_sps) > 1:
            TG.statusBar().showMessage('Series can only be added to one subplot')
        else:
            sp = selected_sps[0]
            if caller == 'Add':
                sourceTree = self.available
                availableFunc = self.remove_from_contents
                plottedFunc = self.add_to_contents
            if caller == 'Remove':
                sourceTree = self.plotted
                availableFunc = self.add_to_contents
                plottedFunc = self.remove_from_contents

            selected = sourceTree.selectedItems()
            if selected:
                # Read contents from selected items
                contents = {}
                if all(item.parent() is None for item in selected):  # if only level0 items in selection
                    for item in selected:
                        children = [item.child(i) for i in range(item.childCount())]
                        for child in children: item.removeChild(child)
                        name = item.text(0)
                        series = [child.text(0) for child in children]
                        units = [child.text(1) for child in children]
                        contents = self.add_to_contents(contents,{name: dict(zip(series,units))})
                else:
                    for item in selected:
                        if item.parent():  # if selected item is level1 (ignore if level0)
                            parent = item.parent()
                            i = parent.indexOfChild(item)
                            child = parent.takeChild(i)
                            name = parent.text(0)
                            series = child.text(0)
                            units = child.text(1)
                            contents = self.add_to_contents(contents,{name: {series:units}})
                # Add/remove contents from sp
                self.update_subplot_contents(sp, plottedFunc(sp.contents, contents))
                # Refresh sp
                sp.refresh()
                # Transfer contents to/from available_data
                AF.available_data = availableFunc(AF.available_data, contents)
                # Populate both trees with un-search-filtered data
                self.populate_tree(AF.available_data, self.available)
                self.populate_tree(sp.contents, self.plotted)
                self.cleanup()
                # Reapply search filters
                self.search(self.searchAvailable, self.available, AF.available_data)
                self.search(self.searchPlotted, self.plotted, sp.contents)
            else:
                TG.statusBar().showMessage('No series selected')

    def get_sp_contents(self):
        TG = self.parent
        AF = TG.axes_frame
        if len(AF.current_sps) == 1:
            contents = AF.current_sps[0].contents
        else:
            contents = {}
        return contents

    def search(self, search_bar, tree, data_set):
        """Displays only series in tree which match input to search_bar (case insensitive)"""
        user_input = re.compile(search_bar.text(), re.IGNORECASE)
        matches = {}
        if data_set:
            for name, series_units in data_set.items():
                for series, units in series_units.items():
                    if user_input.search(series):
                        matches = self.add_to_contents(matches, {name: {series:units}})
            self.populate_tree(matches, tree)
#            self.cleanup()

#        level0s = [tree.topLevelItem(i) for i in range(tree.topLevelItemCount())]
#        if level0s:
#            names = [n.text(0) for n in level0s]
#            series = [[level0.child(i).text(0) for i in range(level0.childCount()) if user_input.search(level0.child(i).text(0))] for level0 in level0s]
#            units = [[level0.child(i).text(1) for i in range(level0.childCount()) if user_input.search(level0.child(i).text(0))] for level0 in level0s]
#            contents = {}
#            for n,s,u in zip(names, series, units):
#                contents[n] = dict(zip(s,u))
#            tree.clear()
#            self.populate_tree(contents, tree)
#            self.cleanup()
