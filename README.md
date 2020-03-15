# Telemetry Grapher
A graphical user interface that streamlines the process of transforming timeseries data collected from sensors into meaningful graphical presentations.

## Features
- Intuitive data wrangling interface for messy CSV files, dealing with common problems like: 
  - Inconsistent timestamp formats
  - Garbage mixed in with real numerical data
  - Labels not in the first row
  - Timestamps not in the first column
- Data beautification and export 
- Control over individual dataseries
- Dynamic Matplotlib-based plotting with extensive customizability
- Automatically generated secondary y-axes

## Getting Started
Download or clone the repository and run `python -m telemetry_grapher` from your command line to launch the GUI. If you have Python 3 and PyQt5 installed, it should run right out of the box. All other dependencies are standard Python packages.

# User Guide

## Main Window
The figure you're currently working on is shown in the center of the main window. Simply click on a subplot to select it, and elsewhere within the figure to deselect. Ctrl+Click and Shift+Click are supported for multiselection. The MS Excel-style tab interface allows you to start a new figure, close a figure, or rename it.

### Series Display
When you load data groups into the main window (see [Data Manager](#data-manager) below), they'll be displayed hierarchically in the *Unplotted Series* tree. You can then intuitively drag/drop series between the trees and subplots, and from one subplot to another. The contents of the selected subplot are displayed under *Subplot Contents*. Double clicking a series in either tree brings up a dialog which displays basic information and allows you to change its alias, unit details, and scale.
> Note: Each data point is plotted proportionate to its series' scale (default 1). Changing the scale does not change the series values themselves and may be misleading if it is not clearly communicated that a scaling factor has been applied.

### Figure Settings
- *Figure Dimensions*: The first group contains layout controls for padding, the spacing between subplots, and the secondary axis offset in normalized units, where 1.0 is the width/height of the figure. *Weights* refers to the relative height proportions of the subplots - for example, in a figure with three subplots, you could set the topmost subplot to a height twice as high as the others by entering [2, 1, 1] or just 211.
- *Grid Settings*: From here you can toggle major/minor X/Y gridlines and use the sliders to customize the frequency of major and minor ticks, which adapt dynamically to sensible intervals. Ticks are sometimes buggy. I am not a professional software developer. You've been warned.
- *Plot Settings*: General plotting settings can be found here: choose between scatter and line plot styles, and adjust the marker size for scatter plots. Lowering the plot density is very helpful when you have a lot of data to plot and matplotlib starts to slow down. It'll automatically be restored to 100% immediately before the figure is saved. *X Margin* refers to the space between the edges of the subplot and the first/last plotted points, and defaults to 5% of the data extents.
- *Text Settings*: These settings control the font size of various labels in the figure and the X-axis tick rotation angle. Currently, the font style is global and can only be changed in `config.json`. **Timestamp Format** opens a dialog which allows you to control the X-axis datetime format and includes a handy syntax reference.
- *Unit Type Colors*: This table determines the color associated with each unit type, to be used when **Color Coordinate** is active (see [Legend Toolbar](#legend-toolbar) below). Click on a color swatch to customize it.

### Subplot Toolbar
- **Insert Subplot**: Inserts a blank subplot below the selected subplot, or at the bottom of the figure if zero or multiple subplots are selected.
- **Delete Subplot**: Deletes selected subplots and returns their contents to the *Unplotted Series* tree.
- **Clear Subplot**: Removes all series from selected subplots.
- **Cycle Axes**: Cycles through the permutations of the secondary axes of the selected subplots.
- **Promote Subplot**: Moves the selected subplot up one position.
- **Demote Subplot**: Moves the selected subplot down one position.

### Legend Toolbar
- **Color Coordinate**: Toggles color coordination of series by unit type (not unit) in the selected subplots. When active, series of the same unit type are differentiated by their marker style.
- **Toggle Legend**: Shows/hides the legend of selected subplots.
- **Toggle Legend Units**: Includes/excludes series units in the legends of selected subplots.
- **Legend Location**: Determines where the legend is shown for each of the selected subplots relative to the subplot itself. The figure is automatically adjusted to the left to account for any legends shown at 'Outside Right'.
- **Legend Columns**: Indicates the number of columns the legends of the selected subplots should have.

### Axes Toolbar
- **Current Axis**: Indicates which axis of the selected subplot is being targeted in the toolbar.
- **Toggle Log Scale**: Toggles between linear and logarithmic scales.
- **Toggle Autoscaling**: When active, Matplotlib determines the Y-axis limits based on the data extents. When deactivated, the displayed Y-axis limits become the axis' custom limits and won't be changed until the user explicitly changes them or until autoscaling is reactivated. These custom limits are preserved when this button is toggled.
- **Y-Axis Min**: Displays the upper Y-axis limit for the currently indicated axis. When enabled, changing this value changes the custom limits of the currently indicated axis.
- **Y-Axis Max**: Displays the lower Y-axis limit for the currently indicated axis. When enabled, changing this value changes the custom limits of the currently indicated axis.

## Data Manager
This will be your first step after launching the GUI - it's where you'll import and configure your data in groups before saving it to the main window. You can always access it from the main window's Tools menu or by the keyboard shortcut Ctrl+D.

### File Grouping
This tab allows you to organize your files into groups. A file can be part of more than one group, but a group cannot contain the same file twice. Groups can be renamed by double clicking on their entry in the list of imported groups.
1. Use the browse button to navigate to the directory containing your CSV files, or enter one manually. Press Enter to display all .csv and .zip files in the specified directory. (ZIP files should contain exactly one CSV)
2. Add files to your group (double click or drag and drop) and give it a name.
3. Click **Import Group** to launch the [Review Import Settings](#review-import-settings) dialog. Adjust the settings in the dialog until you're satisfied, then click **Confirm** to import the group.
4. If you have multiple figures, you can share imported groups between them by selecting the figure with the drop-down menu and drag/drop into *Figure Groups*.

### Review Import Settings
Here's where you can visually configure import parameters for each file in your group. Select one parameter at a time to preview the associated file's contents. Review each file's parameters until your column labels are highlighted in blue and your timestamp column is highlighted in orange, then press **Confirm**. Files retain their import parameters after a successful import, so if you want to use the same file in another group, you can pick up where you left off.
- **Auto-Detect**: Let the program pick import parameters for each of the selected files.
- **Reset**: Return the import parameters of the selected files to what they were when the dialog opened.
>Note: You can copy/paste cells from one row at a time to other rows, provided that the source and destination widths are the same. (ie; an R1xC1 selection copy/pastes onto an R2xC2 selection if R1 = 1 and C1 = C2)

### Series Configuration
Switch over to the Series Configuration tab to see and edit the data series of the groups you've imported. Upon importing a group, the program will try to determine the each column's units from its header. The parsing algorithm first tries to identify a string between square brackets in the column header and applies a map defined by the clarification table. The resultant unit is then compared against the library of recognized units. If a match is found, then the resultant unit and associated unit type are assigned to the series, and an alias is suggested from the rest of the header. For example, a header 'SoupTemp [degC]' will yield a data series with alias 'SoupTemp', unit '°C', and unit type = 'Temperature'. Read more about how this works under [Unit Settings](#unit-settings).

Series Attributes:
- *Keep*: Whether or not to include the series in the main window display (you can always add it back later).
- *Original Header*: Column label as it was loaded from the file. This value will never change.
- *Alias*: If the original header is nonsense, you can give it a more descriptive name to be used instead. Leave this field blank to just use the original header as-is.
- *Unit Type*: Dimension of this series' data.
- *Unit*: Specific unit corresponding to the unit type.

Actions:
- **Export DataFrame**: Saves the group to a CSV file as it's shown in the table, composed of only the series you've decided to keep. Column headers will look like 'alias [unit]', so it's easy to read and parse if you need to import it later.
- **Reparse Headers**: Reruns the header parsing algorithm for the selected columns. Handy to use after you edit your unit settings and want to reinterpret some data headers.

### Unit Settings
Under this tab, you can specify the dictionary of recognized units and unit types and thus fine-tune the parsing algorithm. Everything in this tab can also be edited directly from the configuration file. Being a future-minded program, the native units are in SI. 

- *Base Units*: A set of native units and associated unit types which cover a broad spectrum of possible data outputs. Native units types can be renamed/deleted, and you can also add/delete/rename native units under each type.
- *Custom Units*: If the base units don't describe your data well enough, you can create brand new ones by double clicking on the '+' symbol. Custom unit types don't necessarily need to have specific units associated with them - this allows you the freedom to label data as things like 'Serial ID' or 'Number of Chickens'. Custom units are referenced before the native units during parsing; for example, you could declare a custom unit type 'Altitude' with associated unit 'km', and the parsing algorithm would respectively interpret the column headers 'Trajectory019 [km]' and 'Aperture5 [mm]' as Altitude and Position, effectively overriding the [km] -> Position path.
- *Clarified Units*: This table serves as a map for the parsing algorithm dealing with column headers which record the same units in a different way. For example, degrees Fahrenheit could be equivalently denoted '°F', 'degF', or just 'F'. Rather than list all the possibilities under the unit type 'Temperature', the latter two are listed in the table and associated with a single representation, so the parsing algorithm knows that all three describe the same thing and can display them all the same way. You can add your own clarifications to the table by clicking **Add**, then pairing a string and a recognized unit.
- *Default Unit Type*: If the parsing algorithm can't identify a unit from a given column header, it will assign the default unit type. This is useful if you happen to know that the majority of your data is of a certain type, but the column headers don't include the units in square brackets. Changing the default unit type loads its associated units into the default unit drop-down menu, although you may opt to leave it unassigned, in case you want to broadly assign a label but no unit. (eg. Unicorn Population)
- *Default Unit*: If the default unit type is assigned in the scenario above, the default unit will also be assigned. For example, if you have twenty column headers, 'Hare01' - 'Hare19' and 'Tortoise [mm/s]', the parsing algorithm will only be able to interpret Tortoise as Velocity [mm/s]. To save time, you should set the default unit type to 'Velocity' and the default unit to [m/s] and then reparse all the headers, so that all the Hare columns default to Velocity [m/s] and the explicitly defined Tortoise column is still parsed correctly.
>Note: It's possible to unintentionally override the parsing of an unrelated unit in two ways, either by clarifying it in the table or creating two identical unit strings under different unit types. For example, telling the algorithm to interpret [nm] as [Nm] in the clarification table precludes the parsing of nanometers. Similarly, if the tree lists [NM] under both Position and Torque, all instances of [NM] in column headers will be interpreted as whichever unit type appears first in the tree. 

## Acknowledgements

Developed by Ryan Seery at:
>Max Planck Institut für Sonnensystemforschung  
>Justus-von-Liebig Weg 3  
>37077, Göttingen 

Stylesheets modified from [BreezeStyleSheets](https://github.com/Alexhuszagh/BreezeStyleSheets).  
Entypo pictograms by Daniel Bruce — www.entypo.com  
Helpful online [JSON editor](https://jsoneditoronline.org/).  
Written with [StackEdit](https://stackedit.io/).  
See also documentation for [Qt](https://doc.qt.io/) and [Matplotlib](https://matplotlib.org/).
