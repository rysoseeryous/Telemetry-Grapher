# -*- coding: utf-8 -*-
"""
Created on Thu Jun 13 15:52:45 2019

@author: seery
"""
import numpy as np
from .contents_dict import ContentsDict
from .axis_manager import AxisManager

class SubplotManager():
    """Wrapper around subplot object (host).
    Keeps track of contents and settings of each subplot."""

    def __init__(self, parent, host,
                 contents=None, order=None, index=None,
                 legend=False, color_coord=False):
        self.parent = parent
        self.axes = [host]
#        self.y_limits = {host: host.get_ylim()}
#        self.zoom_factors = [1, 1]
        if contents is None:
            # standard contents format: {group: [headers]}
            self.contents = ContentsDict()
        else:
            self.contents = contents
        if order is None:
            self.order = []
        else:
            self.order = order
        self.index = index
        self.color_coord = color_coord
        self.legend = legend
        self.location = 'Outside Right'
        self.ncols = 1

    def host(self):
        return self.axes[0]

#    def axes(self):
#        return []




    def make_patch_spines_invisible(self, ax):
        """see https://matplotlib.org/gallery/
        ticks_and_spines/multiple_yaxis_with_spines.html"""
        ax.set_frame_on(True)
        ax.patch.set_visible(False)
        for spine in ax.spines.values():
            spine.set_visible(False)

    def verify_order(self):
        sp = self
        ui = self.parent
        identifiers = []
        for group_name in sp.contents:
            group = ui.groups[group_name]
            for alias in sp.contents[group_name]:
                try:
                    header = group.alias_dict[alias]
                except KeyError:
                    header = alias
                s = group.series(header)
                identifiers.append((s.unit_type, s.unit))
        for elem in sp.order:
            if elem not in identifiers:
                sp.order.remove(elem)


    def plot(self, skeleton=False):
        """Main plotting function.
        Auto-generates parasitic axes in specified unit order."""
        sp = self
        ui = self.parent
        cp = ui.control_panel
        fs = ui.figure_settings

        # Reset subplot to 1 blank host axis
        for ax in sp.axes[1:]: ax.remove()
        sp.axes = [sp.host()]
        sp.host().clear()

        color_index = 0
        style_dict = {}
        lines = []
        labels = []
        if sp.contents is not None:
            self.verify_order()
            for group_name in sp.contents:
                group = ui.groups[group_name]
                df = group.data
                subdf = df[(df.index >= cp.start) & (df.index <= cp.end)]
                for alias in sp.contents[group_name]:
                    try:
                        header = group.alias_dict[alias]
                    except KeyError:
                        header = alias
                    s = group.series(header)

                    # Determine which axes to plot on, depending on sp.order
                    # Axes are uniquely identified by unit_type and unit
                    # ie, Position [nm] != Position [km]
                    #     != Altitude [km] != Altitude [nm]
                    if (s.unit_type, s.unit) not in sp.order:
                        sp.order.append((s.unit_type, s.unit))
                    ax_index = sp.order.index((s.unit_type, s.unit))
                    # add parasitic axes as needed
                    while len(sp.axes)-1 < ax_index:
                        par = sp.host().twinx()
                        sp.axes.append(par)
                    ax = sp.axes[ax_index]

                    # Turning skeleton on sets up the axes correctly
                    # but doesn't plot any data.
                    if not skeleton:
                        # Manage colors and styles
                        if sp.color_coord:
                            # keep track of # of plotted series per unit type
                            if s.unit_type not in style_dict:
                                style_dict[s.unit_type] = 0
                            style_counter = style_dict[s.unit_type]
                            style_dict[s.unit_type] = style_counter+1
                            style = fs.markers[style_counter%len(fs.markers)]
                            color = fs.color_dict[s.unit_type]
                            ax.yaxis.label.set_color(color)
                            ax.tick_params(axis='y', labelcolor=color)
                        # set color to rotate through default colormap
                        # (otherwise colormap is done per axis)
                        else:
                            color='C'+str(color_index%10)
                            color_index += 1
                            style = 'o'
                            labelcolor = ui.current_rcs['axes.labelcolor']
                            ax.yaxis.label.set_color(labelcolor)
                            ax.tick_params(axis='y', labelcolor=labelcolor)

                        # Fetch data to plot from references in sp.contents
                        data = subdf[header]
                        n = len(data.index)
                        d = fs.density.value()/100
                        thin = np.linspace(0, n-1, num=int(n*d), dtype=int)
                        data = data.iloc[thin]

                        data = data.map(lambda x: x*s.scale)

                        if fs.scatter.isChecked():
                            line, = ax.plot(data, style, color=color,
                                            markersize=fs.dot_size.value(),
                                            markeredgewidth=fs.dot_size.value(),
                                            linestyle='None')
                        else:
                            line, = ax.plot(data, color=color)
                        lines.append(line)
                        labels.append(alias)
                        # set ylabel to formal unit description
                        if s.unit_type:  # is not None
                            if s.unit:
                                ylabel = '{} [{}]'.format(s.unit_type, s.unit)
                            else:
                                ylabel = s.unit_type
                        else:
                            if s.unit:
                                ylabel = '[{}]'.format(s.unit)
                            else:
                                ylabel = None
                        ax.set_ylabel(ylabel, fontsize=fs.label_size.value())

#                         ax.set_ylim(sp.y_limits[ax])

            # Offset parasitic axes
            offset = fs.axis_offset.value()
            for i, ax in enumerate(sp.axes[1:]):
                self.make_patch_spines_invisible(ax)
                ax.spines["right"].set_visible(True)
                ax.spines["right"].set_position(("axes", 1+offset*(i)))

            # Create and offset legend
            if sp.legend and sp.contents:
                if self.location == 'Outside Right':
                    npars = len(sp.axes[1:])
                    bbox = (1+offset*npars, 0.5)
                elif self.location == 'Outside Top':
                    bbox = (0.5, 1)
                else:
                    bbox = (0, 0, 1, 1)
                sp.host().legend(lines, labels,
                       loc=cp.locations[self.location],
                       bbox_to_anchor=bbox,
                       ncol=self.ncols,
                       markerscale=10,
                       framealpha=1.0)
