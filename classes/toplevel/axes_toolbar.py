# -*- coding: utf-8 -*-
"""axes_toolbar.py - Contains AxesToolbar class definition."""

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

from PyQt5.QtWidgets import (QToolBar, QComboBox, QAction,
                             QDoubleSpinBox, QAbstractSpinBox)

class AxesToolbar(QToolBar):

    def __init__(self, title, parent):
        super().__init__(title)
        self.parent = parent

        self.current_axes = []
        self.selector = QComboBox()
        self.selector.setToolTip('Current Axis')
        self.selector.currentIndexChanged.connect(self.update_current_axes)
        self.selector.setMinimumHeight(33)
        self.addWidget(self.selector)

        self.log_toggle = QAction('log', self)
        self.log_toggle.setToolTip('Toggle Log Scale')
        self.log_toggle.setCheckable(True)
        self.log_toggle.setEnabled(False)
        self.log_toggle.triggered.connect(self.toggle_log_scale)
        self.addAction(self.log_toggle)

        self.autoscale_toggle = QAction('auto', self)
        self.autoscale_toggle.setToolTip('Toggle Autoscaling')
        self.autoscale_toggle.setCheckable(True)
        self.autoscale_toggle.setEnabled(False)
        self.autoscale_toggle.toggled.connect(self.manage_limit_indicators)
        self.autoscale_toggle.triggered.connect(self.toggle_autoscale_limits)
        self.addAction(self.autoscale_toggle)

        self.yaxis_min = QDoubleSpinBox()
        self.yaxis_min.setToolTip('Y-Axis Min')
        # setStepType added after 5.12, currently on 5.9
        # Permission error encountered when trying to upgrade
        if hasattr(self.yaxis_min, 'setStepType'):
            self.yaxis_min.setStepType(
                    QAbstractSpinBox.AdaptiveDecimalStepType)
        self.yaxis_min.setEnabled(False)
        self.yaxis_min.valueChanged.connect(self.update_custom_limits)
        self.yaxis_min.setMinimumHeight(33)
        self.addWidget(self.yaxis_min)

        self.yaxis_max = QDoubleSpinBox()
        self.yaxis_max.setToolTip('Y-Axis Max')
        if hasattr(self.yaxis_max, 'setStepType'):
            self.yaxis_max.setStepType(
                    QAbstractSpinBox.AdaptiveDecimalStepType)
        self.yaxis_max.setEnabled(False)
        self.yaxis_max.valueChanged.connect(self.update_custom_limits)
        self.yaxis_max.setMinimumHeight(33)
        self.addWidget(self.yaxis_max)

    def update_current_axes(self, i):
        # This signal emitted twice when:
        # - Click on an already selected subplot with contents
        # - Add/remove series from subplot
        ui = self.parent
        cf = ui.get_current_figure()
        if i == -1:
            # Selector is blank
            self.current_axes = []
            b = False
        elif i == 0:
            # Selector set to 'All'
            sp = cf.current_sps[0]
            self.current_axes = sp.axes
            b = bool(sp.host().contents)
        else:
            sp = cf.current_sps[0]
            ax = sp.axes[i-1]
            self.current_axes = [ax]
            b = bool(sp.host().contents)
        self.log_toggle.setEnabled(b)
        self.autoscale_toggle.setEnabled(b)
        any_log = any([ax.log for ax in self.current_axes])
        self.log_toggle.setChecked(any_log)
        any_auto = any([ax.auto_limits for ax in self.current_axes])
        self.autoscale_toggle.setChecked(any_auto and b)
        self.manage_limit_indicators(any_auto and b)

    def toggle_log_scale(self, checked):
        ui = self.parent
        cf = ui.get_current_figure()
        log_dict = {True: 'log', False: 'linear'}
        for ax in self.current_axes:
            ax.log = checked
            ax.set_yscale(log_dict[ax.log])
        cf.format_axes()
        cf.draw()

    def manage_limit_indicators(self, checked):
        i = self.selector.currentIndex()
        enable = (not checked and i > 0)
        self.yaxis_min.setEnabled(enable)
        self.yaxis_max.setEnabled(enable)
        self.yaxis_min.blockSignals(True)
        self.yaxis_max.blockSignals(True)
        if i > 0:
            ax = self.current_axes[0]
            data_min, data_max = ax.get_data_extents()
            ymin, ymax = ax.get_ylim()
            span = data_max - data_min
            margin = ax.margins()[1]
            lower = data_min - span*(1 + margin)
            upper = data_max + span*(1 + margin)
            self.yaxis_min.setMinimum(lower)
            self.yaxis_min.setMaximum(upper)
            self.yaxis_max.setMinimum(lower)
            self.yaxis_max.setMaximum(upper)
            self.yaxis_min.setValue(ymin)
            self.yaxis_max.setValue(ymax)
        else:
            self.yaxis_min.setMinimum(0)
            self.yaxis_min.setMaximum(0)
            self.yaxis_max.setMinimum(0)
            self.yaxis_max.setMaximum(0)
            self.yaxis_min.setValue(0)
            self.yaxis_max.setValue(0)
        self.yaxis_min.blockSignals(False)
        self.yaxis_max.blockSignals(False)

    def toggle_autoscale_limits(self, checked):
        ui = self.parent
        cf = ui.get_current_figure()
        for ax in self.current_axes:
            ax.auto_limits = checked
            ax.autoscale(enable=ax.auto_limits, axis='y')
            if not ax.auto_limits:
                if not ax.custom_limits:
                    ax.custom_limits = ax.get_ylim()
                ax.set_ylim(ax.custom_limits)

        self.manage_limit_indicators(checked)
        cf.format_axes()
        cf.draw()

    def update_custom_limits(self):
        ui = self.parent
        cf = ui.get_current_figure()
        ax = self.current_axes[0]
        ymin = self.yaxis_min.value()
        ymax = self.yaxis_max.value()
        if ymin >= ymax: return
        ax.custom_limits = [ymin, ymax]
        ax.set_ylim(ax.custom_limits)
        cf.format_axes()
        cf.draw()
