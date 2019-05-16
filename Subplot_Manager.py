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

#    def refresh(self):
#        FW = self.parent
#        AF = FW.axes_frame
#        for ax in self.axes[1:]: ax.remove()  # remove parasitic axes from subplot
#        self.axes = [self.host()]  # clear parasitic axes from sp.axes
#        self.host().clear()  # clear host axis of data
#
##        color_index = 0
##        style_dict = {}
##        lines = []
#        if self.contents is not None:
#            for group, aliases_units in self.contents.items():
#                for series, unit in aliases_units.items():
#                    if self.order[0] is None:
#                        self.order[0] = unit  # if no order given, default to sorted order
#                    if unit not in self.order:
#                        self.order.append(unit)  # new units go at the end of the order
#                    ax_index = self.order.index(unit)  # get index of unit in unit order
#                    while len(self.axes) < len(self.order): # extend sp.axes as needed
#                        self.axes.append(self.host().twinx())
#                    ax = self.axes[ax_index]
#                    line, = ax.plot(FW.data[group][header])
#                    ax.set_ylabel(AF.unit_dict[unit])
#        AF.draw()


    def make_patch_spines_invisible(self, ax):
        """see https://matplotlib.org/gallery/ticks_and_spines/multiple_yaxis_with_spines.html"""
        ax.set_frame_on(True)
        ax.patch.set_visible(False)
        for sp in ax.spines.values():
            sp.set_visible(False)

    #ported from old structure in control frame. for reference building refresh method here
    def refresh(self, verbose=True):
        """Main plotting function. Auto-generates parasitic axes in specified unit order."""
        sp = self
        TG = self.parent
        AF = TG.axes_frame
        for ax in sp.axes[1:]: ax.remove()  # remove parasitic axes from subplot
        sp.axes = [sp.host()]  # clear parasitic axes from sp.axes
        sp.host().clear()  # clear host axis of data

        color_index = 0
        style_dict = {}
        lines = []
        labels = []
#        print('sp.axes: ',sp.axes)
#        print('sp.contents: ',sp.contents)
#        print('sp.order: ',sp.order)
#        print('sp.index: ',sp.index,'\n')
        if sp.contents is not None:
            for group, aliases_units in sp.contents.items():
                for alias, unit in aliases_units.items():
                    unit_type = TG.get_unit_type(unit)
#                    print('Alias: {}  Unit: {}'.format(alias,unit))
                    # Determine which axes to plot on, depending on sp.order
                    if sp.order[0] is None:
                        sp.order[0] = unit  # if no order given, default to sorted order
                    if unit not in sp.order:
                        sp.order.append(unit)  # new units go at the end of the order
#                    print('After Order Logic: ',sp.order)
                    ax_index = sp.order.index(unit)  # get index of unit in unit order
#                    print('ax_index: ',ax_index)
#                    print('sp.axes: ',sp.axes)
                    while len(sp.axes)-1 < ax_index: # extend sp.axes as needed
                        par = sp.host().twinx()
                        sp.axes.append(par)
#                    print('sp.axes After Twinx Extension: ',sp.axes)
                    ax = sp.axes[ax_index]  # get axis (parasitic or host) at index of unit

                    # Manage colors and styles
                    if sp.colorCoord:
                        if unit_type not in style_dict:  # keep track of how many series are plotted in each unit to cycle through linestyles(/markerstyles TBI)
                            style_dict[unit_type] = 0
                        style_counter = style_dict[unit_type]
                        style_dict[unit_type] = style_counter+1
                        style = TG.markers[style_counter%len(TG.markers)]
#                        try:  # assign color based on unit, black if undefined
                        color = TG.color_dict[unit_type]
#                        except KeyError:
#                            color = 'k'
#                            print('Unit {} has no assigned color in Axes_Frame.color_dict'.format(unit))

                        ax.yaxis.label.set_color(color)
                    else:  # set color to rotate through default colormap (otherwise colormap is done per axis, not the whole subplot)
                        color='C'+str(color_index%10)
                        color_index += 1
                        style = 'o'
                        ax.yaxis.label.set_color('k')

                    # Fetch data to plot from references in sp.contents
                    try:
                        header = TG.groups[group].alias_dict[alias]
                    except KeyError:
                        header = alias
                    scale = TG.groups[group].series[header].scale
                    data = [x*scale for x in TG.groups[group].data[header]]
                    timestamp = TG.groups[group].data.index
                    line, = ax.plot(timestamp, data,
                                    style, color=color, markersize=TG.dotsize, markeredgewidth=TG.dotsize, linestyle='None')
                    lines.append(line)
                    labels.append(alias)
                    if unit_type is not None:  # if no units, leave axis unlabeled
                        ax.set_ylabel('{} [{}]'.format(unit_type, unit))  # set ylabel to formal unit description

            for i,par in enumerate(sp.axes[1:]):  # offset parasitic axes
                self.make_patch_spines_invisible(par)
                par.spines["right"].set_visible(True)
                par.spines["right"].set_position(("axes", 1+.05*(i)))
            if sp.legend and sp.contents:  # create and offset legend
                if 'i' not in locals(): i = -1
                leg = sp.host().legend(lines, labels, bbox_to_anchor=(1+.05*(i+1), .5), loc="center left", markerscale=10)
        sp.host().grid(b=True, axis='x')


#        base_X = AF.subplots[-1].axes[0]
#        plt.sca(base_X)
#        for sp in AF.subplots:
#            if sp.contents is not None:
#            ticks = sp.host().get_xticklabels()
#            print(sp.index, ticks)
#                break
#        if 'ticks' in locals():
#            print(ticks)
#            base_X.xaxis.set_visible(True)
#            base_X.set_xticklabels(ticks)
#            plt.xticks(rotation=50, ha='right')
#        else:
#            base_X.xaxis.set_visible(False)
#            for sp in AF.subplots:
#                sp.host().grid(b=False, axis='x')

#        fig_not_empty = not all([sp.contents==None for sp in AF.subplots])
#        base_X.xaxis.set_visible(fig_not_empty)
#        plt.grid(b=fig_not_empty, axis='x')


        AF.draw()