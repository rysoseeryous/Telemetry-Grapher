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

from PyQt5.QtWidgets import (QWidget, QFileDialog, QInputDialog,
                             QGridLayout, QHBoxLayout, QVBoxLayout, QStyle,
                             QPushButton, QLabel, QLineEdit, QListWidget)
from PyQt5.QtCore import QObject

from .import_settings import ImportSettings
from ..internal.group import Group

class GroupsTab(QWidget):
    """UI for organizing source files into groups."""

    def __init__(self, parent):
        super().__init__()
        self.parent = parent
        dm = self.parent
#        self.importsettings = QWidget()

        self.path_dict = {}
        self.df_preview = {}
        self.dir = os.getcwd()

        vbox = QVBoxLayout()
        hbox = QHBoxLayout()
        self.browse = QPushButton()
        icon = getattr(QStyle, 'SP_DialogOpenButton')
        self.browse.setIcon(self.style().standardIcon(icon))
        self.browse.clicked.connect(self.browse_dialog)
        hbox.addWidget(self.browse)
        self.directory = QLineEdit(self.dir)
        self.directory.returnPressed.connect(self.search_dir)
        hbox.addWidget(self.directory)
        vbox.addLayout(hbox)

        grid = QGridLayout()

        self.file_search = QLineEdit()
        self.file_search.setPlaceholderText('Search')
        self.file_search.textChanged.connect(self.filter_files)
        self.file_search.setFocus(True)
        grid.addWidget(self.file_search, 0, 0)

        self.group_name = QLineEdit('Test')  # delete initial text later #!!!
        self.group_name.setPlaceholderText('Group Name')
        self.group_name.returnPressed.connect(self.import_group)
        grid.addWidget(self.group_name, 0, 1)

        self.import_button = QPushButton('Import Group')
        self.import_button.clicked.connect(self.import_group)
        self.import_button.setDefault(True)
        grid.addWidget(self.import_button, 0, 2)

        grid.addWidget(QLabel('Found Files'), 1, 0)

        grid.addWidget(QLabel('Files in Group'), 1, 1)

        grid.addWidget(QLabel('Imported Groups'), 1, 2)

        self.found_files = QListWidget()
        self.found_files.setSelectionMode(QListWidget.ExtendedSelection)
        grid.addWidget(self.found_files, 2, 0)

        self.group_files = QListWidget()
        self.group_files.setSelectionMode(QListWidget.ExtendedSelection)
        grid.addWidget(self.group_files, 2, 1)

        self.imported_groups = QListWidget()
        self.imported_groups.addItems(dm.groups.keys())
        self.imported_groups.itemDoubleClicked.connect(self.rename_group)
        grid.addWidget(self.imported_groups, 2, 2)

        self.add = QPushButton('Add to Group')
        self.add.clicked.connect(self.toggle_file_active)
        grid.addWidget(self.add, 3, 0)

        self.remove = QPushButton('Remove from Group')
        self.remove.clicked.connect(self.toggle_file_active)
        grid.addWidget(self.remove, 3, 1)

        self.delete = QPushButton('Delete Group')
        self.delete.clicked.connect(self.delete_group)
        grid.addWidget(self.delete, 3, 2)

        vbox.addLayout(grid)
        self.setLayout(vbox)

    def interpret_data(self, path):
        dtf = 'Infer'
        r, c = self.parse_df_origin(path)
        skiprows = None
        return dtf, r, c, skiprows

    def search_dir(self):
        """Searches current directory and displays found files.
        Newly found files are given an entry with default values in a
        dictionary associating filepaths and reading kwargs."""
        path = self.directory.text()
        self.dir = path
        try:
            self.loaded_files, new_path_dict_entries = self.gather_files(path)
            self.path_dict.update(new_path_dict_entries)
            self.file_search.setText('')
            self.found_files.clear()
            self.found_files.addItems(self.loaded_files)
        except FileNotFoundError:
            dm = self.parent
            dm.feedback('{} is not a valid path.'.format(path))

    def browse_dialog(self):
        """Opens a file dialog to select a working directory."""
        path = str(QFileDialog.getExistingDirectory(self, "Select Directory"))
        if path:
            self.directory.setText(path)
            self.search_dir()

    def gather_files(self, path):
        """Returns list of csv file names in directory path.
        Excludes temporary files.
        Does not search subfolders.
        Also returns dictionary associating files to their source paths."""
        found_files = []
        path_dict = {}
        filetypes = re.compile(r'(csv|zip)$')
        exclude = re.compile(r'^~\$')
        for file in os.listdir(path):
            if re.search(filetypes, file) and not re.search(exclude, file):
                found_files.append(file)
                path_dict[file] = os.path.join(path, file)
        return found_files, path_dict

    def filter_files(self):
        """Displays files in found files list which match searchbar input."""
        dm = self.parent
        pattern = re.compile(self.file_search.text(), re.IGNORECASE)
        matches = [item for item in dm.groups_tab.loaded_files
                   if re.search(pattern,item)]
        self.found_files.clear()
        self.found_files.addItems(matches)

    def toggle_file_active(self):
        """Transfers file to or from group file list."""
        dm = self.parent
        if QObject.sender(self) == self.add:
            for file in self.found_files.selectedItems():
                w = self.group_files
                if file.text() in [w.item(i).text() for i in range(w.count())]:
                    dm.feedback('{} already added'.format(file.text()))
                else:
                    self.group_files.addItem(file.text())
        if QObject.sender(self) == self.remove:
            for file in self.group_files.selectedItems():
                self.group_files.takeItem(self.group_files.row(file))

    def rename_group(self, item):
        """Renames imported group.
        Keeps track of past renaming operations so Data Manager's save changes
        can identify existing groups as having been renamed.
        Accessible by double clicking on an imported group."""
        dm = self.parent
        try:
            group_name = item.text()
            new_name, ok = QInputDialog.getText(
                    self,
                    'Rename Group "{}"'.format(group_name),
                    'New group name:',
                    QLineEdit.Normal,
                    group_name)
            if ok and new_name != group_name:
                if new_name in dm.groups:
                    dm.feedback('Group "{}" already exists.'
                                'Please choose a different name.'
                                .format(new_name))
                else:
                    dm.groups[new_name] = dm.groups[group_name]
                    del dm.groups[group_name]
                    # Append new name list of renames
                    # dm.group_reassign looks like:
                    # {ui name: [ui name, rename1, rename2... dm name]}
                    for name in dm.group_reassign:
                        if group_name == dm.group_reassign[name][-1]:
                            dm.group_reassign[name].append(new_name)
                            break
                    i = self.imported_groups.row(item)
                    self.imported_groups.takeItem(i)
                    self.imported_groups.insertItem(i, new_name)
                    i = dm.configure_tab.select_group.findText(group_name)
                    dm.configure_tab.select_group.blockSignals(True)
                    dm.configure_tab.select_group.removeItem(i)
                    dm.configure_tab.select_group.blockSignals(False)
                    dm.configure_tab.select_group.insertItem(i, new_name)
                    dm.modified = True
        except IndexError as e:
            print(e)

    def parse_df_origin(self, path, nrows=20):
        """Guesses the intersection of header row and index column.
        - Loop through the first 20 rows of each column.
        - If cell can be parsed as a datetime,
          return coordinates of cell directly above.
        - If no cells can be parsed, return None, 0."""
        n = 1
        while n <= nrows:  # avoid asking for more rows than there are
            try:
                df = pd.read_csv(path, nrows=n, header=None, encoding='latin1')
                n += 1
            except IndexError:
                if 'df' not in locals(): df = pd.DataFrame()
                break

        for c in range(len(df.columns)):
            for r in range(len(df.index)):
                try:
                    ts0 = pd.to_datetime(df.iloc[r, c],
                                         infer_datetime_format=True)
                    if ts0 is not pd.NaT:
                        if not r:  # if first row is parseable, inconclusive
                            return None, c
                        else:  # else return cell above first parseable cell
                            return r-1, c
                except ValueError:
                    pass
        return None, 0

    def floatify(self, data):
        """Strips data down to float.
        - Try to return data as float.
        - If not possible, try to interpret data as 1.0 or 0.0.
        - If not quasi-boolean, scrub away everything but
          numbers, minus signs, and decimals and return as float.
        - Return NaN if all other attempts fail."""
        try:
            return float(data)  # try returning data as float as-is.
        except (ValueError, TypeError):
            if str(data).lower() in ('on','true','yes','enabled'): return 1.0
            if str(data).lower() in ('off','false','no','disabled'): return 0.0
            try:
                # allow for German-style decimals
                # (1,2 -> 1.2 but 1,2, -> 1.2. will still fail appropriately)
                scrubbed = re.sub(',', '.', str(data))
                scrubbed = re.sub('[^0-9-.]', '', scrubbed)
                return float(scrubbed)
            except ValueError:
                return np.nan

    def combine_files(self, pathlist):
        dm = self.parent
        ui = dm.parent
        dflist = []
        counter = 1
        for path in pathlist:
            mode = 'line' if counter == 1 else 'overwrite'
            dm.feedback('Reading files into group "{}": ({}/{})... '
                        .format(self.group_name.text(), counter, len(pathlist)),
                        mode=mode)
            dm.message_log.repaint()
            counter += 1

            # Get parse kwargs associated with file
            path_kwargs = {'encoding':'latin1'}  # load file as-is
            path_kwargs.update(ui.path_kwargs[path])

            #this is kinda sloppy
            # gets used somewhere else but comes from the same dictionary
            del path_kwargs['format']
            if ui.path_kwargs[path]['format'].lower() == 'infer':
                dtf = None
            else:
                dtf = ui.path_kwargs[path]['format']

            try:
                start = dt.datetime.now()
                data = pd.read_csv(path, **path_kwargs)
                data.index.names = ['Timestamp']
                data.columns = data.columns.map(str)
                data.index = pd.to_datetime(data.index,
                                            infer_datetime_format=True,
                                            format=dtf)
                end = dt.datetime.now()
                # This error has never been thrown
                if any(ts == pd.NaT for ts in data.index):
                    raise ValueError('Timestamps could not be parsed'
                                     'from given index column.'
                                     'Check import settings.')

                dflist.append(data)
            except ValueError as e:
                for file in dm.groups_tab.path_dict:
                    if dm.groups_tab.path_dict[file] == path: source = file
                if 'source' not in locals(): source = path
                dm.feedback('Failed', mode='append')
                dm.feedback('File "{}" threw an error: {}'.format(source, e))
                return pd.DataFrame()
            ui.path_kwargs[path].update(path_kwargs)

        df = pd.concat(dflist, axis=0, sort=False)
        dm.feedback('Scrubbing data... ', mode='append')
        dm.message_log.repaint()
        df = df.applymap(self.floatify)
        dm.feedback('Done', mode='append')
        return df.sort_index()

    def import_group(self):
        dm = self.parent
        ui = dm.parent
        group_name = self.group_name.text()
        w = self.imported_groups
        loaded_groups = [w.item(i).text() for i in range(w.count())]

        # Use case filtering
        if group_name == '':
            dm.feedback('Group name cannot be empty.')
            return
        elif group_name in loaded_groups:
            ok = ui.popup('Group "{}" already exists. Overwrite?'
                          .format(group_name),
                          title='Import Group',
                          mode='confirm')
            if ok:
                self.imported_groups.takeItem(loaded_groups.index(group_name))
        #??? What if group_name is a rename of a previously loaded group?
            else:
                return
        w = self.group_files
        #read groupfiles listview
        source_files = [w.item(i).text() for i in range(w.count())]
        if not source_files:
            dm.feedback('Group cannot have 0 associated files.')
            return

        if self.verify_import_settings(source_files):
            # path_dict is quasi global, appended gather_files
            # therefore, navigating to a different directory
            # should not disconnect files from paths
            source_paths = [self.path_dict[file] for file in source_files]
            df = self.combine_files(source_paths)

            if not df.empty:
                dm.groups[group_name] = Group(df)
                self.imported_groups.addItem(group_name)

                # Try to auto parse units
                if ui.auto_parse:
                    self.parse_series(dm.groups[group_name].series())

