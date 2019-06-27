# -*- coding: utf-8 -*-
"""
Created on Thu Jun 13 15:53:50 2019

@author: seery
"""

#if __name__ == '__main__':
import sys
import logging
from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore import QCoreApplication
# If you want to run from Anaconda Prompt, this should be .classes.ab
# But doing that executes without error but doesn't actually open the app
# *shrug*
from classes.toplevel.main_window import UI

# Allows logging of unhandled exceptions
logger = logging.getLogger(__name__)
logging.basicConfig(filename='errors.log', filemode='w', level=logging.DEBUG)

def handle_unhandled_exception(exc_type, exc_value, exc_traceback):
    """Handler for unhandled exceptions that will write to the logs"""
    if issubclass(exc_type, KeyboardInterrupt):
        # call the default excepthook saved at __excepthook__
        sys.__excepthook__(exc_type, exc_value, exc_traceback)
        return
    logger.critical("Unhandled exception",
                    exc_info=(exc_type, exc_value, exc_traceback))

sys.excepthook = handle_unhandled_exception


if 'app' not in locals():
    app = QCoreApplication.instance()
if app is None:  # otherwise kernel dies
    app = QApplication(sys.argv)
_ = UI(logger=logger)#, groups={'test': test_group})
app.exec_()