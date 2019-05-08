# -*- coding: utf-8 -*-
"""
Created on Mon May  6 14:56:29 2019

@author: seery
"""

class Figure_Window(QMainWindow):
    def __init__(self, data, data_dict):
        super().__init__()
        self.data = data
        self.data_dict = data_dict
        self.start = '2018-12-06 00:00'
        self.end = '2018-12-09 00:00'  # dummy start/end from PHI_HK, default will be None
        self.setWindowTitle('Telemetry Plot Configurator')
        self.setWindowIcon(QIcon('satellite.png'))
        self.statusBar().showMessage('No subplot selected')
        self.fig_preferences()
        self.manager = QWidget()


        self.docked_SF = QDockWidget("Series Frame", self)
        self.series_frame = Series_Frame(self)
        self.docked_SF.setWidget(self.series_frame)
        self.docked_CF = QDockWidget("Control Frame", self)
        self.control_frame = Control_Frame(self)
        self.docked_CF.setWidget(self.control_frame)
        self.addDockWidget(Qt.LeftDockWidgetArea, self.docked_SF)
        self.addDockWidget(Qt.BottomDockWidgetArea, self.docked_CF)
        self.axes_frame = Axes_Frame(self)
        self.master_frame = QWidget()
        self.master_frame.setLayout(QVBoxLayout())
        self.master_frame.layout().addWidget(self.axes_frame)
        self.setCentralWidget(self.master_frame)
        self.resizeDocks([self.docked_SF], [600], Qt.Horizontal)

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
        saveAction.triggered.connect(self.control_frame.save_figure)
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
        refreshAction.triggered.connect(self.refresh_all)
#        resetAction = QAction('Undo', self)
#        resetAction.setShortcut('Ctrl+Z')
#        resetAction.setStatusTip('Undo last action')
#        resetAction.triggered.connect(self.undo)
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
        preferencesAction.triggered.connect(self.fig_preferences)
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
        self.control_frame.setFixedHeight(self.control_frame.height())

    def closeEvent(self, event):
        """Hides any floating QDockWidgets and closes all created figures upon application exit."""
        for dock in [self.docked_CF, self.docked_SF]: #add preferences window to this later
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
        self.manager = Data_Manager(self.data)
        self.manager.setModal(True)
        self.manager.show()

    def import_template(self):
        pass

    def fig_preferences(self):
#        if self.start is None:
#            startCondition = lambda index: index == True
#        else:
#            startCondition = lambda index: index >= self.start
#        if self.end is None:
#            endCondition = lambda index: index == True
#        else:
#            endCondition = lambda index: index <= self.end
        if self.start is None: self.start = min([self.data[name].index[0] for name in self.data.keys()])
        if self.end is None: self.end = max([self.data[name].index[-1] for name in self.data.keys()])
        self.timespan = pd.to_datetime(self.end)-pd.to_datetime(self.start)
        if self.timespan < dt.timedelta(days=1):
            self.dotsize = 0.8
        else:
            self.dotsize = 0.5
        if self.timespan >= dt.timedelta(days=2) and self.timespan < dt.timedelta(days=4):
            self.dateformat = mdates.DateFormatter('%d/%b %H:%M')
            self.major_locator = mdates.DayLocator()
        elif self.timespan >= dt.timedelta(days=4):
            self.dateformat = mdates.DateFormatter('%d/%b %H:%M')
            self.major_locator = mdates.DayLocator()
        else:
            self.dateformat = mdates.DateFormatter('%d %b %Y %H:%M')
            self.major_locator = mdates.HourLocator(interval=2)

    def toggle_docks(self):
        # make toggle instead of only show
        self.docked_CF.show()
        self.docked_SF.show()

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