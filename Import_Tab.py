# -*- coding: utf-8 -*-
"""
Created on Wed May  8 11:22:58 2019

@author: seery
"""
class Import_Tab(QWidget):
    def __init__(self, parent):
        super().__init__()
        self.parent = parent
        self.grid = QGridLayout()
        self.path_dict = {}
        self.dir = os.getcwd()
        self.auto_parse = True

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
        self.groupName = QLineEdit('Test')  # delete initial text later
        self.groupName.setPlaceholderText('Group Name')
        self.autoParseCheck = QCheckBox('Automatically parse units from headers')
        self.autoParseCheck.setChecked(True)
        self.autoParseCheck.stateChanged.connect(self.toggle_auto_parse)
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
        self.editGroup = QPushButton('Rename Group')
        self.editGroup.clicked.connect(self.rename_group)
        self.importSettings = QPushButton('Import Settings')
        self.importSettings.clicked.connect(self.open_import_settings)
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
                self.autoParseCheck,
                foundFilesLabel,
                groupFilesLabel,
                importedGroupsLabel,
                self.foundFiles,
                self.groupFiles,
                self.importedGroups,
                self.add,
                self.remove,
                self.editGroup,
                self.importSettings,
                self.importGroup,
                self.deleteGroup,
                ]
        positions = [
                (0,0,1,1),
                (0,1,1,3),
#                (0,3,1,1),
                (1,1,1,1),
                (1,2,1,1),
                (1,3,1,1),
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


    def toggle_auto_parse(self):
        self.auto_parse = self.autoParseCheck.isChecked()

    def search_dir(self):

        def gather_files(path):
            """Returns list of file names in directory path which match types in filetypes.
            Excludes temporary files.
            Does not search subfolders.
            Also returns dictionary associating files to their source paths."""
            found_files = []
            path_dict = {}
            filetypes = re.compile(r'(csv|zip|txt|xls|xlsx)$')
            exclude = re.compile(r'^~\$')
            for file in os.listdir(path):
                if re.search(filetypes, file) and not re.search(exclude, file):
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
        TG = self.parent.parent
        for file in self.path_dict:
            if file not in TG.path_kwargs:
                TG.path_kwargs[self.path_dict[file]] = {'header':'Auto', 'index_col':'Auto', 'skiprows':None}

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

    def rename_group(self):
        DM = self.parent
        try:
            item = self.importedGroups.selectedItems()[0]
            group = item.text()
            new_name, ok = QInputDialog.getText(self, 'Rename Group \"{}\"'.format(group), 'New group name:')
            if ok:
                DM.groups[new_name] = DM.groups[group]
                del DM.groups[group]
                for name in DM.group_reassign:
                    if group == name or group in DM.group_reassign[name]:
                        DM.group_reassign[name].append(new_name)
                        break
                i = self.importedGroups.row(item)
                self.importedGroups.takeItem(i)
                self.importedGroups.insertItem(i, QListWidgetItem(new_name))
                i = DM.dataframes_tab.selectGroup.findText(group)
                DM.dataframes_tab.selectGroup.removeItem(i)
                DM.dataframes_tab.selectGroup.insertItem(i, new_name)
                i = DM.configure_tab.selectGroup.findText(group)
                DM.configure_tab.selectGroup.removeItem(DM.configure_tab.selectGroup.findText(group))
                DM.configure_tab.selectGroup.insertItem(i, new_name)
                DM.modified = True
        except IndexError:
            pass

    def open_import_settings(self):
        self.settingsDialog = Import_Settings(self)
        self.settingsDialog.setModal(True)
        self.settingsDialog.show()

    def parse_df_origin(self, path, read_func):
        """Searches through first 10 rows for the first datetime and returns the cell above it as label origin."""
        nrows = 10
        n = 1
        while n <= nrows:  # avoid asking for more rows than there are
            try:
                df = read_func(path, nrows=n, header=None)
                n += 1
            except IndexError:
                if 'df' not in locals(): df = pd.DataFrame()
                break

        for c in range(len(df.columns)):
            for r in range(len(df.index)):
                try:
                    ts0 = pd.to_datetime(df.iloc[r,c], infer_datetime_format=True)
                    if ts0 is not pd.NaT:
                        if not r:  # if first row is parseable, inconclusive
                            r = None
                        else:  # else return cell above first parseable cell
                            r = r-1
                        return df, r, c
                except ValueError:
                    pass
        return df, None, None

    def import_group(self):

        def floatify(data):
            """Strip everything but numbers, minus signs, and decimals, and returns data as a float. Returns NaN if not possible. Try to convert booleans to 1/0."""
            if str(data).lower() in ('on','true','yes','enabled'): return 1.0
            if str(data).lower() in ('off','false','no','disabled'): return 0.0
            try:
                scrubbed = re.sub('[^0-9-.]', '', str(data))
                scrubbed = re.sub(',', '.', scrubbed)  # allow for German-style decimals (1,2 -> 1.2 but 1,2 -> 1.2. will still fail appropriately)
                return float(scrubbed)
            except ValueError:
                return np.nan

        def parse_unit(header):
            regex = re.compile('(\[|\()([a-z]|[A-Z])*(\]|\))')  # matches [letters] or (letters) anywhere in header
            parsed = None
            for parsed in re.finditer(regex, header):  # parsed ends up as last match
                pass
            if parsed:
                parsed = parsed.group(0)[1:-1]  # return parsed unit without the brackets
                if parsed in DM.parent.unit_clarify:
                    parsed = DM.parent.unit_clarify[parsed]
                if DM.parent.get_unit_type(parsed) is not None:
                    return parsed
            return None

        def combine_files(pathlist):
            dflist = []
            counter = 1
            for path in pathlist:
                mode = 'line' if counter == 1 else 'overwrite'
                DM.feedback('Reading files into group \"{}\": ({}/{}) ... '.format(self.groupName.text(), counter, len(pathlist)), mode=mode)
                DM.messageLog.repaint()
                counter += 1

                # Get parse kwargs associated with file
                kwargs = {}
                parse_kwargs = TG.path_kwargs[path]
                kwargs.update(parse_kwargs)
                if path.endswith('xls') or path.endswith('xlsx'):
                    read_func = pd.read_excel
                elif path.endswith('csv') or path.endswith('zip'):
                    read_func = pd.read_csv
                    kwargs.update({'encoding':'ISO-8859-1', 'sep':',', 'engine':'python'})

                # Take header_row and index_col as intersecting cell above first parseable datetime
                warnings.filterwarnings('ignore')  # to ignore UserWarning: Discarding nonzero nanoseconds in conversion
                _, kwargs['header'], kwargs['index_col'] = self.parse_df_origin(path, read_func)

                # Override header_row and index_col if not set to 'Auto'
                if parse_kwargs['header'] != 'Auto': kwargs['header'] = parse_kwargs['header']
                if parse_kwargs['index_col'] != 'Auto': kwargs['index_col'] = parse_kwargs['index_col']
                kwargs['skiprows'] = parse_kwargs['skiprows']

                try:
                    if kwargs['header'] is None: raise ValueError('Auto parser could not find a header row. Check import settings.')  # don't let the user try to read a file with no header row
                    if kwargs['index_col'] is None: raise ValueError('Auto parser could not find an index column. Check import settings.')  # don't let the user try to read a file without declaring an index column
                    data = read_func(path, **kwargs)
                    data.index.names = ['Timestamp']
                    data.index = pd.to_datetime(data.index, infer_datetime_format=True)
                    if any(ts == pd.NaT for ts in data.index): raise ValueError('Timestamps could not be parsed from given index column. Check import settings.')
                    dflist.append(data)
                except ValueError as e:
                    for file in self.path_dict:
                        if self.path_dict[file] == path: source = file
                    if 'source' not in locals(): source = path
                    DM.feedback('File "\{}\" threw an error: {}'.format(source, e))
                    return pd.DataFrame()
                TG.path_kwargs[path].update(kwargs)

            DM.feedback('Done', mode='append')
            df = pd.concat(dflist, axis=0, sort=False)
            df = df.applymap(floatify)
            return df.sort_index()

        ### Beginning of actions
        DM = self.parent
        TG = DM.parent
        group = self.groupName.text()
        loaded_groups = [self.importedGroups.item(i).text() for i in range(self.importedGroups.count())]

        # Use case filtering
        if group == '':
            DM.feedback('Group name cannot be empty.')
            return
        elif group in loaded_groups:
            if DM.popup('Group \"{}\" already exists. Overwrite?'.format(group)) == QMessageBox.Ok:
                self.importedGroups.takeItem(loaded_groups.index(group))
            else:
                return
        source_files = [self.groupFiles.item(i).text() for i in range(self.groupFiles.count())]  #read groupfiles listview
        if not source_files:
            DM.feedback('Group cannot have 0 associated files.')
            return
        source_paths = [self.path_dict[file] for file in source_files]  #path_dict is quasi global, appended gather_files (therefore, navigating to a different directory should not disconnect files from paths)
        df = combine_files(source_paths)#, header_row=0, ts_col='PacketTime', dtf='%Y-%m-%d %H:%M:%S.%f')  # These kwargs are specific to PHI_HK

        if not df.empty:
            DM.groups[group] = Group(df, source_files, source_paths)  # this is writing to Data_Manager's version, not TG's
            self.importedGroups.addItem(group)

            # Try to auto parse units
            parse_error_log = []
            if self.auto_parse:
                for header in DM.groups[group].series:
                    parsed = parse_unit(header)
                    DM.groups[group].series[header].unit = parsed
                    if parsed is None:
                        parse_error_log.append(header)  # parse_error_log formerly associated headers with their source files, but this has been removed because you can just look at the data in the DataFrames tab to figure out what the unit should be in the event of parse failure
            if parse_error_log:
                report = ''
                for header in parse_error_log:
                    report += header+'\n'
                DM.popup('Unit Parse Failure',
                         informative='Unable to parse units from the following headers. See Configure tab to manually assign units.',
                         details=report,
                         buttons=1)

            # Update other tabs but don't trigger table filling
            for combo in [DM.dataframes_tab.selectGroup, DM.configure_tab.selectGroup]:
                combo.blockSignals(True)
                combo.addItem(group)
                combo.blockSignals(False)

            self.groupFiles.clear()
            self.groupName.setText('')
            DM.modified = True


    def delete_group(self):
        DM = self.parent
        try:
            item = self.importedGroups.selectedItems()[0]
            group = item.text()
            if DM.popup('Delete group \"{}\"?'.format(group)) == QMessageBox.Ok:
                self.importedGroups.takeItem(self.importedGroups.row(item))
                del DM.groups[group]
                if group in DM.group_reassign: del DM.group_reassign[group]
                DM.dataframes_tab.selectGroup.removeItem(DM.dataframes_tab.selectGroup.findText(group))
                DM.configure_tab.selectGroup.removeItem(DM.configure_tab.selectGroup.findText(group))
        except IndexError:
            pass
        DM.modified = True  # ok if you make one and then delete it, it still thinks something's changed but WHATEVER
