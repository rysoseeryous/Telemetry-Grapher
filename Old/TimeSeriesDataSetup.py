# -*- coding: utf-8 -*-
"""
Created on Thu May  2 10:45:26 2019

@author: seery
"""
import os
import re
import warnings
import IPython.display

import numpy as np
import pandas as pd


def gather_files(path, regexp, SID=None):
    """Returns list of paths of all files in path which match regexp."""
    filelist = []
    for (dirpath, dirnames, filenames) in os.walk(path):
        filelist.extend(filenames)
    assert SID in siddict, 'Please choose SID = 4, 7, 9, or 10.'
    paths = [os.path.join(path, file)
             for file in filelist
             if siddict[SID] in file.split('\\')[-1] and re.match(regexp, file)]
    return paths


def combine_files(filelist, skiprows=None, header_row=0, ts_col=None, dtf=None):
    """Returns dataframe of concatenated data from all files in filelist using ts_col as the index, renamed 'Timestamp'."""
    dflist = []
    for file in filelist:
        data = pd.read_csv(file, skiprows=skiprows, header=header_row, encoding='ISO-8859-1', sep=',', engine='python')
        if verbose: print(file, 'shape info:', data.shape)
        try:
            try:
                ts_name = data.columns[ts_col] # try to convert ts_col to its name (if given as int/position)
            except IndexError:
                ts_name = ts_col
            data.set_index(ts_name, inplace=True) # use ts_col as index
            data.index.names = ['Timestamp'] # rename index 'Timestamp'
        except ValueError:
            print('Could not find column to use as index. Enter column name (string) or position (int).')
            raise
        dflist.append(data)
    df = pd.concat(dflist, axis=0, sort=False)
    # convert pandas date & time column (str) to datetime
    try:
        warnings.filterwarnings('ignore')  # to ignore UserWarning: Discarding nonzero nanoseconds in conversion
        df.index = pd.to_datetime(df.index, format=dtf)
    except ValueError:
        print('\nERROR: datetime formatting does not correspond to the data format\n')
        raise
    return df.sort_index()


def floatify(data):
    """Strip everything but numbers, minus signs, and decimals, and returns data as a float. Returns NaN if not possible."""
    data = re.sub('[^0-9-.]', '', str(data))
    try:
        return float(data)
    except ValueError:
        return np.nan

def days_hours_minutes(timedelta):
    return timedelta.days, timedelta.seconds//3600, (timedelta.seconds//60)%60


def select_span(df, start=None, end=None):
    if start is None and end is None:
        subdf = df
        totalspan = max(df.index)-min(df.index)
        subspan = totalspan
    else:
        try:
            subdf = df[(df.index >= start) & (df.index <= end)]
            totalspan = max(df.index)-min(df.index)
            subspan = pd.to_datetime(end)-pd.to_datetime(start)
        except ValueError:
            print('\nERROR: The selected start and end times are not within the available data, or they are not defined\n')
            raise
    timeinterval = 0; i = 1
    while timeinterval == 0:
        timeinterval = (df.index[i]-df.index[i-1]).total_seconds()
        i += 1

    if verbose:
        print('Data Start:\t', min(df.index))
        print('Data End:\t', max(df.index))
        print('Data Span:\t {} days, {} hours, {} minutes'.format(*days_hours_minutes(totalspan)))
        print('Selected Start:\t', start)
        print('Selected End:\t', end)
        print('Selected Span:\t {} days, {} hours, {} minutes'.format(*days_hours_minutes(subspan)))
        print('Sampling Rate:\t {}s\n'.format(timeinterval))

    return subdf


def cross_section(df, instants, columns=None):
    cols = df.columns if columns is None else columns
    subdf = df.loc[instants, cols]
    subdf = subdf[~subdf.index.duplicated(keep='first')]
    if verbose: IPython.display.display(subdf.transpose())
    return subdf

def PHI_HK_setup(path, regexp, SID=None):
    """Returns dataframe of all files in path that match regexp with floatified relevant data."""
    datafiles = gather_files(path, regexp, SID=SID)
    df = combine_files(datafiles, header_row=0, ts_col='PacketTime', dtf='%Y-%m-%d %H:%M:%S.%f') # in PHI HK, datetime is col "PacketTime"

    # Return df with only columns that start with 'PHI' and can be floatified.
    keep = []
    for col in df.columns:
        if col[0:3] == 'PHI':
            idx = df[col].first_valid_index()
            first_valid_value = df[col].loc[idx] if idx is not None else None
            if np.isfinite(floatify(first_valid_value)): keep.append(col)
    df = df[keep]
    df = df.applymap(floatify)
    return df


def SC_TH_PHI_ITF_setup(path, regexp):
    """Returns dataframe of all files in path that match regexp with floatified relevant data."""
    datafiles = gather_files(path, regexp)
    df = combine_files(datafiles, header_row=1, ts_col=0, dtf='%d/%m/%Y %H:%M')
    df = df.applymap(floatify)
    return df


