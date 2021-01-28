import pandas as pd
import numpy as np
import sys
import os
sys.path.append('/home/pi/RPI_operant/')


def get_data_by_x(metric_df, by_x):
    '''slices a metric  df by animal, experiment, day or combo and returns slice
    metric_df: pandas dataframs of a metric such as total lever presses or pellet latency, cols = [animal, day, value, experiment, file]
    by_x: dict of col names:vals pairs that correspond to columns and the values that the data will be sliced by, col should be str
    returns dataframe copy of sliced data'''

    sli = metric_df #have to make sli before iterating
    for col, val in by_x.items():
        sli = sli.loc[sli[col] == val] 
        #do this how ever many times you need to slice by so you could go by animal, then experiemnt, then day using previous slice each time to narrow it down

    return sli

