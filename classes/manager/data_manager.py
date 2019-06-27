# -*- coding: utf-8 -*-
"""
Created on Thu Jun 13 15:49:30 2019

@author: seery
"""
import re
from copy import copy, deepcopy

from PyQt5.QtWidgets import (QApplication, QDialog, QMessageBox, QWidget,
                             QDialogButtonBox, QVBoxLayout, QSplitter,
                             QTabWidget, QTextEdit, QLabel)
from PyQt5.QtGui import QIcon
from PyQt5.QtCore import Qt

from .groups_tab import GroupsTab
from .configure_tab import ConfigureTab

class DataManager(QDialog):
    """Manages the importing of data and configuration of data groups."""

    def __init__(self, parent):
        super().__init__()
        self.parent = parent
        self.setWindowTitle('Data Manager')
        self.setWindowIcon(QIcon('rc/satellite.png'))
        self.groups = deepcopy(parent.groups)
        self.group_reassign = {name:[name] for name in self.groups}
        self.modified = False
        self.resize(1000, 500)
        splitter = QSplitter(Qt.Vertical)

        self.tab_base = QTabWidget()
        self.groups_tab = GroupsTab(self)
        self.configure_tab = ConfigureTab(self)
        self.tab_base.addTab(self.groups_tab, 'File Grouping')
        self.tab_base.addTab(self.configure_tab, 'Series Configuration')
        splitter.addWidget(self.tab_base)

        self.log_base = QWidget()
        vbox = QVBoxLayout()
        vbox.addWidget(QLabel('Message Log:'))
        self.message_log = QTextEdit()
        self.message_log.setReadOnly(True)
        vbox.addWidget(self.message_log)
        self.log_base.setLayout(vbox)
        splitter.addWidget(self.log_base)

        vbox = QVBoxLayout()
        self.buttonBox = QDialogButtonBox()
        self.buttonBox.setStandardButtons(QDialogButtonBox.Save |
                                          QDialogButtonBox.Close)
        self.buttonBox.accepted.connect(self.save_changes)
        self.buttonBox.rejected.connect(self.close)

        vbox.addWidget(splitter)
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
        if self.message_log.toPlainText():
            if mode == 'line':
                self.message_log.setText(
                        self.message_log.toPlainText() + '\n' + message)
            elif mode == 'append':
                self.message_log.setText(
                        self.message_log.toPlainText() + message)
            elif mode == 'overwrite':
                current_text = self.message_log.toPlainText()
                self.message_log.setText(
                        current_text[:current_text.rfind('\n')+1] + message)
        else:
            self.message_log.setText(message)
        v_scrollbar = self.message_log.verticalScrollBar()
        v_scrollbar.setValue(v_scrollbar.maximum())

    def derive_alias(self, s):
        alias = s.alias
        if not alias:
            unit = s.unit
            alias = re.sub('\[{}\]'.format(unit), '', s.header)
        return alias.strip()

    def save_changes(self):
        """Saves groups created in Data Manager dialog to main window.
        Maps existing data to new data."""

        def get_header(alias):
                try:
                    # get original header of each alias in sp.contents
                    return ui.groups[sp_name].alias_dict[alias]
                except KeyError:
                    # if original header being used as alias
                    # (because no alias was assigned)
                    return alias


        if not self.modified: return
        ui = self.parent
        sd = ui.series_display
        cp = ui.control_panel
        af = ui.axes_frame

        # Get new group: alias information from self.groups
        dm_contents = ui.groups_to_contents(self.groups)
        # Rename/delete groups in subplots first
        for sp in af.subplots:
            for sp_name in copy(tuple(sp.contents.keys())):
                try:
                    dm_name = self.group_reassign[sp_name][-1]
                    sp.contents[dm_name] = sp.contents[dm_name]
                    if dm_name != sp_name: del sp.contents[sp_name]

                    # Try to map old aliases to new
                    sp_aliases = sp.contents[dm_name]
                    dm_aliases = dm_contents[dm_name]
                    headers = [get_header(alias) for alias in copy(sp_aliases)]
                    sp_aliases.clear()
                    for s in self.groups[dm_name].kept():
                        if s.header in headers:
                            new_alias = self.derive_alias(s)
                            sp_aliases.append(new_alias)
                            dm_aliases.remove(new_alias)
                        if not dm_aliases: del dm_aliases
                except KeyError:
                    del sp.contents[sp_name]
            sp.plot(skeleton=True)

        ui.groups = self.groups
        cp.time_filter()  # calls af.refresh_all()
        #reset group_reassign
        self.group_reassign = {name:[name] for name in self.groups}
        # Dump everything else into af.available_data
        af.available_data = dm_contents
        sd.available.clear()
        sd.search_available.textChanged.emit(sd.search_available.text())

        if len(af.current_sps) == 1:
            sp = af.current_sps[0]
            sd.plotted.clear()
            sd.search_plotted.textChanged.emit(sd.search_plotted.text())
        self.feedback('Saved data to main window.')
        self.modified = False

    def closeEvent(self, event):
        """Asks user to save changes before exiting."""
        ui = self.parent
        if self.modified:
            choice = ui.popup('Discard changes?', title='Exiting Data Manager')
            if choice == QMessageBox.Cancel:
                event.ignore()
                return
            elif choice == QMessageBox.Save:
                self.save_changes()
        QApplication.clipboard().clear()
        event.accept()
