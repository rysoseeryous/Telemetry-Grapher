# -*- coding: utf-8 -*-
"""
Created on Mon May  6 15:02:46 2019

@author: seery
"""
class Data_Manager(QDialog):
    def __init__(self, parent):
        super().__init__()
        self.parent = parent
        self.setWindowTitle('Data Manager')
        self.setWindowIcon(QIcon('satellite.png'))

        self.groups = copy.deepcopy(parent.groups)  # copy so that if you can still discard changes
        self.group_reassign = {name:[] for name in self.groups}  # for renaming groups
#        print(self.group_reassign)
        self.modified = False

        self.resize(1000,500)
        self.grid = QGridLayout()
        self.tabBase = QTabWidget()
        self.tabBase.setStyleSheet("QTabBar::tab {height: 30px; width: 300px} QTabWidget::tab-bar {alignment:center;}")
        self.tabBase.currentChanged.connect(self.refresh_tab)
        self.save = QPushButton('Save')
        self.save.setDefault(True)
        self.save.clicked.connect(self.save_changes)
        self.cancel = QPushButton('Cancel')
        self.cancel.clicked.connect(self.close)  # AttributeError: 'bool' object has no attribute 'accept' -> from event.accept()
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
        self.dataframes_tab = DataFrames_Tab(self)
        self.configure_tab = Configure_Tab(self)
        self.tabBase.addTab(self.import_tab, 'Import')
        self.tabBase.addTab(self.configure_tab, 'Configure')
        self.tabBase.addTab(self.dataframes_tab, 'DataFrames')

    def keyPressEvent(self, event):
        """Close application from escape key.

        results in QMessageBox dialog from closeEvent, good but how/why?
        """
        if event.key() == Qt.Key_Escape:
            self.close()

    def refresh_tab(self, tab_index):
        if self.tabBase.currentIndex() == 1:  # hard coded - this will break if I ever rearrange the tabs. But I think that's ok.
            # Configure Tab
            self.configure_tab.display_header_info()
        elif self.tabBase.currentIndex() == 2:
            # DataFrames Tab
            self.dataframes_tab.display_dataframe()

    def popup(self, text, informative=None, details=None, buttons=2):
        """Brings up a message box with provided text and returns Ok or Cancel."""
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
            SF = self.parent.series_frame
            ### Eventually, loop this through all open axes frames (excel tab implementation)
            AF = self.parent.axes_frame
            self.parent.groups = self.groups

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

            # Rename/delete groups in subplots first
            for sp in AF.subplots:
                for group in copy.deepcopy(tuple(sp.contents.keys())):
#                    print('MW group: ',group)
                    if group not in new_contents:  # if not recognized
#                        print('group_reassign: ',self.group_reassign)
                        if group in self.group_reassign:  # check if it's been renamed
                            new_name = self.group_reassign[group][-1]
                            sp.contents[new_name] = sp.contents[group]  # if so, take the most recent renaming
                        del sp.contents[group]  # scrap the old one
#                print('sp.contents: ',sp.contents)

            # Rename/delete series in subplots
            for sp in AF.subplots:
                for group in sp.contents:
                    aliases = copy.deepcopy(tuple(sp.contents[group].keys()))  # define loop elements first so it doesn't change size during iteration
#                    print('aliases: ', aliases)
                    new_series = self.groups[group].series
#                    print('new series: ',new_series.keys())
                    for alias in aliases:
                        del sp.contents[group][alias]  # scrap old alias entry (no matter what)
#                        print('sp.contents after del: ', sp.contents)
#                        print('\ncurrent alias_dict: ',self.parent.groups[group].alias_dict)
                        try:
                            header = self.parent.groups[group].alias_dict[alias]  # get original header of each alias in sp.contents
                        except KeyError:  # if original header being used as alias (because no alias was assigned)
                            header = alias
#                        print('alias: header  ->  ', alias,': ',header)
                        if header in new_series and new_series[header].keep:  # if original header recognized in new groups
                            new_alias = new_series[header].alias
                            if not new_alias: new_alias = header
#                            print('new alias: ',new_alias)
                            sp.contents[group][new_alias] = new_series[header].unit  # make new entry with new_alias
                            del new_contents[group][new_alias]
#                            print('sp.contents after replace: ',sp.contents)
                              # delete the entry in new_contents so we can just dump the rest into AF.available_data
                        if not new_contents[group]: del new_contents[group]  # scrap any now-empty groups
#                        print('new contents after replace: ',new_contents)
                sp.refresh()

            # Dump everything else into AF.available_data
            AF.available_data = new_contents
            SF.available.clear()
            SF.search(SF.searchAvailable, SF.available, AF.available_data)

            sp = AF.current_sps
            if len(sp) == 1:
                SF.plotted.clear()
                SF.search(SF.searchPlotted, SF.plotted, sp[0].contents)
            self.feedback('Saved data to main window.')
            self.modified = False


    def closeEvent(self, event):
        if self.modified:
            if self.popup('Discard changes?') == QMessageBox.Cancel:
                event.ignore()
            else:
                QApplication.clipboard().clear()
                event.accept()
        else:
            QApplication.clipboard().clear()
            event.accept()
