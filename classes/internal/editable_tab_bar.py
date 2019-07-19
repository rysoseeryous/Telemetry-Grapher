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

import re

from PyQt5.QtWidgets import QTabBar, QLineEdit
from PyQt5.QtCore import Qt, QPoint, QEvent

class EditableTabBar(QTabBar):
    def __init__(self, parent):
        QTabBar.__init__(self, parent)
        self._editor = QLineEdit(self)
        self._editor.setWindowFlags(Qt.Popup)
        self._editor.setFocusProxy(self)
        self._editor.editingFinished.connect(self.handleEditingFinished)
        self._editor.installEventFilter(self)

    def eventFilter(self, widget, event):
        if ((event.type() == QEvent.MouseButtonPress and
             not self._editor.geometry().contains(event.globalPos())) or
            (event.type() == QEvent.KeyPress and
             event.key() == Qt.Key_Escape)):
            self._editor.hide()
            return True
        return QTabBar.eventFilter(self, widget, event)

    def mouseDoubleClickEvent(self, event):
        index = self.tabAt(event.pos())
        ui = self.parent().parent()
        if index >= 0 and index != ui.nfigs():
            self.editTab(index)

    def editTab(self, index):
        rect = self.tabRect(index)
        self._editor.setFixedSize(rect.size())
        adjust = self.parent().geometry().height()
        point = QPoint(rect.x(), adjust-rect.height())
        self._editor.move(self.parent().mapToGlobal(point))
        self._editor.setText(self.tabText(index))
        if not self._editor.isVisible():
            self._editor.show()

    def handleEditingFinished(self):
        ui = self.parent().parent()
        index = self.currentIndex()
        if index >= 0 and index != ui.nfigs():
            cf = self.parent().widget(index)
            fig_title = re.sub('[\\\\.]', '', self._editor.text())
            if (fig_title not in ui.open_figure_titles() or
                fig_title == cf.fig_params.title):
                    self._editor.hide()
                    self.setTabText(index, self._editor.text())
                    cf.fig._suptitle.set_text(fig_title)
                    cf.fig_params.title = fig_title
                    cf.draw()
                    cf.saved = False
