# -*- coding: utf-8 -*-
"""
Created on Mon May  6 15:02:46 2019

@author: seery
"""
from PyQt5.QtWidgets import *

class Data_Manager(QDialog):
    def __init__(self, parent):
        super().__init__()
        self.parent = parent
        self.setWindowTitle('Data Manager')
        self.setWindowIcon(QIcon('satellite.png'))

        self.groups = copy.deepcopy(parent.groups)  # copy so that if you can still discard changes
        self.data_dict = copy.deepcopy(parent.data_dict)
        self.modified = False

        self.resize(1000,500)
        self.grid = QGridLayout()
        self.tabBase = QTabWidget()
        self.tabBase.currentChanged.connect(self.refresh_tab)
        self.save = QPushButton('Save')
        self.save.setDefault(True)
        self.save.clicked.connect(self.save_changes)
        self.cancel = QPushButton('Cancel')
#        self.cancel.clicked.connect(self.closeEvent)  # AttributeError: 'bool' object has no attribute 'accept' -> from event.accept()
        msgLog = QLabel('Message Log:')
        self.messageLog = QTextEdit()
        self.messageLog.setReadOnly(True)
        self.messageLog.setText('Ready')

        self.grid.addWidget(self.tabBase,0,0,1,3)
        self.grid.addWidget(msgLog,1,0)
        self.grid.addWidget(self.messageLog,1,1,2,1)
        self.grid.addWidget(self.save,1,2)
        self.grid.addWidget(self.cancel,2,2)
        self.grid.setColumnStretch(1,100)
        #self.messageLog.resize(self.messageLog.width(),100)

        self.setLayout(self.grid)
        self.import_tab = Import_Tab(self)
        self.configure_tab = Configure_Tab(self)
        self.dataframes_tab = DataFrames_Tab(self)  # eventually make your own tab class
        self.tabBase.addTab(self.import_tab, 'Import')
        self.tabBase.addTab(self.configure_tab, 'Configure')
        self.tabBase.addTab(self.dataframes_tab, 'DataFrames')

    def refresh_tab(self):
        pass
    # might be entirely unnecessary because the tables are updated when select group is changed
    # and select group's index changed signal is called every time an item is added, that is, every time a group is imported.

#        if self.tabBase.currentIndex() == 1:  # hard coded - this will break if I ever rearrange the tabs. But I think that's ok.
#            # Configure Tab
#
#        elif self.tabBase.currentIndex() == 2:
#            # DataFrames Tab

#            self.feedback('Configure Tab Selected')
#            self.feedback('Group: '.format(self.configure_tab.selectGroup.currentText()))
            # repopulate configure tab's table with header info from its currently selected group

    def popup(self, text, informative=None, details=None, buttons=2):
        """Brings up a message box with provided text and returns Ok or Cancel"""
        self.prompt = QMessageBox()
        self.prompt.setWindowTitle("HEY.")
        self.prompt.setIcon(QMessageBox.Question)
        self.prompt.setText(text)
        if buttons == 2:
            self.prompt.setStandardButtons(QMessageBox.Ok | QMessageBox.Cancel)
        elif buttons == 1:
            self.prompt.setStandardButtons(QMessageBox.Ok)
        self.prompt.setInformativeText(informative)
        self.prompt.setDetailedText(details)
        self.prompt.show()
        return self.prompt.exec_()

    def feedback(self, message, mode='line'):
        """Adds message to message log as one line. Set overwrite=True to overwrite the last line in the log."""
        if mode == 'line':
            self.messageLog.setText(self.messageLog.toPlainText() + '\n' + message)
        elif mode == 'append':
            self.messageLog.setText(self.messageLog.toPlainText() + message)
        elif mode == 'overwrite':
            current_text = self.messageLog.toPlainText()
            self.messageLog.setText(current_text[:current_text.rfind('\n')+1] + message)
        self.messageLog.verticalScrollBar().setValue(self.messageLog.verticalScrollBar().maximum())

    def save_changes(self):
        if self.modified:
            self.parent.groups = self.groups
            self.parent.data_dict = self.data_dict
            self.modified = False
        # should these be copies?
        # should I clear the manager's groups/data_dict after saving? IN THIS CASE THEY WOULD NEED TO BE COPIES!!
            SF = self.parent.series_frame
            ### Eventually, loop this through all open axes frames (excel tab implementation)
            AF = self.parent.axes_frame
            AF.available_data = SF.add_to_contents(AF.available_data, self.data_dict)
            SF.search(SF.searchAvailable, SF.available, AF.available_data)

    def closeEvent(self, event):
        if self.modified:
            if self.popup('Discard changes?') == QMessageBox.Cancel:
                event.ignore()
            else:
                event.accept()
        else:
            event.accept()
