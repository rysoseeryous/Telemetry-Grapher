# -*- coding: utf-8 -*-
"""groups_tab.py - Contains GroupsTab class definition."""

# This file is part of Telemetry-Grapher.

# Telemetry-Grapher is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.

# Telemetry-Grapher is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY
# without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.

# You should have received a copy of the GNU General Public License
# along with Telemetry-Grapher. If not, see < https: // www.gnu.org/licenses/>.

__author__ = "Ryan Seery"
__copyright__ = 'Copyright 2019 Max-Planck-Institute for Solar System Research'
__license__ = "GNU General Public License"

import os
import re
import math
import datetime as dt
import pandas as pd
import numpy as np

from PyQt5.QtWidgets import (QWidget, QFileDialog, QMessageBox, QHeaderView,
                             QGridLayout, QHBoxLayout, QVBoxLayout, QFrame,
                             QPushButton, QLabel, QLineEdit, QComboBox,
                             QTableView, QListWidget, QListWidgetItem)
from PyQt5.QtGui import QIcon, QStandardItemModel, QStandardItem
from PyQt5.QtCore import Qt, QFileInfo

from .import_settings import ImportSettings
from ..internal.group import Group

class GroupsTab(QWidget):
    """UI for organizing source files into groups."""

    def __init__(self, parent):
        super().__init__()
        self.parent = parent
        dm = self.parent
        ui = dm.parent

        self.path_dict = {}
        self.df_preview = {}

        vbox = QVBoxLayout()
        hbox = QHBoxLayout()
        self.browse = QPushButton()
        self.browse.setIcon(QIcon(dm.parent.current_icon_path+'/browse.png'))
        self.browse.clicked.connect(self.browse_dialog)
        hbox.addWidget(self.browse)
        self.directory = QLineEdit(ui.csv_dir)
        self.directory.returnPressed.connect(self.search_dir)
        hbox.addWidget(self.directory)
        vbox.addLayout(hbox)

        grid = QGridLayout()

        self.file_search = QLineEdit()
        self.file_search.setPlaceholderText('Search')
        self.file_search.textChanged.connect(self.filter_files)
        self.file_search.setFocus(True)
        grid.addWidget(self.file_search, 0, 0)

        grid.addWidget(QLabel('Found Files'), 1, 0)

        self.found_files = QTableView()
        self.found_files.setSortingEnabled(True)
        self.files_model = QStandardItemModel()
        self.found_files.setModel(self.files_model)
        ui.make_widget_deselectable(self.found_files)
        self.found_files.setDragEnabled(True)
        self.found_files.setSelectionBehavior(QTableView.SelectRows)
        grid.addWidget(self.found_files, 2, 0)

        self.group_name = QLineEdit()
        if self.parent.debug:
            self.group_name.setText('Debug')  # delete initial text later #!!!
        self.group_name.setPlaceholderText('Group Name')
        self.group_name.returnPressed.connect(self.import_group)
        grid.addWidget(self.group_name, 0, 1)

        grid.addWidget(QLabel('Files in Group'), 1, 1)

        self.group_files = QListWidget()
        ui.make_widget_deselectable(self.group_files)
        self.group_files.setAcceptDrops(True)
        self.group_files.dropEvent = self.group_files_drop_event
        self.group_files.dragEnterEvent = self.group_files_drag_event
        self.group_files.setSelectionMode(QListWidget.ExtendedSelection)
        self.group_files.keyPressEvent = self.delete_group_file
        if self.parent.debug:
            self.group_files.addItem('Test.csv') #!!! Delete later
        grid.addWidget(self.group_files, 2, 1)

        line = QFrame()
        line.setFrameShape(QFrame.VLine)
        line.setFrameShadow(QFrame.Sunken)
        grid.addWidget(line, 0, 2, 3, 1)

        self.import_button = QPushButton('Import Group')
        self.import_button.clicked.connect(self.import_group)
        self.import_button.setDefault(True)
        grid.addWidget(self.import_button, 0, 3)

        grid.addWidget(QLabel('Imported Groups'), 1, 3)

        self.imported_groups = QListWidget()
        ui.make_widget_deselectable(self.imported_groups)
        self.imported_groups.setDragEnabled(True)
        for group_name in dm.all_groups.keys():
            item = QListWidgetItem(group_name)
            item.setFlags(item.flags() | Qt.ItemIsEditable)
            self.imported_groups.addItem(item)
        self.imported_groups.itemChanged.connect(self.edit_group_name)
        self.imported_groups.keyPressEvent = self.delete_imported_group
        grid.addWidget(self.imported_groups, 2, 3)

        self.figure_selector = QComboBox()
        self.figure_selector.addItems(ui.open_figure_titles())
        cf = ui.get_current_figure()
        self.figure_selector.setCurrentText(cf.title)
        self.figure_selector.currentTextChanged.connect(
                self.update_figure_groups)
        grid.addWidget(self.figure_selector, 0, 4)

        grid.addWidget(QLabel('Figure Groups'), 1, 4)

        self.figure_groups = QListWidget()
        ui.make_widget_deselectable(self.figure_groups)
        self.figure_groups.setAcceptDrops(True)
        self.figure_groups.dropEvent = self.figure_groups_drop_event
        self.figure_groups.dragEnterEvent = self.figure_groups_drag_event
        self.figure_groups.addItems(dm.fig_groups[cf.title])
        self.figure_groups.keyPressEvent = self.delete_figure_group
        grid.addWidget(self.figure_groups, 2, 4)

        factors = [2, 1, 1, 1, 1]
        for c, f in enumerate(factors):
            grid.setColumnStretch(c, f)
        vbox.addLayout(grid)
        self.setLayout(vbox)

    def browse_dialog(self):
        """Opens a file dialog to select a working directory."""
        dm = self.parent
        ui = dm.parent
        path = str(QFileDialog.getExistingDirectory(self,
                                                    "Select Directory",
                                                    ui.csv_dir))
        if path:
            self.directory.setText(path)
            self.search_dir()

    def format_file_size(self, file_size):
        # I think this doesn't quite work properly... #!!!
        if file_size:
            n = np.clip(int(math.log(file_size, 1000)), 0, 3)
        else:
            n = 0
        suffix = ['bytes', 'KB', 'MB', 'GB']
        return str(int(file_size/(1000*n))) + ' ' + suffix[n]

    def populate_found_files(self, files):
        self.files_model.clear()
        labels = ['File Name', 'Size', 'Modified']
        self.files_model.setHorizontalHeaderLabels(labels)
        v_header = self.found_files.verticalHeader()
        v_header.setDefaultSectionSize(v_header.minimumSectionSize())
        v_header.hide()
        h_header = self.found_files.horizontalHeader()
        h_header.setSectionResizeMode(0, QHeaderView.Stretch)
        h_header.setSectionResizeMode(1, QHeaderView.ResizeToContents)
        h_header.setSectionResizeMode(2, QHeaderView.ResizeToContents)
        for f in files:
            name = QStandardItem(f.fileName())
            size = QStandardItem(self.format_file_size(f.size()))
            date = f.lastModified().toPyDateTime()
            modified = QStandardItem(date.strftime('%d-%b-%y %H:%M'))
            self.files_model.appendRow([name, size, modified])

    def search_dir(self):
        """Searches current directory and displays found files.
        Newly found files are given an entry with default values in a
        dictionary associating filepaths and reading kwargs."""
        dm = self.parent
        ui = dm.parent
        path = self.directory.text()
        ui.csv_dir = path
        try:
            self.files, new_path_dict_entries = self.gather_files(path)
        except FileNotFoundError:
            dm.feedback('{} is not a valid path.'.format(path))
        else:
            self.path_dict.update(new_path_dict_entries)
            self.file_search.setText('')
            self.populate_found_files(self.files)

    def gather_files(self, path):
        """Returns list of csv file names in directory path.
        Excludes temporary files.
        Does not search subfolders.
        Also returns dictionary associating files to their source paths."""
        files = []
        path_dict = {}
        filetypes = re.compile(r'(csv|zip)$')
        exclude = re.compile(r'^~\$')
        for file in os.listdir(path):
            if re.search(filetypes, file) and not re.search(exclude, file):
                file_path = os.path.join(path, file)
                files.append(QFileInfo(file_path))
                path_dict[file] = file_path
        return files, path_dict

    def filter_files(self, text):
        """Displays files in found files list which match searchbar input."""
        pattern = re.compile(text, re.IGNORECASE)
        matches = [f for f in self.files
                   if re.search(pattern, os.path.splitext(f.fileName())[0])]
        self.populate_found_files(matches)

    def group_files_drag_event(self, event):
        if event.source() is self.found_files:
            event.accept()
        else:
            event.ignore()

    def figure_groups_drag_event(self, event):
        if event.source() is self.imported_groups:
            event.accept()
        else:
            event.ignore()

    def group_files_drop_event(self, event):
        dm = self.parent
        w = self.group_files
        selected = self.found_files.selectedIndexes()
        for row in set([index.row() for index in selected]):
            file_name = self.found_files.model().item(row, 0).text()
            if file_name in [w.item(i).text() for i in range(w.count())]:
                dm.feedback('"{}" already added to group.'.format(file_name))
            else:
                w.addItem(file_name)
        event.ignore()

    def figure_groups_drop_event(self, event):
        dm = self.parent
        cf_title = self.figure_selector.currentText()
        name = self.imported_groups.currentItem().text()
        w = self.figure_groups
        if name in [w.item(i).text() for i in range(w.count())]:
            dm.feedback('"{}" already in figure "{}".'.format(name, cf_title))
        else:
            w.addItem(name)
            dm.fig_groups[cf_title].append(name)
            dm.group_rename.update({name:[name]})
            dm.modified = True
        event.ignore()

    def review_import_settings(self, source_files):
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
        dm.feedback('Review import settings... ', mode='append')
        dm.message_log.repaint()
        dlg = ImportSettings(self, source_files)
        dlg.setModal(True)
        return dlg.exec()

    def interpret_data(self, path):
        dtf = 'Infer'
        r, c = self.parse_df_origin(path)
        skiprows = None
        return dtf, r, c, skiprows

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

    def import_group(self):
        dm = self.parent
        ui = dm.parent
        group_name = self.group_name.text().strip()
        w = self.imported_groups
        loaded_groups = [w.item(i).text() for i in range(w.count())]

        # Use case filtering
        if group_name == '':
            dm.feedback('Group name cannot be empty.')
            return
        elif group_name in loaded_groups:
            result = ui.popup('Group "{}" already exists. Overwrite?'
                          .format(group_name),
                          title='Import Group',
                          mode='confirm')
            if result != QMessageBox.Ok:
                return

        w = self.group_files
        #read groupfiles listview
        source_files = [w.item(i).text() for i in range(w.count())]
        if not source_files:
            dm.feedback('Group cannot have 0 associated files.')
            return

        if self.review_import_settings(source_files):
            dm.feedback('Confirmed.', mode='append')
            dm.message_log.repaint()
            # path_dict is quasi global, appended gather_files
            # therefore, navigating to a different directory
            # should not disconnect files from paths
            source_paths = [self.path_dict[file] for file in source_files]
            df = self.combine_files(source_paths)

            if not df.empty:
                title = self.figure_selector.currentText()
                group = Group(df, group_name)
                dm.all_groups[group_name] = group
                if group_name not in loaded_groups:
                    item = QListWidgetItem(group_name)
                    item.setFlags(item.flags() | Qt.ItemIsEditable)
                    dm.fig_groups[title].append(group_name)
                    self.imported_groups.addItem(item)
                    self.figure_groups.addItem(group_name)
                dm.group_rename.update({group_name:[group_name]})
                # Try to auto parse units
                if ui.auto_parse:
                    report = self.parse_series(group.series())
                    self.report_parse_error_log(report)
