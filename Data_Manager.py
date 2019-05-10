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
#            for group in self.groups:
#                for header in self.groups[group].series:
#                    print(header, ': ', self.groups[group].series[header].alias)
#                    print(header, ': ', self.groups[group].series[header].alias)
#                    print(header, ': ', self.groups[group].series[header].alias)
            SF = self.parent.series_frame
            ### Eventually, loop this through all open axes frames (excel tab implementation)
            AF = self.parent.axes_frame

            # Get new alias/unit information from self.groups
            new_contents = {}
            for group in self.groups:
                aliases = []
                units = []
                for header in self.groups[group].series.keys():
                    if self.groups[group].series[header].keep:
                        alias = self.groups[group].series[header].alias
                        if alias:
                            aliases.append(alias)
                        else:
                            aliases.append(header)
                        units.append(self.groups[group].series[header].unit)
                new_contents.update({group: dict(zip(aliases, units))})

            # Look up headers from aliases in self.parent.groups
            # Map those headers to their new aliases and units
                # Do this through AF.available_data and AF.subplots
#            print('new_contents:',new_contents,'\n')

            for sp in AF.subplots:
                content_groups = copy.deepcopy(tuple(sp.contents.keys()))
                for group in content_groups:
                    # delete top-level groups in subplot if group was deleted.
                    #THIS MEANS that if you edited the source files, and reimported with a different name and the same data, the data will be removed from the figure
#                    print('group: ',group)
                    if group not in new_contents:
                        del sp.contents[group]
                    else:
                        aliases = copy.deepcopy(tuple(sp.contents[group].keys()))  # define loop elements first so it doesn't change size during iteration
#                        print('aliases: ', aliases)
                        for alias in aliases:
#                            print('\ncurrent alias_dict: ',self.parent.groups[group].alias_dict)
                            try:
                                header = self.parent.groups[group].alias_dict[alias]  # get original header of each alias in sp.contents
                            except KeyError:  # if original header being used as alias (because no alias was assigned)
                                header = alias
#                            print('alias: header  ->  ', alias,': ',header)
                            del sp.contents[group][alias]  # scrap old alias entry
#                            print('sp.contents after del: ', sp.contents)
#                            print('new series: ',self.groups[group].series)
                            if header in self.groups[group].series:  # if original header regonized in new groups dictionary
                                new_alias = self.groups[group].series[header].alias
                                if new_alias is None: new_alias = header
                                if self.groups[group].series[new_alias].keep:
                                    sp.contents[group][new_alias] = self.groups[group].series[header].unit
                                    del new_contents[group][new_alias]
#                                print('sp.contents after replace: ',sp.contents)
                                  # delete the entry in new_contents so we can just dump the rest into AF.available_data
                                if not new_contents[group]: del new_contents[group]  # scrap any now-empty groups
#                                print('new contents after replace: ',new_contents)
            AF.available_data = new_contents
            SF.search(SF.searchAvailable, SF.available, AF.available_data)
            self.parent.groups = self.groups
            sp = AF.current_sps
            if len(sp) == 1:
                sp[0].refresh()
                SF.search(SF.searchPlotted, SF.plotted, sp[0].contents)
            self.modified = False
        # should these be copies?
        # should I clear the manager's groups/data_dict after saving? IN THIS CASE THEY WOULD NEED TO BE COPIES!!


    def closeEvent(self, event):
        if self.modified:
            if self.popup('Discard changes?') == QMessageBox.Cancel:
                event.ignore()
            else:
                event.accept()
        else:
            event.accept()
