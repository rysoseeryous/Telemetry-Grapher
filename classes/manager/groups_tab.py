# -*- coding: utf-8 -*-
"""
Created on Thu Jun 13 15:49:53 2019

@author: seery
"""
import os
import re
import datetime as dt
import pandas as pd
import numpy as np

from PyQt5.QtWidgets import (QWidget, QMessageBox, QFileDialog, QInputDialog,
                             QGridLayout, QHBoxLayout, QVBoxLayout, QStyle,
                             QPushButton, QLabel, QLineEdit,
                             QListWidget, QListWidgetItem)

from .import_settings import Import_Settings
from ..internal.group import Group

class Groups_Tab(QWidget):
    """UI for organizing source files into groups."""

    def __init__(self, parent):
        super().__init__()
        self.parent = parent
        DM = self.parent
        self.importsettings = QWidget()

        self.path_dict = {}
        self.df_preview = {}
        self.dir = os.getcwd()

        vbox = QVBoxLayout()
        hbox = QHBoxLayout()
        self.browse = QPushButton()
        self.browse.setIcon(self.style().standardIcon(getattr(QStyle, 'SP_DialogOpenButton')))
        self.browse.clicked.connect(self.browse_dialog)
        hbox.addWidget(self.browse)
        self.directory = QLineEdit(self.dir)
        self.directory.returnPressed.connect(self.search_dir)
        hbox.addWidget(self.directory)
        vbox.addLayout(hbox)

        grid = QGridLayout()

        self.fileSearch = QLineEdit()
        self.fileSearch.setPlaceholderText('Search')
        self.fileSearch.textChanged.connect(self.filter_files)
        self.fileSearch.setFocus(True)
        grid.addWidget(self.fileSearch, 0, 0)

        self.groupName = QLineEdit('Test')  # delete initial text later #!!!
        self.groupName.setPlaceholderText('Group Name')
        self.groupName.returnPressed.connect(self.import_group)
        grid.addWidget(self.groupName, 0, 1)

        self.importGroup = QPushButton('Import Group')
        self.importGroup.clicked.connect(self.import_group)
        self.importGroup.setDefault(True)
        grid.addWidget(self.importGroup, 0, 2)

        foundFilesLabel = QLabel('Found Files')
        grid.addWidget(foundFilesLabel, 1, 0)

        groupFilesLabel = QLabel('Files in Group')
        grid.addWidget(groupFilesLabel, 1, 1)

        importedGroupsLabel = QLabel('Imported Groups')
        grid.addWidget(importedGroupsLabel, 1, 2)

        self.foundFiles = QListWidget()
        self.foundFiles.setSelectionMode(QListWidget.ExtendedSelection)
        grid.addWidget(self.foundFiles, 2, 0)

        self.groupFiles = QListWidget()
        self.groupFiles.setSelectionMode(QListWidget.ExtendedSelection)
        grid.addWidget(self.groupFiles, 2, 1)

        self.importedGroups = QListWidget()
        self.importedGroups.addItems(DM.groups.keys())
        self.importedGroups.itemDoubleClicked.connect(self.rename_group)
        grid.addWidget(self.importedGroups, 2, 2)

        self.add = QPushButton('Add to Group')
        self.add.clicked.connect(lambda: self.toggle_file_active('Add'))
        grid.addWidget(self.add, 3, 0)

        self.remove = QPushButton('Remove from Group')
        self.remove.clicked.connect(lambda: self.toggle_file_active('Remove'))
        grid.addWidget(self.remove, 3, 1)

        self.deleteGroup = QPushButton('Delete Group')
        self.deleteGroup.clicked.connect(self.delete_group)
        grid.addWidget(self.deleteGroup, 3, 2)

        vbox.addLayout(grid)
        self.setLayout(vbox)

    def interpret_data(self, path, read_func=pd.read_csv):
        dtf = 'Infer'
        r, c = self.parse_df_origin(path, read_func)
        skiprows = None
        return dtf, r, c, skiprows

    def search_dir(self):
        """Searches current directory and displays found files.
        Newly found files are given an entry with default values in a dictionary associating filepaths and reading kwargs."""
        path = self.directory.text()
        self.dir = path
        try:
            self.loaded_files, new_path_dict_entries = self.gather_files(path)
            self.path_dict.update(new_path_dict_entries)
            self.fileSearch.setText('')
            self.foundFiles.clear()
            self.foundFiles.addItems(self.loaded_files)
        except FileNotFoundError:
            DM = self.parent
            DM.feedback('{} is not a valid path.'.format(path))

    def browse_dialog(self):
        """Opens a file dialog to select a working directory and displays found files."""
        path = str(QFileDialog.getExistingDirectory(self, "Select Directory"))
        if path:
            self.directory.setText(path)
            self.search_dir()

    def gather_files(self, path):
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

    def filter_files(self):
        """Displays files in found files list which match searchbar input."""
        DM = self.parent
        pattern = re.compile(self.fileSearch.text(), re.IGNORECASE)
        matches = [item for item in DM.groups_tab.loaded_files if re.search(pattern,item)]
        self.foundFiles.clear()
        self.foundFiles.addItems(matches)

    def toggle_file_active(self, caller):
        """Transfers file to or from group file list."""
        DM = self.parent
        if caller == 'Add':
            for file in self.foundFiles.selectedItems():
                if file.text() in [self.groupFiles.item(i).text() for i in range(self.groupFiles.count())]:
                    DM.feedback('{} already added'.format(file.text()))
                else:
                    self.groupFiles.addItem(file.text())
        elif caller == 'Remove':
            for file in self.groupFiles.selectedItems():
                self.groupFiles.takeItem(self.groupFiles.row(file))

    def rename_group(self, item):
        """Renames imported group.
        Keeps track of past renaming operations so Data Manager's save changes can identify existing groups as having been renamed.
        Accessible by double clicking on an imported group."""
        DM = self.parent
        try:
            group_name = item.text()
            new_name, ok = QInputDialog.getText(self, 'Rename Group "{}"'.format(group_name), 'New group name:', QLineEdit.Normal, group_name)
            if ok and new_name != group_name:
                if new_name in DM.groups:
                    DM.feedback('Group "{}" already exists. Please choose a different name.'.format(new_name))
                else:
                    # Create new entry in DM.groups with new_name, give it old group's info, scrap the old one
                    DM.groups[new_name] = DM.groups[group_name]
                    del DM.groups[group_name]
                    # Append new name list of renames
                    # DM.group_reassign looks like {AB name: [AB name, rename1, rename2... DM name]}
                    for name in DM.group_reassign:
                        if group_name == DM.group_reassign[name][-1]:
                            DM.group_reassign[name].append(new_name)
                            break
                    i = self.importedGroups.row(item)
                    self.importedGroups.takeItem(i)
                    self.importedGroups.insertItem(i, QListWidgetItem(new_name))
                    i = DM.configure_tab.selectGroup.findText(group_name)
                    DM.configure_tab.selectGroup.blockSignals(True)
                    DM.configure_tab.selectGroup.removeItem(DM.configure_tab.selectGroup.findText(group_name))
                    DM.configure_tab.selectGroup.blockSignals(False)
                    DM.configure_tab.selectGroup.insertItem(i, new_name)
                    DM.modified = True
        except IndexError as e:
            print(e)

    def parse_df_origin(self, path, read_func, nrows=20):
        """Tries to identify the cell at which the header row and index column intersect.
        - Loop through the first 20 rows of each column.
        - If cell can be parsed as a datetime, return coordinates of cell directly above.
        - If no cells can be parsed, return Nones."""
        n = 1
        while n <= nrows:  # avoid asking for more rows than there are
            try:
                df = read_func(path, nrows=n, header=None, encoding='latin1')
                n += 1
            except IndexError:
                if 'df' not in locals(): df = pd.DataFrame()
                break

        for c in range(len(df.columns)):
            for r in range(len(df.index)):
                try:
                    ts0 = pd.to_datetime(df.iloc[r, c], infer_datetime_format=True)
                    if ts0 is not pd.NaT:
                        if not r:  # if first row is parseable, inconclusive
                            r = None
                        else:  # else return cell above first parseable cell
                            r = r-1
                        return r, c
                except ValueError:
                    pass
        return None, 0

    def floatify(self, data):
        """Strips data down to float.
        - Try to return data as float.
        - If not possible, try to interpret data as quasi-boolean and return 1.0 or 0.0.
        - If not quasi-boolean, scrub away everything but numbers, minus signs, and decimals and return as float.
        - Return NaN if all other attempts fail."""
        try:
            return float(data)  # try returning data as float as-is. Should speed things up.
        except (ValueError, TypeError):
            if str(data).lower() in ('on','true','yes','enabled'): return 1.0
            if str(data).lower() in ('off','false','no','disabled'): return 0.0
            try:
                scrubbed = re.sub(',', '.', str(data))  # allow for German-style decimals (1,2 -> 1.2 but 1,2, -> 1.2. will still fail appropriately)
                scrubbed = re.sub('[^0-9-.]', '', scrubbed)
                return float(scrubbed)
            except ValueError:
                return np.nan

    def combine_files(self, pathlist):
        DM = self.parent
        AB = DM.parent
        dflist = []
        counter = 1
        for path in pathlist:
            mode = 'line' if counter == 1 else 'overwrite'
            DM.feedback('Reading files into group "{}": ({}/{})... '.format(self.groupName.text(), counter, len(pathlist)), mode=mode)
            DM.messageLog.repaint()
            counter += 1

            # Get parse kwargs associated with file
            path_kwargs = {'encoding':'latin1'}  # just load the dang file as-is
            path_kwargs.update(AB.path_kwargs[path])

            #this is kinda sloppy
            del path_kwargs['format']  # because it gets used somewhere else but comes from the same dictionary
            if AB.path_kwargs[path]['format'].lower() == 'infer':
                dtf = None
            else:
                dtf = AB.path_kwargs[path]['format']

