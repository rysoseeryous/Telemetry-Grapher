# -*- coding: utf-8 -*-
"""
Created on Wed May  8 11:22:58 2019

@author: seery
"""
from PyQt5.QtWidgets import *

class Import_Tab(QWidget):
    def __init__(self, parent):
        super().__init__()
        self.parent = parent
        self.grid = QGridLayout()
        self.path_dict = {}
        self.dir = os.getcwd()
#        self.dir = r'C:\Users\seery\Documents\German (the person)\PHI_data_housekeeping\CSV'  # delete later, just for quicker access

#        dirLabel = QLabel('Directory:')
        self.browse = QPushButton()
        self.browse.setIcon(self.style().standardIcon(getattr(QStyle, 'SP_DialogOpenButton')))
        self.browse.clicked.connect(self.browse_dialog)
        self.directory = QLineEdit(self.dir)
        self.directory.returnPressed.connect(self.search_dir)
        self.fileSearch = QLineEdit()
        self.fileSearch.setPlaceholderText('Search')
        self.fileSearch.textChanged.connect(self.filter_files)
        self.fileSearch.setFocus(True)
        self.groupName = QLineEdit('Test')  # delete this later
        self.groupName.setPlaceholderText('Group Name')
        foundFilesLabel = QLabel('Found Files')
        groupFilesLabel = QLabel('Files in Group')
        importedGroupsLabel = QLabel('Imported Groups')
        self.foundFiles = QListWidget()
        self.foundFiles.setSelectionMode(QListWidget.ExtendedSelection)
        self.groupFiles = QListWidget()
        self.groupFiles.setSelectionMode(QListWidget.ExtendedSelection)
        self.importedGroups = QListWidget()
        self.importedGroups.addItems(self.parent.groups.keys())
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


        #row_weights = [1, 1, 1, 1, 1, 1]
        #for i,rw in enumerate(row_weights):
        #    self.import_tab.grid.setRowStretch(i,rw)
        #col_weights = [1, 1, 1, 1, 1, 1]
        #for i,cw in enumerate(col_weights):
        #    self.import_tab.grid.setColumnStretch(i,cw)

        widgets = [
#                dirLabel,
                self.browse,
                self.directory,
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
                ]
        positions = [
                (0,0,1,1),
                (0,1,1,3),
#                (0,3,1,1),
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
                ]

        for w, p in zip(widgets, positions):
            self.grid.addWidget(w, *p)
        self.setLayout(self.grid)
        self.search_dir()




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
                    DM.feedback('{} already added.\n'.format(file.text()))
                else:
                    self.groupFiles.addItem(file.text())
        elif caller == 'Remove':
            for file in self.groupFiles.selectedItems():
                self.groupFiles.takeItem(self.groupFiles.row(file))

    def edit_source_files(self):
        """Shows source files of selected group but doesn't un-import. Click "Import Group" and overwrite to save edits."""
        try:
            item = self.importedGroups.selectedItems()[0]
            if self.groupFiles.count():
                if DM.popup('Abandon unimported group?') == QMessageBox.Ok:
                     self.groupFiles.clear()
                else:
                    return
#            self.importedGroups.takeItem(self.importedGroups.row(item))
            DM.configure_tab.selectGroup.removeItem(DM.configure_tab.selectGroup.findText(item.text()))
            group = DM.groups[item.text()]
            self.groupName.setText(item.text())
            self.groupFiles.addItems(group.source_files)
        except IndexError:
            pass

    def set_preferences(self):
        #TBI Preferences window to set import preferences
        pass

    def import_group(self):

        def floatify(data):
            """Strip everything but numbers, minus signs, and decimals, and returns data as a float. Returns NaN if not possible. Try to convert booleans to 1/0."""
            if str(data).lower() in ('on','true','yes','enabled'): return 1.0
            if str(data).lower() in ('off','false','no','disabled'): return 0.0
            try:
                return float(re.sub('[^0-9-.]', '', str(data)))
            except ValueError:
                return np.nan

        def parse_unit(header):
            regex = re.compile('\[([a-z]|[A-Z])*\]')  # returns match if something like [letters] anywhere in header
            parsed = re.search(regex, header)
            if parsed:
                parsed = parsed.group(0)[1:-1]  # return parsed unit without the brackets
                if parsed in DM.parent.unit_clarify:
                    parsed = DM.parent.unit_clarify[parsed]
                if (DM.parent.get_unit_type(parsed) is not None):
                    return parsed
            return None
            # feedback to message log: 'Unable to parse unit from header \"{}\" in file \"{}\". See Unit Settings in Configure tab.
            # pop up saying:
            # 'Unit could not be parsed from header \"{}\". You can assign one yourself here, or click cancel to leave it blank. See Unit Settings in Configure tab to append unit database'.format(header)
            # combo box for unit type, label updates with default unit.

        def combine_files(pathlist):
            dflist = []
            series_units = {}
            parse_error_log = {}
            for file in pathlist:
                data = pd.read_excel(file, index_col=0)
                data.index.names = ['Timestamp']
                units = []
                for header in data.columns:
                    parsed = parse_unit(header)
                    units.append(parsed)
                    if parsed is None:
                        if file in parse_error_log:
                            parse_error_log[file].append(header)
                        else:
                            parse_error_log[file] = [header]
                series_units.update(dict(zip(data.columns, units)))
                dflist.append(data)
            df = pd.concat(dflist, axis=0, sort=False)
            try:
                warnings.filterwarnings('ignore')  # to ignore UserWarning: Discarding nonzero nanoseconds in conversion
                df.index = pd.to_datetime(df.index, format='%Y-%m-%d %H:%M:%S.%f')
            except ValueError:
                print('\\nERROR: datetime formatting does not correspond to the data format\\n')
                raise
            return df, series_units, parse_error_log
