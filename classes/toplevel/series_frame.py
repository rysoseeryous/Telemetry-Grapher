# -*- coding: utf-8 -*-
"""
Created on Thu Jun 13 15:47:40 2019

@author: seery
"""
import re

from PyQt5.QtWidgets import (QWidget, QGridLayout, QPushButton, QLineEdit,
                             QTreeWidget, QTreeWidgetItem)

class Series_Frame(QWidget):
    """Displays hierarchical string references to imported data groups/aliases.
    Available tree shows series which have not yet been plotted.
    Plotted tree shows contents of selected subplot."""

    def __init__(self, parent):
        super().__init__()
        self.parent = parent
        grid = QGridLayout()
        w = QWidget()
        ncols = 1
        self.available = QTreeWidget(w)
        self.available.setSelectionMode(QTreeWidget.ExtendedSelection)
        self.available.setSortingEnabled(True)
        self.available.setHeaderLabels(["Available Series"])
        self.available.setColumnCount(ncols)
        self.plotted = QTreeWidget(w)
        self.plotted.setSelectionMode(QTreeWidget.ExtendedSelection)
        self.plotted.setSortingEnabled(True)
        self.plotted.setHeaderLabels(["Plotted Series"])
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
        """Sorts both trees and deletes any group references that contain no series."""
        for tree in [self.available, self.plotted]:
            tree.sortItems(0, 0)  # sort by column 0 in ascending order
            to_delete = []
            for i in range(tree.topLevelItemCount()):
                if tree.topLevelItem(i).childCount() == 0:
                    to_delete.append(i)
                else:
                    tree.topLevelItem(i).sortChildren(0, 0)
            for x in to_delete:
                tree.takeTopLevelItem(x)

    def add_to_contents(self, contents, to_add):
        """Returns contents dictionary extended by items in to_add."""
        for group in to_add:
            if group in contents:
                contents[group].extend(to_add[group])
            else:
                contents[group] = to_add[group]
        return contents

    def remove_from_contents(self, contents, to_remove):
        """Returns contents dictionary without items in to_remove."""
        for group in to_remove:
            if group in contents:
                for alias in to_remove[group]:
                    contents[group].remove(alias)
                if not contents[group]:
                    del contents[group]
        return contents

    def populate_tree(self, contents, target_tree):
        """Clears target_tree and repopulates with contents"""
        target_tree.clear()
        if contents:
            for group in contents:
                level0 = QTreeWidgetItem([group])
                target_tree.addTopLevelItem(level0)
                for alias in contents[group]:  # add series to their corresponding level0 entry
                    level1 = QTreeWidgetItem([alias])
                    level0.addChild(level1)
                level0.setExpanded(True)
            target_tree.resizeColumnToContents(0)
            self.cleanup()

    def transfer(self, caller):
        """Swaps series or entire group references from available to plotted or vice versa."""
        AB = self.parent
        AF = AB.axes_frame
        selected_sps = AF.current_sps
        if not selected_sps:
            AB.statusBar().showMessage('Select a subplot to add or remove series')
        elif len(selected_sps) > 1:
            AB.statusBar().showMessage('Series can only be added to one subplot')
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
                for item in selected:
                    if all(item.parent() is None for item in selected):  # if only level0 items in selection
                        children = [item.child(i) for i in range(item.childCount())]
                        for child in children: item.removeChild(child)
                        group = item.text(0)
                        aliases = [child.text(0) for child in children]
                    else:
                        if item.parent():  # if selected item is level1 (ignore if level0)
                            parent = item.parent()
                            i = parent.indexOfChild(item)
                            child = parent.takeChild(i)
                            group = parent.text(0)
                            aliases = [child.text(0)]
                    contents = self.add_to_contents(contents, {group: aliases})
                # Add/remove contents from sp
                sp.contents = plottedFunc(sp.contents, contents)
                # Refresh sp
                sp.plot(skeleton=True)
                AF.refresh_all()
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
                AB.statusBar().showMessage('No series selected')

    def get_sp_contents(self):
        """Returns contents of selected subplot if exactly one is selected, otherwise returns an empty dictionary."""
        AB = self.parent
        AF = AB.axes_frame
        if len(AF.current_sps) == 1:
            contents = AF.current_sps[0].contents
        else:
            contents = {}
        return contents

    def search(self, search_bar, tree, data_set):
        """Displays series in tree which match input to search_bar (case insensitive)"""
        # There's probably a more efficient way to do this. More pythonic.
        user_input = re.compile(search_bar.text(), re.IGNORECASE)
        matches = {}
        if data_set:
            for group in data_set:
                to_add = {group: [alias for alias in data_set[group] if user_input.search(alias)]}
                matches = self.add_to_contents(matches, to_add)
            self.populate_tree(matches, tree)
