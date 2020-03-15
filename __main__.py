# -*- coding: utf-8 -*-
"""__main__.py - Instantiates logger and executes GUI."""

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

if __name__ == '__main__':
    import datetime as dt
    import logging
    import sys
    import os

    from PyQt5.QtWidgets import QApplication
    from PyQt5.QtCore import QCoreApplication
    
    from telemetry_grapher.classes.toplevel.main_window import UI

    if 'app' not in locals():
        app = QCoreApplication.instance()
    if app is None:  # otherwise kernel dies
        app = QApplication(sys.argv)
    _ = UI()
    app.exec_()
