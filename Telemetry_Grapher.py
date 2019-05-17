# -*- coding: utf-8 -*-
"""
Created on Mon May  6 14:56:29 2019

@author: seery
"""
class Telemetry_Grapher(QMainWindow):
    def __init__(self, groups={}):
        super().__init__()
        self.groups = copy.deepcopy(groups)
        self.path_kwargs = {}
        self.unit_dict = {  # dictionary of supported units
                'Position':['nm','μm','mm','cm','m'],
                'Velocity':['mm/s','cm/s','m/s'],
                'Acceleration':['mm/s^2','m/s^2'],  # check how superscripts are parsed
                'Angle':['deg','rad'],
                'Temperature':['°C','°F','K'],
                'Pressure':['mPa','Pa','kPa','MPa','GPa','mbar','bar','kbar','atm','psi','ksi'],
                'Heat':['mJ','J','kJ'],
                'Voltage':['mV','V','kV','MV'],
                'Current':['mA','A','kA'],
                'Resistance':['mΩ','Ω','kΩ','MΩ'],
                'Force':['mN','N','kN'],
                'Torque':['Nmm','Nm','kNm'],
                'Power':['mW','W','kW'],
                }

        self.unit_clarify = {  # try to map parsed unit through this dict before comparing to TG unit_dict
                'degC':'°C',
                'degF':'°F',
                'C':'°C',
                'F':'°F',
                }

        self.color_dict = {
                'Position':'C0',
                'Velocity':'C1',
                'Acceleration':'C2',
                'Angle':'C3',
                'Temperature':'C4',
                'Pressure':'C5',
                'Heat':'C6',
                'Voltage':'C7',
                'Current':'C8',
                'Resistance':'C9',
                'Force':'b',
                'Torque':'g',
                'Power':'r',
                None:'k'
                }

        self.markers = [  # when color coordination is on, use markers in this order to differentiate series
                'o',
                '+',
                'x',
                'D',
                's',
                '^',
                'v',
                '<',
                '>',
            ]

        self.setWindowTitle('Telemetry Plot Configurator')
        self.setWindowIcon(QIcon('satellite.png'))
        self.statusBar().showMessage('No subplot selected')
        self.manager = QWidget()

        self.docked_FS = QDockWidget("Figure Settings", self)
        self.figure_settings = Figure_Settings(self)
        self.docked_FS.setWidget(self.figure_settings)

        self.docked_CF = QDockWidget("Control Frame", self)
        self.control_frame = Control_Frame(self)
        self.docked_CF.setWidget(self.control_frame)
        self.axes_frame = Axes_Frame(self)
        self.master_frame = QWidget()
        self.master_frame.setLayout(QVBoxLayout())
        self.master_frame.layout().addWidget(self.axes_frame)
        self.setCentralWidget(self.master_frame)
        self.docked_SF = QDockWidget("Series Frame", self)
        self.series_frame = Series_Frame(self)
        self.docked_SF.setWidget(self.series_frame)
        self.addDockWidget(Qt.LeftDockWidgetArea, self.docked_SF)
        self.addDockWidget(Qt.LeftDockWidgetArea, self.docked_CF)
        self.addDockWidget(Qt.RightDockWidgetArea, self.docked_FS)  # Currently under construction
        self.docked_FS.hide()
        self.figure_settings.connect_widgets(container=self.axes_frame)
        self.control_frame.time_filter()

        self.resizeDocks([self.docked_SF], [450], Qt.Horizontal)

        fileMenu = self.menuBar().addMenu('File')
        newAction = QAction('New', self)
        newAction.setShortcut('Ctrl+N')
        newAction.setStatusTip('Open a blank figure')
        newAction.triggered.connect(self.new)
        openAction = QAction('Open', self)
        openAction.setShortcut('Ctrl+O')
        openAction.setStatusTip('Open existing figure')
        openAction.triggered.connect(self.open_fig)
        saveAction = QAction('Save', self)
        saveAction.setShortcut('Ctrl+S')
        saveAction.triggered.connect(self.save_figure)
        exitAction = QAction('Exit', self)
        exitAction.setShortcut('Ctrl+Q')
        exitAction.setStatusTip('Exit application')
        exitAction.triggered.connect(self.close)
        fileMenu.addAction(newAction)
        fileMenu.addAction(openAction)
        fileMenu.addAction(saveAction)
        fileMenu.addAction(exitAction)

        editMenu = self.menuBar().addMenu('Edit')
        undoAction = QAction('Undo', self)
        undoAction.setShortcut('Ctrl+Z')
        undoAction.triggered.connect(self.undo)
        redoAction = QAction('Redo', self)
        redoAction.setShortcut('Ctrl+Y')
        redoAction.triggered.connect(self.redo)
        refreshAction = QAction('Refresh Figure', self)
        refreshAction.setShortcut('Ctrl+R')
        refreshAction.triggered.connect(self.axes_frame.refresh_all)
