import numpy as np
import pandas as pd
import io as io
import re
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D
import math
import seaborn as sns

file = '/Users/davidprotter/Downloads/Naloxone Day 1 AM_4_TCR.TXT'
with open(file) as f:
    #find the format string
    found = False
    frame_rate = None

    while not found:
        line = f.readline()

        if 'Frame Rate' in line:
            frame_rate = float(line.split(':')[1])
        #format line begins with 'Format:'
        if 'Format:' in line:
            found = True

            col_names_r = line.strip().replace('Motion\tOrientation(-pi/2 to pi/2)', 'Motion Orientation(-pi/2 to pi.2)\tUnknown').split('\t')
            col_names_r[0] = 'FrameNum'

        #find which side the partner is on. Animal 2 is always on the left
        if 'animal id' in line.lower():
            newline = f.readline()
            animal_ID = newline.split()[2]
            partner_pos = newline.split()[3]
            test_group = newline.split()[4]

            #figure out who is where
            if partner_pos.lower() == 'l' or partner_pos.lower() == 'left':
                'Partner on left, animal_2 = partner'
                animal_2 = 'partner'
                animal_3 = 'novel'
            else:
                'Partner on right, animal_3 = partner'
                animal_2 = 'novel'
                animal_3 = 'partner'

#skip the header
df = pd.read_table(file, skiprows = 67, header = None)
#get rid of weird empty columns
df.dropna(how = 'all', axis =  'columns', inplace = True)

#rename columns with informative names, like "CenterX(mm)_partner"
new_col = []
for n in col_names_r:

    #if the column not yet in the col name list, add it.
    #first pass is for the test animal
    if not n in new_col:
        new_col.append(n)

    #if the col name plus animal_2 is there, add name plus animal_3
    elif n+'_'+animal_2 in new_col:
        new_col.append(n+'_'+animal_3)

    else:
        new_col.append(n+'_'+animal_2)

df.columns = new_col

for key in df.columns:
    if "Center" in key:
        df[df[key] == -1] = np.nan
df['Time'] = df.FrameNum/frame_rate
zs = df['Time'].astype('float').interpolate()

fig = plt.figure(figsize = (15,10))
ax = fig.add_subplot(111, projection='3d')
ax.plot(xs=df['CenterX(mm)'].astype('float').interpolate(), ys = df['CenterY(mm)'].astype('float').interpolate() , zs = zs, alpha = 1,linewidth = 1, color = 'green')
ax.plot(xs=df['CenterX(mm)_partner'].astype('float').interpolate(), ys = df['CenterY(mm)_partner'].astype('float').interpolate(), zs = zs, alpha = 0.5, linewidth = 0.5, color = 'orange')
ax.plot(xs=df['CenterX(mm)_novel'].astype('float').interpolate(), ys = df['CenterY(mm)_novel'].astype('float').interpolate(), zs = zs , alpha = 0.5,linewidth = 0.5, color = 'blue')
fig.legend(['test', 'partner', 'novel'])
ax.set_title(animal_ID+"   /    "+test_group)
plt.show()
left_cmb = df['EventRule1'].sum()
left_cmb/29.97
right_cmb = df['EventRule2'].sum()
right_cmb/29.97
