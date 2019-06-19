# -*- coding: utf-8 -*-
"""
Created on Thu Jun 13 15:52:45 2019

@author: seery
"""
import numpy as np

class Subplot_Manager():
    """Wrapper around subplot object (host). Keeps track of contents and settings of each subplot."""

    def __init__(self, parent, host, contents={}, order=[], index=None, legend=False, colorCoord=False):
        self.parent = parent
        self.axes = [host]  # keeps track of parasitic axes
        self.contents = contents # standard contents format: {group: [headers]} in the context of display
        self.order = order  # keeps track of plotted unit order
        self.index = index  # convenience attribute
        self.colorCoord = colorCoord  # color coordination toggle
        self.legend = legend  # legend toggle
        self.legendLocation = 'Outside Right'
        self.ncols = 1

    def host(self):
        return self.axes[0]

    def make_patch_spines_invisible(self, ax):
        """see https://matplotlib.org/gallery/ticks_and_spines/multiple_yaxis_with_spines.html"""
        ax.set_frame_on(True)
        ax.patch.set_visible(False)
        for spine in ax.spines.values():
            spine.set_visible(False)

    def verify_order(self):
        sp = self
        AB = self.parent
        identifiers = []
        for group_name in sp.contents:
            group = AB.groups[group_name]
            for alias in sp.contents[group_name]:
                try:
                    header = group.alias_dict[alias]
                except KeyError:
                    header = alias
                unit_type = group.series[header].unit_type
                unit = group.series[header].unit
                identifiers.append((unit_type, unit))
        for elem in sp.order:
            if elem not in identifiers:
                sp.order.remove(elem)


    def plot(self, skeleton=False):
        """Main plotting function. Auto-generates parasitic axes in specified unit order."""
        sp = self
        AB = self.parent
        CF = AB.control_frame
        FS = AB.figure_settings
        for ax in sp.axes[1:]: ax.remove()  # remove parasitic axes from subplot
        sp.axes = [sp.host()]  # clear parasitic axes from sp.axes
        sp.host().clear()  # clear host axis of data

        color_index = 0
        style_dict = {}
        lines = []
        labels = []
        if sp.contents is not None:
            self.verify_order()
            for group_name in sp.contents:
                group = AB.groups[group_name]
                df = group.data
                subdf = df[(df.index >= CF.start) & (df.index <= CF.end)]  # filter by start/end time
                for alias in sp.contents[group_name]:
                    try:
                        header = group.alias_dict[alias]
                    except KeyError:
                        header = alias
                    unit_type = group.series[header].unit_type
                    unit = group.series[header].unit
#                    print('alias: ', alias)
#                    print('unit:  ', unit)
#                    print('order: ', sp.order)

                    # Determine which axes to plot on, depending on sp.order
                    # Axes are uniquely identified by combination of unit_type and unit
                    # ie, Position [nm] != Position [km] != Altitude [km] != Altitude [nm]
#                    if not sp.order:
#                        sp.order[0] = (unit_type, unit)  # if no order given, default to sorted order
                    if (unit_type, unit) not in sp.order:
                        sp.order.append((unit_type, unit))  # new units go at the end of the order
                    ax_index = sp.order.index((unit_type, unit))  # get index of unit in unit order
                    while len(sp.axes)-1 < ax_index: # extend sp.axes as needed
                        par = sp.host().twinx()
                        sp.axes.append(par)
                    ax = sp.axes[ax_index]  # get axis (parasitic or host) at index of unit

                    # Manage colors and styles
                    if not skeleton:  # turning skeleton on sets up the axes correctly but doesn't plot any data. Helps efficiency in series transfer/clear
                        if sp.colorCoord:
                            if unit_type not in style_dict:  # keep track of how many series are plotted in each unit to cycle through linestyles(/markerstyles TBI)
                                style_dict[unit_type] = 0
                            style_counter = style_dict[unit_type]
                            style_dict[unit_type] = style_counter+1
                            style = FS.markers[style_counter%len(FS.markers)]
                            color = FS.color_dict[unit_type]
                            ax.yaxis.label.set_color(color)
                            ax.tick_params(axis='y', labelcolor=color)
                        else:  # set color to rotate through default colormap (otherwise colormap is done per axis, not the whole subplot)
                            color='C'+str(color_index%10)
                            color_index += 1
                            style = 'o'
                            labelcolor = AB.current_rcs['axes.labelcolor']
                            ax.yaxis.label.set_color(labelcolor)
                            ax.tick_params(axis='y', labelcolor=labelcolor)

                        # Fetch data to plot from references in sp.contents
                        s = subdf[header]
                        n = len(s.index)
                        d = FS.density.value()/100
                        thin = np.linspace(0, n-1, num=int(n*d), dtype=int)
                        s = s.iloc[thin]

                        scale = group.series[header].scale
                        s = s.map(lambda x: x*scale)

                        if FS.scatter.isChecked():
                            line, = ax.plot(s, style, color=color, markersize=FS.dotsize.value(), markeredgewidth=FS.dotsize.value(), linestyle='None')
                        else:
                            line, = ax.plot(s, color=color)
                        lines.append(line)
                        labels.append(alias)
                        # set ylabel to formal unit description
                        if unit_type is not None:
                            if unit:
                                ax.set_ylabel('{} [{}]'.format(unit_type, unit), fontsize=FS.labelSize.value())
                            else:
                                ax.set_ylabel(unit_type, fontsize=FS.labelSize.value())
                        else:
                            if unit:
                                ax.set_ylabel('[{}]'.format(unit), fontsize=FS.labelSize.value())

            offset = FS.parOffset.value()
            for i, par in enumerate(sp.axes[1:]):  # offset parasitic axes
                self.make_patch_spines_invisible(par)
                par.spines["right"].set_visible(True)
                par.spines["right"].set_position(("axes", 1+offset*(i)))

            if sp.legend and sp.contents:  # create and offset legend
                location = self.legendLocation
                if location == 'Outside Right':
                    npars = len(sp.axes[1:])
                    bbox = (1+offset*npars, 0.5)
                elif location == 'Outside Top':
                    bbox = (0.5, 1)
                else:
                    bbox = (0, 0, 1, 1)
                sp.host().legend(lines, labels,
                       loc=CF.legend_dict[location],
                       bbox_to_anchor=bbox,
                       ncol=self.ncols,
                       markerscale=10,
                       framealpha = 1.0)



