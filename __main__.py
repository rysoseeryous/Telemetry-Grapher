# -*- coding: utf-8 -*-
"""__main__.py - Executes GUI."""

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

#if __name__ == '__main__':
import sys
import logging
from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore import QCoreApplication
# If you want to run from Anaconda Prompt, this should be .classes.ab
# Doing that executes without error but doesn't actually open the app
# *shrug*
from classes.toplevel.main_window import UI

# Allows logging of unhandled exceptions
logger = logging.getLogger(__name__)
logging.basicConfig(filename='errors.log', filemode='w', level=logging.DEBUG)

def handle_unhandled_exception(exc_type, exc_value, exc_traceback):
    """Handler for unhandled exceptions that will write to the logs"""
    print('Error thrown! Check the log.')
    if issubclass(exc_type, KeyboardInterrupt):
        # call the default excepthook saved at __excepthook__
        sys.__excepthook__(exc_type, exc_value, exc_traceback)
        return
    logger.critical("Unhandled exception",
                    exc_info=(exc_type, exc_value, exc_traceback))

#sys.excepthook = handle_unhandled_exception


if 'app' not in locals():
    app = QCoreApplication.instance()
if app is None:  # otherwise kernel dies
    app = QApplication(sys.argv)
_ = UI(logger=logger)
app.exec_()