### CURRENTLY FUNCTIONAL ONLY FOR PHI_HK DATA
#        def combine_files(pathlist, skiprows=None, header_row=0, ts_col=None, dtf=None):
#            """Returns dataframe of concatenated data from all files in filelist using ts_col as the index, renamed 'Timestamp'."""
#            dflist = []
#            counter = 1
#            for file in pathlist:
#                mode = 'line' if counter == 1 else 'overwrite'
#                DM.feedback('Reading files into group \"{}\": ({}/{}) ... '.format(self.groupName.text(), counter, len(pathlist)), mode=mode)
#                self.repaint()
#                counter += 1
#                data = pd.read_csv(file, skiprows=skiprows, header=header_row, encoding='ISO-8859-1', sep=',', engine='python')
#                #if verbose: print(file, 'shape info:', data.shape)
#                try:
#                    try:
#                        ts_name = data.columns[ts_col] # try to convert ts_col to its name (if given as int/position)
#                    except IndexError:
#                        ts_name = ts_col
#                    data.set_index(ts_name, inplace=True) # use ts_col as index
#                    data.index.names = ['Timestamp'] # rename index 'Timestamp'
#                except ValueError:
#                    print('Could not find column to use as index. Enter column name (string) or position (int).')
#                    raise
#                data = data.applymap(floatify)
#                dflist.append(data)
#            DM.feedback('Done', mode='append')
#            df = pd.concat(dflist, axis=0, sort=False)
#            # convert pandas date & time column (str) to datetime
#            try:
#                warnings.filterwarnings('ignore')  # to ignore UserWarning: Discarding nonzero nanoseconds in conversion
#                df.index = pd.to_datetime(df.index, format=dtf)
#            except ValueError:
#                print('\\nERROR: datetime formatting does not correspond to the data format\\n')
#                raise
#            return df.sort_index()

        ### Beginning of actions
        DM = self.parent

        name = self.groupName.text()
        loaded_groups = [self.importedGroups.item(i).text() for i in range(self.importedGroups.count())]

        # Use case filtering
        if name == '':
            DM.feedback('Group name cannot be empty.')
            return
        elif name in loaded_groups:
            if DM.popup('Group \"{}\" already exists. Overwrite?'.format(name)) == QMessageBox.Ok:
                self.importedGroups.takeItem(loaded_groups.index(name))
            else:
                return
        source_files = [self.groupFiles.item(i).text() for i in range(self.groupFiles.count())]  #read groupfiles listview
        if not source_files:
            DM.feedback('Group cannot have 0 associated files.')
            return
        source_paths = [self.path_dict[file] for file in source_files]  #path_dict is quasi global, appended gather_files (therefore, navigating to a different directory should not disconnect files from paths)
        df, series_units, parse_error_log = combine_files(source_paths)#, header_row=0, ts_col='PacketTime', dtf='%Y-%m-%d %H:%M:%S.%f')  # These kwargs are specific to PHI_HK
        # need some error handling here, and subsequent encouragement to check import preferences
        DM.groups[name] = Group(df, df.columns, source_files, source_paths)  # this is writing to Data_Manager's version, not TG's
        # data_dict assignment
        # Later this should try to parse units from df.columns/group.og_headers
        # if unknown unit found, do the following:
        # You can turn off this setting in Import Settings, but then you have to assign all the units manually
#        units = ['T']*len(df.columns)  # assign all series to Temperature for now
        DM.data_dict[name] = series_units  # this is writing to Data_Manager's version, not TG's

        # future error handling goes here and looks maybe a little like this

        self.importedGroups.addItem(name)

        # Update other tabs
        DM.configure_tab.selectGroup.addItem(name)
        DM.dataframes_tab.selectGroup.addItem(name)

        self.groupFiles.clear()
        self.groupName.setText('')
        DM.modified = True
        if parse_error_log:
            report = ''
            for file in parse_error_log:
                report += file[file.rindex('\\')+1:]+'\n'
                for header in parse_error_log[file]:
                    report += '\t'+header+'\n'
            DM.popup('Unit Parse Failure',
                              informative='''Unable to parse units from the following source files and headers. See Configure tab to manually assign units.''',
                              details=report,
                              buttons=1)

    def delete_group(self):
        DM = self.parent
        try:
            item = self.importedGroups.selectedItems()[0]
            if DM.popup('Delete group \"{}\"?'.format(item.text())) == QMessageBox.Ok:
                self.importedGroups.takeItem(self.importedGroups.row(item))
                del DM.groups[item.text()]
                DM.configure_tab.selectGroup.removeItem(DM.configure_tab.selectGroup.findText(item.text()))
        except IndexError:
            pass
        DM.modified = True  # ok if you make one and then delete it, it still thinks something's changed but WHATEVER