def SC_TH_PHI_EW_setup(path, regexp):
    """Returns dataframe of all files in path that match regexp with floatified relevant data."""
    datafiles = gather_files(path, regexp)
    df = combine_files(datafiles, header_row=1, ts_col=0, dtf='%d/%m/%Y %H:%M')
    df = df.applymap(floatify)
    return df


def SC_TC_setup(path, regexp):
    """Returns dataframe of all files in path that match regexp with floatified relevant data."""
    datafiles = gather_files(path, regexp)
    df = combine_files(datafiles, skiprows = [2,3], header_row=1, ts_col=0, dtf='%d/%m/%Y %H:%M:%f')
    df = df.applymap(floatify)
    return df

def initialize(telemetry, SID=None):
    if telemetry=='PHI_HK':
        path = r'C:\Users\seery\Documents\German (the person)\PHI_data_housekeeping\CSV'
        df = PHI_HK_setup(path,regexp,SID)
        start = '2018-12-06 00:00'
        end = '2018-12-09 00:00'
    elif telemetry=='SC_TH_PHI_ITF':
        path = r'C:\Users\seery\Documents\German (the person)\SC_data_thermistors'
        sensors = 'PHI_interfaces'
        path = os.path.join(path, sensors)
        df = SC_TH_PHI_ITF_setup(path,regexp)
        start = '2018-12-03 00:00'
        end = '2018-12-15 00:00'
    elif telemetry=='SC_TH_PHI_EW':
        path = r'C:\Users\seery\Documents\German (the person)\SC_data_thermistors'
        sensors = 'PHI_entrance_windows'
        path = os.path.join(path, sensors)
        df = SC_TH_PHI_EW_setup(path,regexp)
        start = '2018-12-03 00:00'
        end = '2018-12-15 00:00'
    elif telemetry=='SC_TC':
        path = r'C:\Users\seery\Documents\German (the person)\SC_data_thermocouples'
        df = SC_TC_setup(path,regexp)
        start = '2018-12-08 00:00'
        end = '2018-12-09 00:00'
    return df, start, end

def declare_headers(df, SID):
    headers = {x:x for x in df.columns}
#     groups = {'All Series':list(df.columns)}
    if SID == 7:
        headers = ({
            'PHI_HPTEMP_FG_OVEN_1': 'PHI OPT FG OVEN 1',
            'PHI_HPTEMP_FG_OVEN_2': 'PHI OPT FG OVEN 2',
            'PHI_HPTEMP_PMP_FDT_1': 'PHI OPT PMP FDT 1',
            'PHI_HPTEMP_PMP_FDT_2': 'PHI OPT PMP FDT 2',
            'PHI_HPTEMP_PMP_HRT_1': 'PHI OPT PMP HRT 1',
            'PHI_HPTEMP_PMP_HRT_2': 'PHI OPT PMP HRT 2',
            'PHI_TEMP_AMHD_1': 'PHI OPT FDT MOTOR',
            'PHI_TEMP_AMHD_2': 'PHI OPT FSM MOTOR',
            'PHI_TEMP_PMP_FDT': 'PHI OPT CT MOTOR',
            'PHI_TEMP_PMP_HRT': 'PHI OPT HRT MOTOR',
            'PHI_TEMP_CT_MOTOR': 'PHI OPT FDT HOUSING',
            'PHI_TEMP_HRT_MOTOR': 'PHI OPT M2 OPT BAFFLE',
            'PHI_TEMP_OPT_1': 'PHI OPT MAIN OPT BAFFLE',
            'PHI_TEMP_OPT_2': 'PHI OPT HPMP HOUSING',
            'PHI_TEMP_MIRROR_1': 'PHI OPT M1 REAR BLOCK',
            'PHI_TEMP_MIRROR_2': 'PHI OPT TT HOUSING',
            'PHI_TEMP_HRT_TT_1': 'PHI OPT HRT TT 1',
            'PHI_TEMP_HRT_TT_2': 'PHI OPT HRT TT 2',
            'PHI_TEMP_FG_1': 'PHI OPT FG 1',
            'PHI_TEMP_FG_2': 'PHI OPT FG 2',
            'PHI_TEMP_FSM_MOTOR': 'PHI ELE AMHD DCDC',
            'PHI_TEMP_FDT_MOTOR': 'PHI ELE AMHD PCB',
            'PHI_TEMP_PCM_MAIN_1': 'PHI ELE PCM MAIN 1',
            'PHI_TEMP_PCM_MAIN_2': 'PHI ELE PCM MAIN 2',
            'PHI_TEMP_PCM_RED_1': 'PHI ELE PCM RED 1',
            'PHI_TEMP_PCM_RED_2': 'PHI ELE PCM RED 2',
            'PHI_TEMP_DPU_1': 'PHI ELE DPU 1',
            'PHI_TEMP_DPU_2': 'PHI ELE DPU 2',
            'PHI_TEMP_TTC': 'PHI ELE TTC',
            'PHI_TEMP_HVPS': 'PHI ELE HVPS',
            'PHI_TEMP_EUNIT_TRP': 'PHI ELE EUNIT TRP',
        })
        keys = list(headers.keys())
        groups = ({
            'PHI_OPT_Mechanisms': [keys[i] for i in [10, 11, 12, 13]],
            'PHI_OPT_HRT_PMP': [keys[i] for i in [4, 5]],
            'PHI_OPT_Group_1': [keys[i] for i in [8, 9, 14, 15]],
            'PHI_OPT_Group_2': [keys[i] for i in [16, 17, 28, 29]],
            'PHI_ELE_Group_1': [keys[i] for i in [20, 21, 22, 23, 30]],
            'PHI_ELE_Group_2': [keys[i] for i in [6, 7, 24, 25, 26, 27]],
        })
    elif SID == 9:
        headers = ({
            'PHI_FPA_FPGA_TEMP': 'PHI OPT FPA FPGA',
            'PHI_FPA_SENSOR_TEMP': 'PHI OPT FPA SENSOR',
            'PHI_CPC_temperature': 'PHI OPT CPC',
        })
        keys = list(headers.keys())
        groups = ({
            'PHI_OPT_FPA': [keys[i] for i in [0, 1, 2]]
        })
    elif SID == 10:
        headers = ({
            'PHI_CTC_fpgaTemp': 'PHI OPT CTC FPGA',
            'PHI_CTC_sensorTemp': 'PHI OPT CTC STAR1000',
        })
        keys = list(headers.keys())
        groups = ({
            'PHI_OPT_CTC': [keys[i] for i in [0, 1]]
        })
    elif SID == 'SC_TH_PHI_ITF':
