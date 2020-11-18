import pandas as pd

def append_name_general(input_name, append_str):
        vals = input_name.split('.')
        return vals[0] + '_' + append_str + '.' + vals[1]

def run_analysis_script(filepath):