#        resetAction = QAction('Undo', self)
#        resetAction.setShortcut('Ctrl+Z')  # wrong
#        resetAction.setStatusTip('Undo last action')  #wrong
#        resetAction.triggered.connect(self.undo)  #wrong
        editMenu.addAction(undoAction)
        editMenu.addAction(redoAction)
        editMenu.addAction(refreshAction)
#        editMenu.addAction(resetAction)

        toolsMenu = self.menuBar().addMenu('Tools')
        dataAction = QAction('Manage Data', self)
        dataAction.setShortcut('Ctrl+D')
        dataAction.triggered.connect(self.open_data_manager)
        templateAction = QAction('Import Template', self)
        templateAction.setShortcut('Ctrl+T')
        templateAction.triggered.connect(self.import_template)
        preferencesAction = QAction('Figure Preferences', self)
        preferencesAction.setShortcut('Ctrl+P')
#        preferencesAction.triggered.connect(self.axes_frame.fig_preferences)
        toolsMenu.addAction(dataAction)
        toolsMenu.addAction(templateAction)
        toolsMenu.addAction(preferencesAction)

        viewMenu = self.menuBar().addMenu('View')
        docksAction = QAction('Show/Hide Docks', self)
        docksAction.setShortcut('Ctrl+H')
        docksAction.triggered.connect(self.toggle_docks)
        interactiveAction = QAction('MPL Interactive Mode', self)
        interactiveAction.setShortcut('Ctrl+M')
        interactiveAction.setStatusTip('Toggle Matplotlib\'s interactive mode')
        interactiveAction.triggered.connect(self.toggle_interactive)
        darkAction = QAction('Dark Mode', self)
        darkAction.setShortcut('Ctrl+B')
        darkAction.setStatusTip('Toggle dark user interface')
        darkAction.triggered.connect(self.toggle_dark_mode)
        viewMenu.addAction(docksAction)
        viewMenu.addAction(interactiveAction)
        viewMenu.addAction(darkAction)

        self.showMaximized()
        ### Adding Figure Settings dock to right side currently screws this up
        self.control_frame.setFixedHeight(self.control_frame.height()) #(98 on my screen)
        self.control_frame.setFixedWidth(self.control_frame.width()) #(450 on my screen)

        ### Delete later, just for speed
#        self.open_data_manager()

    def groups_to_contents(self, groups):
        contents = {}
        for group in groups:
            aliases = []
            units = []
            for header in groups[group].series.keys():
                if groups[group].series[header].keep:
                    alias = groups[group].series[header].alias
                    if alias:
                        aliases.append(alias)
                    else:
                        aliases.append(header)
                    units.append(groups[group].series[header].unit)
            contents.update({group: dict(zip(aliases, units))})
        return contents

    def save_figure(self):
        ### Disconnected from button, but still should be connected to menubar action (TBI)
        """Saves figure using PyQt5's file dialog. Default format is .jpg."""
        AF = self.axes_frame
        AF.select_subplot(None, force_select=[])  # force deselect before save (no highlighted axes in saved figure)
        AF.draw()

        ### ONLY JPG WORKS RIGHT NOW
        dlg = QFileDialog()
        dlg.setFileMode(QFileDialog.AnyFile)
#        dlg.setConfirmOverwrite(True)
        dlg_output = dlg.getSaveFileName(self, 'Save Figure', os.getcwd(), "JPEG Image (*.jpg);;PNG Image (*.png)")
        plt.savefig(dlg_output[0], dpi=300, format='jpg', transparent=True, bbox_inches='tight')
#        TG.statusBar().showMessage('Saved to {}'.format(fileName))


    # I could move this and the unit_dicts/clarify dictionaries to DM, and have it read/write from/to a .txt file
    # ^ No, I don't think you can. DM is a QDialog and all its information will be lost when it's closed.
    def get_unit_type(self, unit):
        for e in self.unit_dict:
            if unit in self.unit_dict[e]:
                return e
        return None

    def closeEvent(self, event):
        """Hides any floating QDockWidgets and closes all created figures upon application exit."""
        for dock in [self.docked_CF, self.docked_SF, self.docked_FS]:
            if dock.isFloating(): dock.close()
        plt.close('all')
        event.accept()

    def new(self):
        pass

    def open_fig(self):
        pass

    def undo(self):
        pass

    def redo(self):
        pass

    def refresh_all(self):
        pass

    def open_data_manager(self):
        self.manager = Data_Manager(self)
        self.manager.setModal(True)
        self.manager.show()

    def import_template(self):
        pass

    def toggle_docks(self):
        docks = [self.docked_CF, self.docked_SF, self.docked_FS]
        if any([not dock.isVisible() for dock in docks]):
            for dock in docks: dock.show()
        else:
            for dock in docks: dock.hide()

    def toggle_interactive(self):
        pass

    def toggle_dark_mode(self):
        pass
# Legacy
#    def center(self):
#        qr = self.frameGeometry()
#        cp = QDesktopWidget().availableGeometry().center()
#        qr.moveCenter(cp)
#        self.move(qr.topLeft())