# -> this emits a signal to call CT's display_header_info function
                dm.configure_tab.select_group.addItem(group_name)
                self.group_files.clear()
                self.group_name.setText('')
                dm.modified = True
        else:
            dm.feedback('Import canceled.', mode='append')

    def parse_series(self, series):
        dm = self.parent
        ui = dm.parent
        report = ''
        for s in series:
            header = s.header
            parsed = ui.parse_unit(header)
            unit, interpreted = ui.interpret_unit(parsed)
            s.unit = unit
            s.unit_type = ui.get_unit_type(unit)
            if not interpreted:
                report += header + '\n'
            else:
                alias = re.sub('\[{}\]'.format(parsed), '', header).strip()
                s.alias = alias
                s.parent.alias_dict[alias] = header
        if report:
            ui.popup('Some units not assigned.',
                     title='Unit Parse Error Log',
                     informative=('You can assign units manually'
                                  'under Series Configuration,'
                                  'leave them blank, or '
                                  'adjust unit settings and reparse.'),
                     details=report,
                     mode='alert')

    def verify_import_settings(self, source_files):
        dm = self.parent
        ui = dm.parent
        counter = 1
        for file in source_files:
            mode = 'line' if counter == 1 else 'overwrite'
            dm.feedback('Loading previews: ({}/{})... '
                        .format(counter, len(source_files)),
                        mode=mode)
            dm.message_log.repaint()
            counter += 1

            if file not in ui.path_kwargs:
                path = self.path_dict[file]

                # Read first column and take its length
                # so you can read head and tail later
                # without loading the whole DF into memory
                shown_rows = 20
                first_col = pd.read_csv(path, usecols=[0], header=None,
                                      encoding='latin1')
                n = len(first_col.index)

                if n > shown_rows:
                    upper_df = pd.read_csv(path,
                                           nrows=shown_rows//2,
                                           header=None, encoding='latin1')
                    lower_df = pd.read_csv(path,
                                           skiprows=range(n-shown_rows//2),
                                           header=None, encoding='latin1')
                    ellipses = pd.DataFrame(['...']*len(upper_df.columns),
                                            index=upper_df.columns,
                                            columns=['...']).T
                    shown_df = upper_df.append(ellipses).append(lower_df)
                else:
                    shown_df = pd.read_csv(path,
                                           header=None, encoding='latin1')
                self.df_preview[path] = shown_df
                dtf, r, c, skiprows = self.interpret_data(path)
                ui.path_kwargs[path] = {'format': dtf,
                                        'header': r,
                                        'index_col': c,
                                        'skiprows': skiprows}
        dm.feedback('Verify import settings... ', mode='append')
        dm.message_log.repaint()
        dlg = ImportSettings(self, source_files)
        dlg.setModal(True)
        return dlg.exec()

    def delete_group(self):
        dm = self.parent
        ui = dm.parent
        try:
            item = self.imported_groups.selectedItems()[0]
            group_name = item.text()
            ok = ui.popup('Delete group "{}"?'.format(group_name),
                          mode='confirm')
            if ok:
                self.imported_groups.takeItem(self.imported_groups.row(item))
                del dm.groups[group_name]

                # delete corresponding entry in group_reassign (if it exists)
                for name in dm.group_reassign:
                    if group_name == dm.group_reassign[name][-1]:
                        del dm.group_reassign[name]
                        # only modified if the deleted group was loaded into ui
                        dm.modified = True
                        break
                w = dm.configure_tab.select_group
                w.removeItem(w.findText(group_name))
        except IndexError as e:
            print(e)
