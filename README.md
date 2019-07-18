# Telemetry-Grapher
A graphical user interface that streamlines the process of transforming timeseries data collected from sensors into meaningful graphical presentations.
## Features
- Intuitive data wrangling for ugly csv files with:
  - Inconsistent timestamp formats
  - Garbage mixed in with real numerical data
  - Labels not in the first row
  - Timestamps not in the first column
- Export nicely formatted data 
- Control over individual dataseries
- Dynamic Matplotlib based plotting
- Automatically generated secondary y-axes

## Getting Started
Simply download or clone the repository and run the `__main__.py` file to launch the GUI. If you have Python 3 and PyQt5 installed, it should run right out of the box. All other dependencies are standard Python packages.

# User Guide
## Main Window
The figure you're currently working on is shown in the center of the main window. Simply click on a subplot to select it, and elsewhere within the figure to deselect. Ctrl+Click and Shift+Click are supported for multiselection. A future version of this program will feature excel-sheets-style figures, so you can work on multiple figures in the same session.
### Series Display
When you load data groups into the main window (see *Data Manager* below), they'll be displayed hierarchically in the *Unplotted Series* tree, and then you can add or remove series from one subplot at a time. You can see the contents of a subplot by selecting it in the main window.
### Figure Settings
- *Figure Dimensions*: Controls the padding, spacing between subplots, and secondary axis offset in units between 0.0 and 1.0, where 1.0 is the width/height of the figure. *Weights* refers to the relative height proportions of the subplots.
- *Grid Settings*: Toggles major/minor X/Y gridlines for the entire current figure
- *Plot Settings*: Choose between scatter and line plot styles, and adjust the marker size for scatter plots. Lowering the plot density is very helpful when you have a lot of data to plot and matplotlib starts to slow down. It'll automatically be restored to 100% when you save the figure. The timestamp controls refer to the earliest/latest dates for which data will be plotted, not necessarily the start/end points of the X-axis. If your data has gaps, the start/end points may be respectively later/earlier than the timestamp controls display.
- *Text Settings*: Controls the font size of various labels in the figure and the X-axis tick rotation angle. Currently, the font style is set and can only be changed in `__config.json__`. **Timestamp Format** opens a dialog which allows you to control the X-axis datetime format and includes a handy syntax reference.
- *Unit Type Colors*: Determines the color associated with each unit type to be used when **Color Coordinate** is active (see *Legend Toolbar* below). Click on a color button to customize it.
### Subplot Toolbar
- **Insert Subplot**: Inserts a blank subplot below the selected subplot, or at the bottom of the figure if zero or multiple subplots are selected.
- **Delete Subplot**: Deletes selected subplots and returns their contents to the *Unplotted Series* tree.
- **Clear Subplot**: Removes all series from selected subplots.
- **Cycle Axes**: Cycles through the possible orders of the secondary axes of the selected subplots.
- **Promote Subplot**: Move the selected subplot up one position.
- **Demote Subplot**: Move the selected subplot down one position.
### Legend Toolbar
- **Color Coordinate**: Toggle color coordination of series by unit type (not unit) in the selected subplots. When active, series of the same unit type are differentiated by their marker style.
- **Toggle Legend**: Show/hide the legend of selected subplots.
- **Toggle Legend Units**: Include/exclude series units in the legends of selected subplots.
- **Legend Location**: Determines where the legend is shown for each of the selected subplots relative to the subplot itself. Extra figure padding space is automatically allotted for legends shown at 'Outside Right'.
- **Legend Columns**: Indicates the number of columns the legends of the selected subplots should have.
### Axes Toolbar
- **Current Axis**: Indicates which axis of the selected subplot to be modified.
- **Toggle Log Scale**: Toggles between linear and logarithmic scales.
- **Toggle Autoscaling**: When active, Matplotlib determines the Y-axis limits based on the data extents. When deactivated, the displayed Y-axis limits become the axis' custom limits and won't be changed until the user explicitly changes them or until the button is reactivated. These custom limits are preserved when this button is toggled.
- **Y-Axis Min**: Displays the upper Y-axis limit for the currently indicated axis. When enabled, changing this value changes the custom limits of the currently indicated axis.
- **Y-Axis Max**: Displays the lower Y-axis limit for the currently indicated axis. When enabled, changing this value changes the custom limits of the currently indicated axis.
## Data Manager
This will be your first step after launching the GUI - it's where you'll import and configure your data in groups before saving it to the main window. You can always access it from the main window's Tools menu or by the keyboard shortcut Ctrl+D.
### File Grouping
This tab allows you to organize your files into groups. A file can be part of more than one group, but a group cannot contain the same file twice. Groups can be renamed by double clicking on their entry in the list of imported groups.
1. Use the browse button to navigate to the directory containing your csv files, or enter one manually. Confirm to display all .csv and .zip files in the specified directory (zip files should contain exactly one csv)
2. Add files to your group and give it a name.
3. Click **Import Group** to launch the Review Import Settings dialog.
### Review Import Settings
Here's where you can visually configure import parameters for each file in your group. Select one parameter at a time to preview the associated file's contents. Review each file's parameters until your column labels are highlighted in blue and your timestamp column is highlighted in orange, then press **Confirm**. Files retain their import parameters after a successful import, so if you want to use the same file in another group, you can pick up where you left off.
- **Auto-Detect**: Let the program pick import parameters for each of the selected files.
- **Reset**: Return the import parameters of the selected files to what they were when the dialog opened.
  
