
import pandas as pd
import importlib
import queue
from tabulate import tabulate
import os
import time as time
import threading

import DataBaseControl.CSV_file_functions as cff

csv_file = 'DataBaseControl/Test_CSV.csv'

experiment = cff.Experiment(csv_file)

experiment.module.setup()

experiment.module.run_script()


