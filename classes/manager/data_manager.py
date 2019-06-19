# -*- coding: utf-8 -*-
"""
Created on Thu Jun 13 15:49:30 2019

@author: seery
"""
import re
import copy

from PyQt5.QtWidgets import (QApplication, QDialog, QMessageBox,
                             QDialogButtonBox, QVBoxLayout,
                             QTabWidget, QTextEdit, QLabel)
from PyQt5.QtGui import QIcon
from PyQt5.QtCore import Qt

from .groups_tab import Groups_Tab
from .configure_tab import Configure_Tab

class Data_Manager(QDialog):
    """Manages the importing of data and configuration of data groups."""

    def __init__(self, parent):
        super().__init__()
        self.parent = parent
        self.setWindowTitle('Data Manager')
        self.setWindowIcon(QIcon('rc/satellite.png'))

        self.groups = copy.deepcopy(parent.groups)  # copy so that if you can still discard changes
        self.group_reassign = {name:[name] for name in self.groups}  # for renaming groups

        self.modified = False

        self.resize(1000, 500)
        vbox = QVBoxLayout()
        self.tabBase = QTabWidget()
        self.groups_tab = Groups_Tab(self)
        self.configure_tab = Configure_Tab(self)
        self.tabBase.addTab(self.groups_tab, 'File Grouping')
        self.tabBase.addTab(self.configure_tab, 'Series Configuration')
        vbox.addWidget(self.tabBase)

        vbox.addWidget(QLabel('Message Log:'))
        self.messageLog = QTextEdit()
        self.messageLog.setReadOnly(True)
        vbox.addWidget(self.messageLog)

        self.buttonBox = QDialogButtonBox()
        self.buttonBox.setStandardButtons(QDialogButtonBox.Save | QDialogButtonBox.Close)
        self.buttonBox.accepted.connect(self.save_changes)
        self.buttonBox.rejected.connect(self.close)
        vbox.addWidget(self.buttonBox)
        self.setLayout(vbox)
        self.groups_tab.search_dir()

    def keyPressEvent(self, event):
        """Close dialog from escape key."""
        if event.key() == Qt.Key_Escape:
            self.close()

    def feedback(self, message, mode='line'):
        """Adds message to message log as one line.
        Set mode=overwrite to overwrite the last line in the log.
        Set mode=append to append the last line in the log."""
        if self.messageLog.toPlainText():
            if mode == 'line':
                self.messageLog.setText(self.messageLog.toPlainText() + '\n' + message)
            elif mode == 'append':
                self.messageLog.setText(self.messageLog.toPlainText() + message)
            elif mode == 'overwrite':
                current_text = self.messageLog.toPlainText()
                self.messageLog.setText(current_text[:current_text.rfind('\n')+1] + message)
        else:
            self.messageLog.setText(message)
        self.messageLog.verticalScrollBar().setValue(self.messageLog.verticalScrollBar().maximum())

    def save_changes(self):
        """Saves groups created in Data Manager dialog to Application Base main window.
        Maps existing data to new data within subplots and in available tree, saving the user the trouble of repopulating the subplots every time a change is made."""
        if self.modified:
            AB = self.parent
            SF = AB.series_frame
            CF = AB.control_frame
            AF = AB.axes_frame

            # Get new group: alias information from self.groups
            new_contents = AB.groups_to_contents(self.groups)

            # Rename/delete groups in subplots first
            for sp in AF.subplots:
                for group_name in copy.copy(tuple(sp.contents.keys())):
                    # Try to map old group name to new
                    if group_name in self.group_reassign:
                        new_name = self.group_reassign[group_name][-1]  # get new name
                        sp.contents[new_name] = sp.contents[group_name] # transfer contents from old to new
                        if new_name != group_name: del sp.contents[group_name] # scrap the old (only if group was renamed)

                        # Try to map old aliases to new
                        aliases = copy.copy(sp.contents[new_name])
                        new_series = self.groups[new_name].series  # dictionary of Series objects
                        for alias in aliases:
                            sp.contents[new_name].remove(alias)  # delete the alias entry first in case alias == new_alias

                            try:
                                header = AB.groups[group_name].alias_dict[alias]  # get original header of each alias in sp.contents
                            except KeyError:  # if original header being used as alias (because no alias was assigned)
                                header = alias
                            if header in new_series and new_series[header].keep:
                                new_alias = new_series[header].alias
                                if not new_alias:
                                    unit = new_series[header].unit
                                    new_alias = re.sub('\[{}\]'.format(unit), '', header).strip()
                                sp.contents[new_name].append(new_alias)
                                new_contents[new_name].remove(new_alias)
                            if not new_contents[new_name]: del new_contents[new_name]
                    else:
                        del sp.contents[group_name] # scrap it because it doesn't exist in new_contents
                sp.plot(skeleton=True)


            AB.groups = self.groups
            CF.time_filter()  # calls AF.refresh_all()
            #reset group_reassign
            self.group_reassign = {name:[name] for name in self.groups}
            # Dump everything else into AF.available_data
            AF.available_data = new_contents
            SF.available.clear()
            SF.search(SF.searchAvailable, SF.available, AF.available_data)

            if len(AF.current_sps) == 1:
                sp = AF.current_sps[0]
                SF.plotted.clear()
                SF.search(SF.searchPlotted, SF.plotted, sp.contents)
#            AF.refresh_all()
            self.feedback('Saved data to main window.')
            self.modified = False

    def closeEvent(self, event):
        """Asks user to confirm exit if changes have been made and not saved."""
        AB = self.parent
        if self.modified:
            choice = AB.popup('Discard changes?', title='Exiting Data Manager')
            if choice == QMessageBox.Cancel:
                event.ignore()
                return
            elif choice == QMessageBox.Save:
                self.save_changes()
        QApplication.clipboard().clear()
        event.accept()