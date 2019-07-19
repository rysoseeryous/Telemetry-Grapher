# -*- coding: utf-8 -*-
"""series_display.py - Contains SeriesDisplay class definition."""

# This file is part of Telemetry-Grapher.

# Telemetry-Grapher is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.

# Telemetry-Grapher is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY
# without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.

# You should have received a copy of the GNU General Public License
# along with Telemetry-Grapher. If not, see < https: // www.gnu.org/licenses/>.

__author__ = "Ryan Seery"
__copyright__ = 'Copyright 2019 Max-Planck-Institute for Solar System Research'
__license__ = "GNU General Public License"

import re
from copy import copy

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
        ui = self.parent
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
        grid.addWidget(self.add, 1, 0)
        grid.addWidget(self.remove, 1, 1)
        grid.addWidget(self.available, 2, 0)
        grid.addWidget(self.plotted, 2, 1)
        w.setLayout(grid)
        self.setWidget(w)

        cf = ui.get_current_figure()
        self.populate_tree('available', cf.available_data)
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

    def populate_tree(self, which, contents):
        """Clears target_tree and repopulates with contents"""
        if which == 'available':
            target_tree = self.available
            w = self.search_available
        elif which == 'plotted':
            target_tree = self.plotted
            w = self.search_plotted
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
#            w.textChanged.emit(w.text())
            self.cleanup()

    def transfer(self):
        """Swaps series or group references between available and plotted."""
        ui = self.parent
        cf = ui.get_current_figure()
        sps = cf.current_sps
        if not sps:
            ui.statusBar().showMessage(
                    'Select a subplot to add or remove series')
        elif len(sps) > 1:
            ui.statusBar().showMessage(
                    'Series can only be added to one subplot')
        else:
            sp = sps[0]
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
                    sp.add(contents)
                    cf.available_data.remove(contents)
                elif caller == self.remove:
                    sp.remove(contents)
                    cf.available_data.add(contents)
                sp.plot()
                sp.show_legend()
                cf.select_subplot(None, force_select=[sp])
                cf.update_gridspec()
                cf.draw()
                # Populate both trees and reapply search filter
                self.populate_tree('available', cf.available_data)
                self.populate_tree('plotted', sp.contents)
            else:
                ui.statusBar().showMessage('No series selected')

    def get_sp_contents(self):
        """Returns contents of selected subplot if exactly one is selected.
        Otherwise returns an empty ContentsDict object."""
        ui = self.parent
        cf = ui.get_current_figure()
        if len(cf.current_sps) == 1:
            return cf.current_sps[0].contents
        else:
            return ContentsDict()

    def search(self, text):
        """Displays series in tree which match input to search bars.
        (case insensitive)"""
        search_bar = QObject.sender(self)
        if search_bar == self.search_available:
            which = 'available'
            cf = self.parent.get_current_figure()
            data_set = cf.available_data
        elif search_bar == self.search_plotted:
            which = 'plotted'
            data_set = self.get_sp_contents()
        # There's probably a more efficient way to do this. More pythonic.
        user_input = re.compile(text, re.IGNORECASE)
        matches = ContentsDict()
        if data_set:
            for group, aliases in data_set.items():
                matches.add({group:
                    [a for a in aliases if user_input.search(a)]})
#                #  add an input method to group.series(which)
#                #  for which=function
#                #  ie lambda x: x.keep
#                #  or lambda x: user_input.search(x)
#                for alias in aliases:
#                    if user_input.search(alias):
#                        matches.add({group: [alias]})
            self.populate_tree(which, matches)
