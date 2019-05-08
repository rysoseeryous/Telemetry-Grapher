# -*- coding: utf-8 -*-
"""
Created on Mon May  6 15:02:46 2019

@author: seery
"""

class Data_Manager(QDialog):
    def __init__(self, parent):
        super().__init__()
        self.parent = parent
        self.dir = os.getcwd()
#        self.dir = 'C:\Users\seery\Documents\German (the person)\PHI_data_housekeeping\CSV'  # delete later, just for quicker access
        self.path_dict = {}
        self.groups = {}

        self.resize(1000,500)
        self.grid = QGridLayout()
        self.tabBase = QTabWidget()
        self.save = QPushButton('Save')
        self.save.setDefault(True)
        self.save.clicked.connect(self.confirm)
        self.cancel = QPushButton('Cancel')
        self.cancel.clicked.connect(self.nevermind)

        self.grid.addWidget(self.tabBase,0,0,1,3)
        self.grid.addWidget(self.save,1,1)
        self.grid.addWidget(self.cancel,1,2)
        self.grid.setColumnStretch(0,100)

        self.setLayout(self.grid)
#        self.popup = QDialogButtonBox()
        self.importUI()
        #self.configureUI()
        self.tabBase.addTab(self.import_tab, 'Import')
        #self.tabBase.addTab(self.configure_tab, 'Configure')

    def popup(self,text):
        """Brings up a message box with provided text and returns Ok or Cancel"""
        self.prompt = QMessageBox()
        self.prompt.setWindowTitle("Input Required")
        self.prompt.setIcon(QMessageBox.Question)
        self.prompt.setText(text)
        self.prompt.setStandardButtons(QMessageBox.Ok | QMessageBox.Cancel)
        self.prompt.show()
        return self.prompt.exec_()

    def confirm(self):

        def floatify(data):
            """Strip everything but numbers, minus signs, and decimals, and returns data as a float. Returns NaN if not possible."""
            data = re.sub('[^0-9-.]', '', str(data))
            try:
                return float(data)
            except ValueError:
                return np.nan
        pass

    def nevermind(self):
        pass

    def closeEvent(self, event):
        event.accept()

    def importUI(self):
        self.import_tab = QWidget()
        self.import_tab.grid = QGridLayout()

        dirLabel = QLabel('Directory:')
        self.directory = QLineEdit(self.dir)
        self.directory.returnPressed.connect(self.search_dir)
        self.browse = QPushButton()
        self.browse.setIcon(self.style().standardIcon(getattr(QStyle, 'SP_DialogOpenButton')))
        self.browse.clicked.connect(self.browse_dialog)
        self.fileSearch = QLineEdit()
        self.fileSearch.setPlaceholderText('Search')
        self.fileSearch.textChanged.connect(self.filter_files)
        self.fileSearch.setFocus(True)
        self.groupName = QLineEdit()
        self.groupName.setPlaceholderText('Group Name')
        foundFilesLabel = QLabel('Found Files')
        groupFilesLabel = QLabel('Files in Group')
        importedGroupsLabel = QLabel('Imported Groups')
        self.foundFiles = QListWidget()
        self.foundFiles.setSelectionMode(QListWidget.ExtendedSelection)
        self.groupFiles = QListWidget()
        self.groupFiles.setSelectionMode(QListWidget.ExtendedSelection)
        self.importedGroups = QListWidget()
        self.add = QPushButton('Add to Group')
        self.add.clicked.connect(lambda: self.toggle_file_active('Add'))
        self.remove = QPushButton('Remove from Group')
        self.remove.clicked.connect(lambda: self.toggle_file_active('Remove'))
        self.editGroup = QPushButton('Edit Source Files')
        self.editGroup.clicked.connect(self.edit_source_files)
        self.importPreferences = QPushButton('Import Preferences')
        self.importPreferences.clicked.connect(self.set_preferences)
        self.importGroup = QPushButton('Import Group')
        self.importGroup.clicked.connect(self.import_group)
        self.deleteGroup = QPushButton('Delete Group')
        self.deleteGroup.clicked.connect(self.delete_group)
        msgLog = QLabel('Message Log:')
        self.messageLog = QTextEdit()
        self.messageLog.setReadOnly(True)
        self.messageLog.setText('Ready')

        #row_weights = [1, 1, 1, 1, 1, 1]
        #for i,rw in enumerate(row_weights):
        #    self.import_tab.grid.setRowStretch(i,rw)
        #col_weights = [1, 1, 1, 1, 1, 1]
        #for i,cw in enumerate(col_weights):
        #    self.import_tab.grid.setColumnStretch(i,cw)

        widgets = [
                dirLabel,
                self.directory,
                self.browse,
                self.fileSearch,
                self.groupName,
                foundFilesLabel,
                groupFilesLabel,
                importedGroupsLabel,
                self.foundFiles,
                self.groupFiles,
                self.importedGroups,
                self.add,
                self.remove,
                self.editGroup,
                self.importPreferences,
                self.importGroup,
                self.deleteGroup,
                msgLog,
                self.messageLog
                ]
        positions = [
                (0,0,1,1),
                (0,1,1,2),
                (0,3,1,1),
                (1,1,1,1),
                (1,2,1,1),
                (2,1,1,1),
                (2,2,1,1),
                (2,3,1,1),
                (3,1,1,1),
                (3,2,1,1),
                (3,3,1,1),
                (4,1,1,1),
                (4,2,1,1),
                (4,3,1,1),
                (5,1,1,1),
                (5,2,1,1),
                (5,3,1,1),
                (6,0,1,1),
                (6,1,1,3),
                ]

        for w, p in zip(widgets, positions):
            self.import_tab.grid.addWidget(w, *p)
        self.import_tab.setLayout(self.import_tab.grid)
        #self.messageLog.resize(self.messageLog.width(),100)
        self.search_dir()

    def feedback(self, message, mode='line'):
        """Adds message to message log as one line. Set overwrite=True to overwrite the last line in the log."""
        if mode == 'line':
            self.messageLog.setText(self.messageLog.toPlainText() + '\n' + message)
        elif mode == 'append':
            self.messageLog.setText(self.messageLog.toPlainText() + message)
        elif mode == 'overwrite':
            current_text = self.messageLog.toPlainText()
            self.messageLog.setText(current_text[:current_text.rfind('\n')+1] + message)

    def search_dir(self):

        def gather_files(path):
            """Returns dictionary {filename:path} of all files in path which match types in filetypes."""
            found_files = []
            path_dict = {}
            filelist = []
            for (dirpath, dirnames, filenames) in os.walk(path):
                filelist.extend(filenames)
            filetypes = re.compile(r'(csv|zip|txt|xls|xlsx)$')
            for file in filelist:
                if re.search(filetypes, file):
                    found_files.append(file)
                    path_dict[file] = os.path.join(path, file)
            return found_files, path_dict

        path = self.directory.text()
        self.dir = path
        self.loaded_files, new_path_dict_entries = gather_files(path)
        self.path_dict.update(new_path_dict_entries)
        self.fileSearch.setText('')
        self.foundFiles.clear()
        self.foundFiles.addItems(self.loaded_files)

    def browse_dialog(self):
        path = str(QFileDialog.getExistingDirectory(self, "Select Directory"))
        self.directory.setText(path)
        self.search_dir()

    def filter_files(self):
        pattern = re.compile(self.fileSearch.text(), re.IGNORECASE)
        matches = [item for item in self.loaded_files if re.search(pattern,item)]
        self.foundFiles.clear()
        self.foundFiles.addItems(matches)

    def toggle_file_active(self, caller):
        if caller == 'Add':
            for file in self.foundFiles.selectedItems():
                if file.text() in [self.groupFiles.item(i).text() for i in range(self.groupFiles.count())]:
                    self.feedback('{} already added.\n'.format(file.text()))
                else:
                    self.groupFiles.addItem(file.text())
        elif caller == 'Remove':
            for file in self.groupFiles.selectedItems():
                self.groupFiles.takeItem(self.groupFiles.row(file))

    def edit_source_files(self):
        try:
            item = self.importedGroups.selectedItems()[0]
            if item:
                if self.groupFiles.count():
                    if self.popup('Abandon unimported group?') == QMessageBox.Ok:
                         self.groupFiles.clear()
                    else:
                        return
                self.importedGroups.takeItem(self.importedGroups.row(item))
                group = self.groups[item.text()]
                self.groupName.setText(group.name)
                self.groupFiles.addItems(group.source_files)
        except IndexError:
            pass

    def set_preferences(self):
        #TBI Preferences window to set import preferences
        pass

    def import_group(self):

        def combine_files(pathlist, skiprows=None, header_row=0, ts_col=None, dtf=None):
            """Returns dataframe of concatenated data from all files in filelist using ts_col as the index, renamed 'Timestamp'."""
            dflist = []
            counter = 1
            for file in pathlist:
                mode = 'line' if counter == 1 else 'overwrite'
                self.feedback('Reading files into group \"{}\": ({}/{})'.format(self.groupName.text(), counter, len(pathlist)), mode=mode)
                self.repaint()
                counter += 1
                data = pd.read_csv(file, skiprows=skiprows, header=header_row, encoding='ISO-8859-1', sep=',', engine='python')
                #if verbose: print(file, 'shape info:', data.shape)
                try:
                    try:
                        ts_name = data.columns[ts_col] # try to convert ts_col to its name (if given as int/position)
                    except IndexError:
                        ts_name = ts_col
                    data.set_index(ts_name, inplace=True) # use ts_col as index
                    data.index.names = ['Timestamp'] # rename index 'Timestamp'
                except ValueError:
                    print('Could not find column to use as index. Enter column name (string) or position (int).')
                    raise
                dflist.append(data)
            self.feedback(' ...Done', mode='append')
            df = pd.concat(dflist, axis=0, sort=False)
            # convert pandas date & time column (str) to datetime
            try:
                warnings.filterwarnings('ignore')  # to ignore UserWarning: Discarding nonzero nanoseconds in conversion
                df.index = pd.to_datetime(df.index, format=dtf)
            except ValueError:
                print('\\nERROR: datetime formatting does not correspond to the data format\\n')
                raise
            return df.sort_index()

        name = self.groupName.text()
        loaded_groups = [self.importedGroups.item(i).text() for i in range(self.importedGroups.count())]
        if name == '':
            self.feedback('Group name cannot be empty.')
            return
        elif name in loaded_groups:
            if self.popup('Group \"{}\" already exists. Overwrite?'.format(name)) == QMessageBox.Ok:
                self.importedGroups.takeItem(loaded_groups.index(name))
            else:
                return
        source_files = [self.groupFiles.item(i).text() for i in range(self.groupFiles.count())]  #read groupfiles listview
        if not source_files:
            self.feedback('Group cannot have 0 associated files.')
            return
        source_paths = [self.path_dict[file] for file in source_files]  #path_dict is quasi global, assigned in gather_files
        df = combine_files(source_paths, header_row=0, ts_col='PacketTime', dtf='%Y-%m-%d %H:%M:%S.%f')  # These kwargs are specific to PHI_HK
        # need some error handling here, and subsequent encouragement to check import preferences
        self.groups[name] = Group(name,df,source_files,source_paths)
        self.importedGroups.addItem(name)
        self.groupFiles.clear()
        self.groupName.setText('')

    def delete_group(self):
        try:
            item = self.importedGroups.selectedItems()[0]
            if self.popup('Delete group \"{}\"?'.format(item.text())) == QMessageBox.Ok:
                self.importedGroups.takeItem(self.importedGroups.row(item))
        except IndexError:
            pass