# -> this emits a signal to call CT's display_header_info function
                dm.configure_tab.select_group.addItem(group_name)
                dm.configure_tab.select_group.setCurrentText(group_name)
                self.group_files.clear()
                self.group_name.setText('')
                dm.modified = True
        else:
            dm.feedback('Import canceled.', mode='append')

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
        df.drop_duplicates(inplace=True)
        df.sort_index(inplace=True)
        return df

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

    def parse_series(self, series):
        dm = self.parent
        report = ''
        for s in series:
            header = s.header
            parsed = dm.parse_unit(header)
            unit, unit_type, interpreted = dm.interpret_unit(parsed)
            s.unit = unit
            s.unit_type = unit_type
            if not interpreted:
                report += header + '\n'
            else:
                alias = re.sub('\[{}\]'.format(parsed), '', header).strip()
                s.alias = alias
                s.group.alias_dict[alias] = header
        return report

    def report_parse_error_log(self, report):
        dm = self.parent
        ui = dm.parent
        if report:
            ui.popup('Some units and/or unit types not assigned.',
                     title='Unit Parse Error Log',
                     informative=('You can assign units and unit types '
                                  'manually under Series Configuration, '
                                  'leave them blank, or adjust unit settings '
                                  'and reparse.'),
                     details=report,
                     mode='alert')

    def update_figure_groups(self, text):
        dm = self.parent
        self.figure_groups.clear()
        self.figure_groups.addItems(dm.fig_groups[text])

    def delete_group_file(self, event):
        if event.key() == Qt.Key_Delete:
            for item in self.group_files.selectedItems():
                self.group_files.takeItem(self.group_files.row(item))

    def edit_group_name(self, item):
        """Renames or imported group.
        Keeps track of past renaming operations so Data Manager's save changes
        can identify existing groups as having been renamed.
        Accessible by double clicking on an imported group."""
        dm = self.parent
        ui = dm.parent
        new = item.text()
        old = list(dm.all_groups.keys())[self.imported_groups.row(item)]
        if new == old: return
        if not new:
            dm.feedback('Group name cannot be blank.')
            item.setText(old)
        elif new in dm.all_groups:
            dm.feedback('Group "{}" already exists.'
                        'Please choose a different name.'
                        .format(new))
            item.setText(old)
        else:
            dm.all_groups[new] = dm.all_groups[old]
            del dm.all_groups[old]
            for name in dm.group_rename:
                if old == dm.group_rename[name][-1]:
                    dm.group_rename[name].append(new)
                    break
            for cf in ui.all_figures():
                if old in dm.fig_groups[cf.title]:
                    i = dm.fig_groups[cf.title].index(old)
                    dm.fig_groups[cf.title][i] = new
            cf_title = self.figure_selector.currentText()
            self.figure_groups.clear()
            self.figure_groups.addItems(dm.fig_groups[cf_title])
            i = dm.configure_tab.select_group.findText(old)
            dm.configure_tab.select_group.setItemText(i, new)
            dm.modified = True

    def delete_imported_group(self, event):
        dm = self.parent
        ui = dm.parent
        if event.key() == Qt.Key_Delete:
            item = self.imported_groups.currentItem()
            group_name = item.text()
            result = ui.popup('Delete group "{}"?'.format(group_name),
                              mode='confirm')
            if result == QMessageBox.Ok:
                del dm.all_groups[group_name]
                for name in dm.group_rename:
                    if group_name == dm.group_rename[name][-1]:
                        del dm.group_rename[name]
                        break
                self.imported_groups.takeItem(self.imported_groups.row(item))
                for cf in ui.all_figures():
                    try:
                        dm.fig_groups[cf.title].remove(group_name)
                    except ValueError:
                        pass
                cf_title = self.figure_selector.currentText()
                self.figure_groups.clear()
                self.figure_groups.addItems(dm.fig_groups[cf_title])
                w = dm.configure_tab.select_group
                w.removeItem(w.findText(group_name))
                dm.feedback('Deleted group "{}".'.format(group_name))
                dm.modified = True

    def delete_figure_group(self, event):
        dm = self.parent
        ui = dm.parent
        if event.key() == Qt.Key_Delete:
            cf_title = self.figure_selector.currentText()
            item = self.figure_groups.selectedItems()[0]
            group_name = item.text()
            result = ui.popup('Remove group "{}"?'.format(group_name),
                              mode='confirm')
            if result == QMessageBox.Ok:
                self.figure_groups.takeItem(self.figure_groups.row(item))
                dm.fig_groups[cf_title].remove(item.text())
                del dm.group_rename[item.text()]
                dm.modified = True
                dm.feedback('Removed group "{}" from figure "{}".'
                            .format(group_name, cf_title))