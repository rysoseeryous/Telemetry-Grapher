# -*- coding: utf-8 -*-
"""
Created on Thu May  9 09:18:02 2019

@author: seery
"""

# ignore case of input and match
unit_dict = {
        'Position':['nm','μm','mm','cm','m'],
        'Velocity':['mm/s','cm/s','m/s'],
        'Acceleration':['mm/s^2','m/s^2'],  # check how superscripts are parsed
        'Angle':['rad','deg'],
        'Temperature':['°C','°F','degF','degC','K'],
        'Pressure':['mPa','Pa','kPa','MPa','GPa','mbar','bar','kbar','atm','psi','ksi'],
        'Heat':['mJ','J','kJ'],
        'Voltage':['mV','V','kV','MV'],
        'Current':['mA','A','kA'],
        'Resistance':['mΩ','Ω','kΩ','MΩ'],
        'Force':['mN','N','kN'],
        'Torque':['Nmm','Nm','kNm'],
        'Power':['mW','W','kW'],
        }

unit = 'V'
result = None

# use this logic in sp.refresh()?
# what if you have series in mm and cm? FORCE THE USER TO DECLARE ONE AND ONLY ONE UNIT FOR EACH UNIT TYPE FOR THE ENTIRE FIGURE
for e in unit_dict:
    if unit in unit_dict[e]:
        result = e
print(result)

# drop down box will display "mm" and not "Position" for successful parsing
# options in drop down box will be list of supported units ONLY one unit per unit type
# these 'default' unit options can be customized in Settings

if result == None:
    category = 'Voltage'
    if category in unit_dict:
        unit_dict[category].append(unit)
    else:
        unit_dict[category] = [unit]

print(unit_dict)
