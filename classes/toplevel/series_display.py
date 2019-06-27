# -*- coding: utf-8 -*-
"""
Created on Thu Jun 13 15:47:40 2019

@author: seery
"""
import re

from PyQt5.QtWidgets import (QDockWidget, QGridLayout, QPushButton, QLineEdit,
                             QWidget, QTreeWidget, QTreeWidgetItem)
from PyQt5.QtCore import QObject

from ..internal.contents_dict import ContentsDict

class SeriesDisplay(QDockWidget):
    """Displays hierarchical string references to imported data groups/aliases.
    Available tree shows series which have not yet been plotted.
    Plotted tree shows contents of selected subplot."""

    def __init__(self, parent, title):
        super().__init__(title)
        self.parent = parent
        grid = QGridLayout()
        w = QWidget()
        ncols = 1
        self.available = QTreeWidget()
        self.available.setSelectionMode(QTreeWidget.ExtendedSelection)
        self.available.setSortingEnabled(True)
        self.available.setHeaderLabels(["Unplotted Series"])
        self.available.setColumnCount(ncols)
        self.plotted = QTreeWidget()
        self.plotted.setSelectionMode(QTreeWidget.ExtendedSelection)
        self.plotted.setSortingEnabled(True)
        self.plotted.setHeaderLabels(["Subplot Contents"])
        self.available.setColumnCount(ncols)
        self.add = QPushButton('Add')
        self.add.clicked.connect(self.transfer)
        self.remove = QPushButton('Remove')
        self.remove.clicked.connect(self.transfer)
        self.search_available = QLineEdit()
        self.search_available.setPlaceholderText('Search')
        self.search_available.textChanged.connect(self.search)
        self.search_plotted = QLineEdit()
        self.search_plotted.setPlaceholderText('Search')
        self.search_plotted.textChanged.connect(self.search)

        grid.addWidget(self.search_available, 0, 0)
        grid.addWidget(self.search_plotted, 0, 1)
        grid.addWidget(self.available, 1, 0)
        grid.addWidget(self.plotted, 1, 1)
        grid.addWidget(self.add, 2, 0)
        grid.addWidget(self.remove, 2, 1)
        w.setLayout(grid)
        self.setWidget(w)

        self.populate_tree(parent.axes_frame.available_data, self.available)
        self.available.expandAll()
        self.available.resizeColumnToContents(0)

    def cleanup(self):
        """Sorts both trees and deletes any empty group references."""
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

    def populate_tree(self, contents, target_tree):
        """Clears target_tree and repopulates with contents"""
        target_tree.clear()
        if contents:
            for group in contents:
                level0 = QTreeWidgetItem([group])
                target_tree.addTopLevelItem(level0)
                # add series to their corresponding level0 entry
                for alias in contents[group]:
                    level1 = QTreeWidgetItem([alias])
                    level0.addChild(level1)
                level0.setExpanded(True)
            target_tree.resizeColumnToContents(0)
            self.cleanup()

    def transfer(self):
        """Swaps series or group references between available and plotted."""
        ui = self.parent
        af = ui.axes_frame
        selected_sps = af.current_sps
        if not selected_sps:
            ui.statusBar().showMessage(
                    'Select a subplot to add or remove series')
        elif len(selected_sps) > 1:
            ui.statusBar().showMessage(
                    'Series can only be added to one subplot')
        else:
            sp = selected_sps[0]
            caller = QObject.sender(self)
            if caller == self.add:
                selected = self.available.selectedItems()
            elif caller == self.remove:
                selected = self.plotted.selectedItems()

            if selected:
                # Read contents from selected items
                contents = ContentsDict()
                for item in selected:
                    if all(item.parent() is None for item in selected):
                        # if only level0 items in selection
                        count = item.childCount()
                        children = [item.child(i) for i in range(count)]
                        for child in children: item.removeChild(child)
                        group = item.text(0)
                        aliases = [child.text(0) for child in children]
                    else:
                        if item.parent():
                            # if selected item is level1 (ignore if level0)
                            parent = item.parent()
                            i = parent.indexOfChild(item)
                            child = parent.takeChild(i)
                            group = parent.text(0)
                            aliases = [child.text(0)]
                    contents.add({group: aliases})

                if caller == self.add:
                    sp.contents.add(contents)
                    af.available_data.remove(contents)
                elif caller == self.remove:
                    sp.contents.remove(contents)
                    af.available_data.add(contents)
                # Refresh sp
                sp.plot(skeleton=True)
                af.refresh_all()
                # Populate both trees with un-search-filtered data
                self.populate_tree(af.available_data, self.available)
                self.populate_tree(sp.contents, self.plotted)
                self.cleanup()
                # Reapply search filters
                w = self.search_available
                w.textChanged.emit(w.text())
                w = self.search_plotted
                w.textChanged.emit(w.text())
            else:
                ui.statusBar().showMessage('No series selected')

    def get_sp_contents(self):
        """Returns contents of selected subplot if exactly one is selected.
        Otherwise returns an empty ContentsDict object."""
        ui = self.parent
        af = ui.axes_frame
        if len(af.current_sps) == 1:
            return af.current_sps[0].contents
        else:
            return ContentsDict()

    def search(self, text):
        """Displays series in tree which match input to search bars.
        (case insensitive)"""
        search_bar = QObject.sender(self)
        if search_bar == self.search_available:
            tree = self.available
            data_set = self.parent.axes_frame.available_data
        elif search_bar == self.search_plotted:
            tree = self.plotted
            data_set = self.get_sp_contents()
        # There's probably a more efficient way to do this. More pythonic.
        user_input = re.compile(text, re.IGNORECASE)
        matches = ContentsDict()
        if data_set:
            for group, headers in data_set.items():
                for alias in headers:
                    if user_input.search(alias):
                        matches.add({group: [alias]})
            self.populate_tree(matches, tree)
