import numpy as np
import pandas as pd
import csv
import matplotlib.pyplot as plt
import os
from datetime import datetime

def get_latency(file = None):
    input = pd.read_csv(file, skiprows=1, header = 0)
    input.columns = ['Event', 'Time']
    disp = input.loc[input['Event'] == 'Pellet dispensed']
    retr = input.loc[input['Event'] == 'Pellet retrieved']

    #great, every dispensed pellet has a retrieved buddy
    if len(disp) == len(retr):
        lat = retr['Time'].values - disp['Time'].values
    #the last dispensed pellet was never retrieved
    elif len(disp) == len(retr) + 1:
        lat = retr['Time'].values - disp['Time'].values[:-1]
    #something else wrong, manually check
    else:
        print('dispense and retrieve length mismatch for: ')
        print(file)
        return ''
    return lat

def parse_file(file = None):
    with open(file) as f:
        read = csv.reader(f)
        head = next(read)
    header_out = {}
    for val in head:
        k, v = val.split(': ')
        header_out[k] = v
    header_out['latency'] = get_latency(file)
    return(header_out)

def assemble_names(directory, suppress_output = True):
    '''return a list of paths to files to parse'''
    os.chdir(directory)

    #create an empty 2d list
    out_names = []

    #this will assemble a list of ALL filenames for images, sorted by timestamp of acquisition
    for root, dirs, files in os.walk(directory):
        out = [os.path.join(root, f) for f in sorted(files)
               if not f.startswith('.') if f.endswith('.csv')]
        out_names += out
    return out_names



names = assemble_names('/Users/davidprotter/Documents/Donaldson Lab/Operant Data/First Test of v2 chamber')

all_files =  [parse_file(f) for f in names]
all_files
latencies = {}
for file in all_files:
    this_vole = file['vole']
    if this_vole in latencies.keys():
        latencies[this_vole][file['date']] = file['latency']
    else:
        latencies[this_vole] = {}
        latencies[this_vole][file['date']] = file['latency']

latencies
for animal in latencies.keys():
    dates = sorted(latencies[animal].keys())
    ani = latencies[animal]
    fig, ax = plt.subplots()
    ax.set_title(animal)
    ax.set_xlabel('round')
    ax.set_ylabel('Latency (s)')
    rounds = [0,0]
    for date in dates:
        print(date)
        rounds[0] = rounds[1]
        rounds[1] = rounds[1] + len(ani[date])
        ax.plot(range(rounds[0], rounds[1]), ani[date])
    plt.show()

#first_date = datetime.strptime(one['date'], "%Y-%m-%d %H:%M:%S.%f")