#         headers = df.columns[1:13].copy()
        keys = df.columns
        groups = ({
            'PHI_OPT_Hot_Elements': [keys[i] for i in [0,1,2,3,4]],
            'PHI_OPT_Cold_Element': [keys[i] for i in [5]],
            'PHI_OPT_SRP': [keys[i] for i in [6, 10, 11]],
            'PHI_ELE_URP': [keys[i] for i in [7,8,9]],
        })
    elif SID == 'SC_TH_PHI_EW':
#         headers = df.columns[1:5].copy()
        keys = df.columns
        groups = ({
            'HRT HREW FT': [keys[i] for i in [0, 1]],
            'FDT HREW FT': [keys[i] for i in [2, 3]],
        })
    elif SID == 'SC_TC':
#         headers = df.columns[1:].copy()
        keys = df.columns
        groups = ({
            'PHI_OPT_Hot_Elements': [keys[i] for i in [3, 4, 5]],
            'PHI_OPT_Cold_Element': [keys[i] for i in [6, 7, 8, 9]],
            'PHI_OPT_SRP': [keys[i] for i in [0, 1]],
            'PHI_ELE_URP': [keys[i] for i in [2]],
        })
    else:
        raise ValueError('Warning: Invalid SID. Please choose from:\n{}\n{}, {}, {}'.format(
            siddict,'"SC_TH_PHI_ITF"', '"SC_TH_PHI_EW"', '"SC_TC"'))

    if verbose:
        print('\nSensors to be plotted:')
        [print('{:3} {:21} {}'.format(str(i), k, headers[k])) for i, k in enumerate(headers)]

    return headers, groups

# Global Controls
siddict = {4:'activePCM', 7:'temperature', 9:'fpa', 10:'iss', None:''}
regexp = re.compile(r'.*\.(csv|zip)')
verbose = False
# Initialize PHI_HK temperatures, voltages, and currents for stack/parasitic plotting tests
temp, start, end = initialize('PHI_HK', 7)
#temp = select_span(temp, start, end)
apcm, start, end = initialize('PHI_HK', 4)
#apcm = select_span(apcm, start, end)

apcm = apcm.loc[:,
    ['PHI_aPCM_V_PRIM',
    'PHI_aPCM_V_AB_pos3V3',
    'PHI_aPCM_V_AB_pos7V',
    'PHI_aPCM_V_AB_pos15V',
    'PHI_aPCM_V_AB_neg15V',
    'PHI_aPCM_I_PRIM',
    'PHI_aPCM_I_HEATER',]
]


dfs = [temp, apcm]
names = ['PHI_HK Temps SID=7', 'PHI_HK aPCM SID=4']
groups = {}
for name, df in zip(names,dfs):
    groups[name] = Group(df, [], [])  #empty source files/paths
#data = dict(zip(names,dfs))

assign_units = [
    ['T']*len(temp.columns),
    ['V','V','V','V','V','I','I',]
]
data_dict = {}
for i, df in enumerate(dfs):
    ncols = len(df.columns)
    units = assign_units[i]
    if ncols != len(units):
        print('DataFrame {} has {} columns, but {} units were specified.'.format(names[i], ncols, len(units)))
        units = []
        for x in range(ncols):
            if x < len(assign_units[i]):
                units.append(assign_units[i][x])
            else:
                units.append('')
    data_dict[names[i]] = dict(zip(df.columns, units))
