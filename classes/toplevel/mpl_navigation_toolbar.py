# -*- coding: utf-8 -*-
"""
Created on Tue Jun 25 16:15:34 2019

@author: seery
"""
import numpy as np
from matplotlib.dates import num2date
from matplotlib.backends.backend_qt5agg import NavigationToolbar2QT

class NavToolbar(NavigationToolbar2QT):
    NavigationToolbar2QT.toolitems = (
            ('Home', 'Reset original view', 'home', 'home'),
#            ('Back', 'Back to  previous view', 'back', 'back'),
#            ('Forward', 'Forward to next view', 'forward', 'forward'),
#            (None, None, None, None),
#            ('Pan', 'Pan axes with left mouse, zoom with right', 'move', 'pan'),
            ('Zoom', 'Zoom to rectangle', 'zoom_to_rect', 'zoom'),
#            ('Subplots', 'Configure subplots', 'subplots', 'configure_subplots'),
#            (None, None, None, None),
#            ('Save', 'Save the figure', 'filesave', 'save_figure')
            )

    def __init__(self, plotCanvas, parent):
        NavigationToolbar2QT.__init__(self, plotCanvas, parent)
        self._pressed_sp = None

    def _update_buttons_checked(self):
        # sync button checkstates to match active mode
        if 'pan' in self._actions:
            self._actions['pan'].setChecked(self._active == 'PAN')
        self._actions['zoom'].setChecked(self._active == 'ZOOM')

    def press_zoom(self, event):
        super().press_zoom(event)
        if event.inaxes and self._xypress:
            self._pressed_sp = self.canvas.get_subplot(event)
        else:
            self._pressed_sp = None

    def release_zoom(self, event):
        """Callback for mouse button release in zoom to rect mode."""
        for zoom_id in self._ids_zoom:
            self.canvas.mpl_disconnect(zoom_id)
        self._ids_zoom = []

        self.remove_rubberband()

        if not self._xypress:
            return

#        last_a = []

#        for cur_xypress in self._xypress:
        x, y = event.x, event.y
        lastx, lasty, a, ind, view = self._xypress[0]
        # ignore singular clicks - 5 pixels is a threshold
        # allows the user to "cancel" a zoom action
        # by zooming by less than 5 pixels
        if ((abs(x - lastx) < 5 and self._zoom_mode != "y") or
                (abs(y - lasty) < 5 and self._zoom_mode != "x")):
            self._xypress = None
            self.release(event)
            self.draw()
            return

        ix_min, ix_max = a.bbox.intervalx
        iy_min, iy_max = a.bbox.intervaly

        (x1, y1), (x2, y2) = np.clip(
            [[lastx, lasty], [x, y]], a.bbox.min, a.bbox.max)
        if self._zoom_mode == "x":
            y1, y2 = iy_min, iy_max
        elif self._zoom_mode == "y":
            x1, x2 = ix_min, ix_max

        xmin, xmax = sorted([x1, x2])
        ymin, ymax = sorted([y1, y2])
        xspan = ix_max - ix_min
        yspan = iy_max - iy_min
        y2_m = 1 - abs((iy_max - ymax)/yspan)
        y1_m = 1 + abs((iy_min - ymin)/yspan)
        x2_m = 1 - abs((ix_max - xmax)/xspan)
        x1_m = 1 + abs((ix_min - xmin)/xspan)
        print('y2_m: ', y2_m)
        print('y1_m: ', y1_m)
        print('x2_m: ', x2_m)
        print('x1_m: ', x1_m)
        print()

        sp = self._pressed_sp
        for ax in sp.axes:
            limits = sp.y_limits[ax]
            sp.y_limits[ax] = [i*j for i,j in zip(limits, [y1_m, y2_m])]





        self._pressed_sp = None


        # detect twinx,y axes and avoid double zooming
#        twinx, twiny = False, False
#        if last_a:
#            for la in last_a:
#                if a.get_shared_x_axes().joined(a, la):
#                    twinx = True
#                if a.get_shared_y_axes().joined(a, la):
#                    twiny = True
#        last_a.append(a)
#
#        if self._button_pressed == 1:
#            direction = 'in'
#        elif self._button_pressed == 3:
#            direction = 'out'
#        else:
#            continue
#
#        a._set_view_from_bbox((lastx, lasty, x, y), direction,
#                              self._zoom_mode, twinx, twiny)

#        self.draw()
        self._xypress = None
        self._button_pressed = None

        self._zoom_mode = None

        self.push_current()
        self.release(event)