Note: You can copy/paste cells from one row at a time to other rows, provided that the source and destination widths are the same. (ie; an R1xC1 selection copy/pastes onto an R2xC2 selection if R1 = 1 and C1 = C2)
### Series Configuration
Switch over to the Series Configuration tab to see and edit the data series of the group you just created. Upon importing a group, the program will try to parse the unit out of the column header and use the rest of the header as the alias (ie; header = 'SoupTemp [degC]' -> alias = 'SoupTemp', unit = '°C').

Series Attributes:
- *Keep*: Toggle whether or not to include the series in the main window display (you can always add it back later).
- *Scale*: Scaling factor for plotting this series. Useful for fudging mm to cm in the display, for example, but make sure you change the unit accordingly! The original data will not be modified. (SOON TO BE MOVED)
- *Original Header*: Column label as it was loaded from the file. This value will never change.
- *Alias*: If the original header is nonsense, you can give it a more descriptive name to be used in the main window. Leave this field blank to just use the original header.
- *Unit Type*: Dimension of this series' data.
- *Unit*: Specific unit corresponding to the unit type.

Actions:
- **Export DataFrame**: Save the group to a csv file as it's shown in the table, made of only the series you've decided to keep. Column headers will look like 'alias [unit]', so it's easy to parse the next time you want to import it.
- **Reparse Headers**: Rerun the header parsing algorithm for the selected columns.
- **Unit Settings**: See below for dialog explanation.
### Unit Settings
(UNDER CONSTRUCTION)  
If the native units don't describe your data well enough, you can add your own from the Series Configuration tab. Currently, the following options are available:
1. 'Subclass' a base unit type. Select a base unit type to 'inherit' from, and give it a name. No repeats. (ex. Altitude (Position))
2. Declare a default unit type. This can be an existing base unit type, or any other string. If the header parsing algorithm can't identify a unit for a given header, it will assign the default unit type. If it's an existing base unit type, the associated units will be used.
3. Declare a default unit. This can be an existing unit from any base unit type, or any other string. If the header parsing algorithm can't identify a unit for a given header, it will assign the default unit. The unit type will not be assigned, even if the default unit is an existing unit associated with a unit type (ie; declaring the default unit as mm will not implicitly declare the default unit type as Position)
4. Clarify a parsable unit. Here you can let the header parsing algorithm know that newton-meters (conventionally denoted Nm) may be recorded in the column headers as [newton-meters] or [N*m]. Note that you'll override the parsing of an existing unit if you tell the algorithm here to interpret it as something else. (ex. clarifying [nm] to [Nm] means you can't interpret [nm] as nanometers anymore!)
5. Edit the config file and declare your own system of units.
___
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