#            if path.endswith('xls') or path.endswith('xlsx'):
#                read_func = pd.read_excel
##                    path_kwargs.update({'sheet_name':None})  # read all sheets
#            elif path.endswith('csv') or path.endswith('zip'):
#                read_func = pd.read_csv

            try:
                # Sunrise Test.csv: 2009-06-06 14:49:01.000
                # dtf = %Y-%m-%d %H:%M:%S.%f

                start = dt.datetime.now()
                data = pd.read_csv(path, **path_kwargs)
                data.index.names = ['Timestamp']
                data.columns = data.columns.map(str)  # convert headers to strings
                data.index = pd.to_datetime(data.index, infer_datetime_format=True, format=dtf)
                end = dt.datetime.now()
                # This error has never been thrown
                if any(ts == pd.NaT for ts in data.index): raise ValueError('Timestamps could not be parsed from given index column. Check import settings.')

                dflist.append(data)
            except ValueError as e:
                for file in DM.groups_tab.path_dict:
                    if DM.groups_tab.path_dict[file] == path: source = file
                if 'source' not in locals(): source = path
                DM.feedback('Failed', mode='append')
                DM.feedback('File "{}" threw an error: {}'.format(source, e))
                return pd.DataFrame()
            AB.path_kwargs[path].update(path_kwargs)

        df = pd.concat(dflist, axis=0, sort=False)
        DM.feedback('Scrubbing data... ', mode='append')
        DM.messageLog.repaint()
        df = df.applymap(self.floatify)
        DM.feedback('Done', mode='append')
        return df.sort_index()

    def import_group(self):
        DM = self.parent
        AB = DM.parent
        group_name = self.groupName.text()
        loaded_groups = [self.importedGroups.item(i).text() for i in range(self.importedGroups.count())]

        # Use case filtering
        if group_name == '':
            DM.feedback('Group name cannot be empty.')
            return
        elif group_name in loaded_groups:
            if AB.popup('Group "{}" already exists. Overwrite?'.format(group_name), title='Importing Group', mode='confirm') == QMessageBox.Ok:
                self.importedGroups.takeItem(loaded_groups.index(group_name))
                #??? If group_name is a renaming of a previously loaded group, is that bad?
            else:
                return
        source_files = [self.groupFiles.item(i).text() for i in range(self.groupFiles.count())]  #read groupfiles listview
        if not source_files:
            DM.feedback('Group cannot have 0 associated files.')
            return

        if self.verify_import_settings(source_files):#result == QDialog.Accepted:
            source_paths = [self.path_dict[file] for file in source_files]  #path_dict is quasi global, appended gather_files (therefore, navigating to a different directory should not disconnect files from paths)
            df = self.combine_files(source_paths)#, header_row=0, ts_col='PacketTime', dtf='%Y-%m-%d %H:%M:%S.%f')  # These kwargs are specific to PHI_HK

            if not df.empty:
                DM.groups[group_name] = Group(df, source_files, source_paths)  # this is writing to Data_Manager's version, not AB's
                self.importedGroups.addItem(group_name)

                # Try to auto parse units
                if AB.auto_parse:
                    self.parse_series(DM.groups[group_name], DM.groups[group_name].series.keys())

                DM.configure_tab.selectGroup.addItem(group_name)  # -> this emits a signal to call CT's display_header_info function
                self.groupFiles.clear()
                self.groupName.setText('')
                DM.modified = True
        else:
            DM.feedback('Import canceled.', mode='append')

    def verify_import_settings(self, source_files):
        DM = self.parent
        AB = DM.parent
        counter = 1
        for file in source_files:
            mode = 'line' if counter == 1 else 'overwrite'
            DM.feedback('Loading previews: ({}/{})... '.format(counter, len(source_files)), mode=mode)
            DM.messageLog.repaint()
            counter += 1

            if file not in AB.path_kwargs:
                if file.endswith('xls') or file.endswith('xlsx'):
                    read_func = pd.read_excel
                elif file.endswith('csv') or file.endswith('zip'):
                    read_func = pd.read_csv

                path = self.path_dict[file]

                # Read first column and take its length so you can read head and tail later without loading the whole DF into memory
                shownRows = 20
                n = len(read_func(path, usecols=[0], header=None, encoding='latin1').index)

                if n > shownRows:
                    upper_df = read_func(path, nrows=shownRows//2, header=None, encoding='latin1')
                    lower_df = read_func(path, skiprows=range(n-shownRows//2), header=None, encoding='latin1')
                    ellipses = pd.DataFrame(['...']*len(upper_df.columns),
                                            index=upper_df.columns,
                                            columns=['...']).T
                    shown_df = upper_df.append(ellipses).append(lower_df)
                else:
                    shown_df = read_func(path, header=None, encoding='latin1')
                self.df_preview[path] = shown_df
                dtf, r, c, skiprows = self.interpret_data(path, read_func)
                AB.path_kwargs[self.path_dict[file]] = {'format':dtf, 'header':r, 'index_col':c, 'skiprows':skiprows}
        DM.feedback('Verify import settings... ', mode='append')
        DM.messageLog.repaint()
        self.importsettings = Import_Settings(self, source_files)
        self.importsettings.setModal(True)
        return self.importsettings.exec()

    def parse_series(self, group, headers):
        DM = self.parent
        AB = DM.parent
        report = ''
        for header in headers:
            parsed = AB.parse_unit(header)
            unit, interpreted = AB.interpret_unit(parsed)
            group.series[header].unit = unit
            group.series[header].unit_type = AB.get_unit_type(unit)
            if not interpreted:
                report += header + '\n'
            else:
                alias = re.sub('\[{}\]'.format(parsed), '', header).strip()
                group.series[header].alias = alias
                group.alias_dict[alias] = header
        if report:
            AB.popup('Some units not assigned.',
                     title='Unit Parse Error Log',
                     informative='You can assign units manually under Series Configuration, leave them blank, or adjust unit settings and reparse.',
                     details=report,
                     icon=False,
                     mode='alert')

    def delete_group(self):
        DM = self.parent
        AB = DM.parent
        try:
            item = self.importedGroups.selectedItems()[0]
            group_name = item.text()
            if AB.popup('Delete group "{}"?'.format(group_name), mode='confirm') == QMessageBox.Ok:
                self.importedGroups.takeItem(self.importedGroups.row(item))
                del DM.groups[group_name]

                # delete the corresponding entry in group_reassign (if it exists)
                for name in DM.group_reassign:
                    if group_name == DM.group_reassign[name][-1]:
                        del DM.group_reassign[name]
                        DM.modified = True  # only modified if the deleted group was loaded into AB
                        break
                DM.configure_tab.selectGroup.removeItem(DM.configure_tab.selectGroup.findText(group_name))
        except IndexError as e:
            print(e)