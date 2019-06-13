# -*- coding: utf-8 -*-
"""
Created on Mon May  6 14:57:54 2019

@author: seery
"""
class Subplot_Manager():
    """Wrapper around subplot object (host). Keeps track of contents and settings of each subplot."""
    def __init__(self, parent, host, contents={}, order=[None], index=None, legend=False, colorCoord=False):
        self.parent = parent
        self.axes = [host]  # keeps track of parasitic axes
        self.contents = contents # standard contents format: {group: {headers:units}} in the context of display
        self.order = order  # keeps track of preferred unit order
        self.index = index  # convenience attribute
        self.legend = legend  # legend toggle
        self.colorCoord = colorCoord  # color coordination toggle

    def host(self):
        return self.axes[0]

    def make_patch_spines_invisible(self, ax):
        """see https://matplotlib.org/gallery/ticks_and_spines/multiple_yaxis_with_spines.html"""
        ax.set_frame_on(True)
        ax.patch.set_visible(False)
        for sp in ax.spines.values():
            sp.set_visible(False)

    def plot(self, verbose=True):
        """Main plotting function. Auto-generates parasitic axes in specified unit order."""
        sp = self
        TG = self.parent
        CF = TG.control_frame
        FS = TG.figure_settings
        for ax in sp.axes[1:]: ax.remove()  # remove parasitic axes from subplot
        sp.axes = [sp.host()]  # clear parasitic axes from sp.axes
        sp.host().clear()  # clear host axis of data

        color_index = 0
        style_dict = {}
        lines = []
        labels = []
        if sp.contents is not None:
            for group, aliases_units in sp.contents.items():
                df = TG.groups[group].data
                subdf = df[(df.index >= CF.start) & (df.index <= CF.end)]  # filter by start/end time
                for alias, unit in aliases_units.items():

                    # Determine which axes to plot on, depending on sp.order
                    if sp.order[0] is None:
                        sp.order[0] = unit  # if no order given, default to sorted order
                    if unit not in sp.order:
                        sp.order.append(unit)  # new units go at the end of the order
                    ax_index = sp.order.index(unit)  # get index of unit in unit order
                    while len(sp.axes)-1 < ax_index: # extend sp.axes as needed
                        par = sp.host().twinx()
                        sp.axes.append(par)
                    ax = sp.axes[ax_index]  # get axis (parasitic or host) at index of unit

                    # Manage colors and styles
                    unit_type = TG.get_unit_type(unit)
                    if sp.colorCoord:
                        if unit_type not in style_dict:  # keep track of how many series are plotted in each unit to cycle through linestyles(/markerstyles TBI)
                            style_dict[unit_type] = 0
                        style_counter = style_dict[unit_type]
                        style_dict[unit_type] = style_counter+1
                        style = TG.markers[style_counter%len(TG.markers)]
                        color = TG.color_dict[unit_type]
                        ax.yaxis.label.set_color(color)
                    else:  # set color to rotate through default colormap (otherwise colormap is done per axis, not the whole subplot)
                        color='C'+str(color_index%10)
                        color_index += 1
                        style = 'o'
                        ax.yaxis.label.set_color(TG.current_rcs['axis.labelcolor'])

                    # Fetch data to plot from references in sp.contents
                    try:
                        header = TG.groups[group].alias_dict[alias]
                    except KeyError:
                        header = alias
                    scale = TG.groups[group].series[header].scale
                    data = [x*scale for x in subdf[header]]
                    timestamp = subdf.index
                    line, = ax.plot(timestamp, data,
                                    style, color=color, markersize=CF.dotsize, markeredgewidth=CF.dotsize, linestyle='None')
                    lines.append(line)
                    labels.append(alias)
                    if unit_type is not None:  # if no units, leave axis unlabeled
                        ax.set_ylabel('{} [{}]'.format(unit_type, unit), fontsize=FS.labelSize.value())  # set ylabel to formal unit description

            offset = FS.parOffset.value()
            for i,par in enumerate(sp.axes[1:]):  # offset parasitic axes
                self.make_patch_spines_invisible(par)
                par.spines["right"].set_visible(True)
                par.spines["right"].set_position(("axes", 1+offset*(i)))

            npars = len(sp.axes[1:])
            if sp.legend and sp.contents:  # create and offset legend
                sp.host().legend(lines, labels,
                       bbox_to_anchor=(1+offset*npars, .5),
                       loc="center left", markerscale=10)
