#!/usr/bin/python3
import pandas as pd
import importlib
import queue
from tabulate import tabulate
import os
import time as time
import threading

import DataBaseControl.CSV_file_functions as cff
import argparse

parser = argparse.ArgumentParser(description='input io info')
parser.add_argument('--csv_in', '-i',type = str, 
                    help = 'where is the csv experiments file?',
                    action = 'store')
parser.add_argument('--output_loc','-o', type = str, 
                    help = 'where to save output files',
                    action = 'store')

args = parser.parse_args()

if args.csv_in:
    csv_file = args.csv_in
 
else:
    csv_file = 'DataBaseControl/Test_CSV.csv'
print(f'path to csv experiment file: {csv_file}')
if not os.path.isfile(csv_file):
    print('not a valid csvfile. double check that filepath! see ya.')
    exit()

if args.output_loc:
    if not os.path.isdir(args.output_loc):
        selection  = input(f'\n\nhmmm, output location {args.output_loc} doesnt exist. make it? \ne (exit) \ny (make new directory) \nn (use default output location /home/pi/test_outputs/)\n\n')
        selection = selection.lower()
        if not selection in ['y', 'n','e']:
            print('invalid choice. see ya!')
            exit()
        elif selection == 'y':
            os.mkdir(args.output_loc)
            output= args.output_loc
        elif selection == 'n':
            print('ok, saving to default loc.')
            output = None
            time.sleep(2)
        else:
            exit()
    else:
        output = args.output_loc
else:
    output = None

print(f'output to: {output}')
    
experiment = cff.Experiment(csv_file, output_loc = output)

resp = experiment.ask_to_run()

while resp:
    experiment.run()
    experiment.next_experiment()
    resp = experiment.ask_to_run()

print('whew! what a day of experiments!')



