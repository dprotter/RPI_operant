''''in theory this launcher will live in the folder where all of the data
will be stored, along with the csv file of what were doing.'''



'''general idea:
check each time with the CSV as to who is the last completed script.
we will record rounds completed as we go along. if we need to complete something
that was closed out, thats ok, we can just change the number of rounds after importing
the script, when we start it. we just need the absolute location of the script to
import it.

update and save the csv using pandas each round. if we finish a script, note it
as done.

'''

import pandas as pd
import importlib
import queue
from tabulate import tabulate
import os
import time as time
import threading

os.chdir('/home/pi/RPI_operant/')

csv_path = '/home/pi/iter2_test/csv_test.csv'
output_dir = '/home/pi/iter2_test/output/'
experiment_status = pd.read_csv(csv_path)

unfinished = experiment_status.loc[experiment_status.done != 'y']
print(unfinished)
unfinished_loc = 0

#use the index to select the row for the next experiment
next_exp = unfinished.index.values[unfinished_loc]

next_vole = experiment_status.iloc[next_exp].vole
next_script = experiment_status.iloc[next_exp].script
print(f'next_script: {next_script}')
next_day = experiment_status.iloc[next_exp].day
updated_rounds = None


def insert_row(df, row_number,  row_values):
    df_top_copy = df.loc[df.index<=row_number].copy()
    df_bottom_copy = df.loc[df.index>=row_number].copy()
    df_bottom_copy.index = df_bottom_copy.index + 1
    if row_values!=None:
        new_row_cols = row_values.keys()

    for col in df.columns:
        if col in new_row_cols:
            df_top_copy.loc[df_top_copy.experiment_status.index ==row_number, col] = row_values[col]
        else:
            df_top_copy.loc[df_top_copy.experiment_status.index ==row_number, col]=''

    # return the dataframe
    return df_top_copy.append(df_bottom_copy)

def skip_vole():
    global module
    experiment_status.loc[experiment_status.index == next_exp, 'experiment_status']= 'skipped'
    experiment_status.to_csv(csv_path, index = False)

    #of the list of unfinished indexes, start at the min and move through.
    unfinished_loc+=1
    next_exp = unfinished.index.values[unfinished_loc]

    next_vole = experiment_status.iloc[next_exp].vole
    next_script = experiment_status.iloc[next_exp].script
    next_day = experiment_status.iloc[next_exp].day

    #dynamically reload the module with the new vole info.
    spec = importlib.util.spec_from_file_location(next_script,
                f'/home/pi/RPI_operant/{next_script}.py')
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)

def choose_unfinished():
    '''check if this script has previously be run'''
    global next_script
    global next_vole
    global next_exp
    global experiment_status
    global module

    print(f'''script {next_script} for vole {next_vole} may have previously been run.
    only {experiment_status.iloc[next_exp].completed_rounds} of
    {experiment_status.iloc[next_exp].rounds} were completed. \n\n''')

    rounds_left = (experiment_status.iloc[next_exp].rounds -
                     experiment_status.iloc[next_exp].completed_rounds)
    valid = False
    while valid == False:
        rr = input(f'''Should I: run {next_script} for {rounds_left} more rounds (<y>) \n
                        restart from round 0 (<r>)\n
                        skip to next vole (<s>)\n''')
        if rr not in ['y','r','s']:
            print('Ooops, that wasnt a valid entry. use only: [y,r,s]')
        else:
            valid = True

    if rr == 'y':
        module.key_values['num_rounds'] = rounds_left
    elif rr == 's':
        skip_vole()

    elif rr == 'r':
        #we need to make a copy of the current row.
        experiment_status = insert_row(experiment_status, next_exp+1, row_values = {})

        #copy the old row to the new row, reset soem values
        experiment_status.iloc[next_exp+1] = experiment_status.iloc[next_exp]
        experiment_status.iloc[next_exp+1].completed_rounds = 0
        experiment_status.iloc[next_exp+1].file = ''
        experiment_status.iloc[next_exp+1].done = ''

        experiment_status.to_csv(csv_path, index = False)

        next_vole = experiment_status.iloc[next_exp+1].vole
        next_script = experiment_status.iloc[next_exp+1].script
        next_day = experiment_status.iloc[next_exp+1].day
        next_exp = next_exp + 1

def modify_vars():
    '''give the user the opportunity to update the module values before running'''
    global module

    defs = [[i, val, module.key_values_def[val],module.key_values[val]] for i, val in enumerate(module.key_val_names_order)]
    defs += [[-1, 'done','','']]
    print(defs)
    print(tabulate(defs, headers = ['select','var name', 'var def', 'var value'], tablefmt = 'grid'))

    choice = int(input('which will you modify?\n'))


    while choice != -1:
        '''!!!implement a check on input here'''
        key = module.key_val_names_order[choice]

        val = int(input(f'new value for {key}?\n'))
        '''!!!implement a check on input here'''
        module.key_values[key] = val

        print('\n\n******************\n\n')

        defs = [[i, val, module.key_values_def[val],module.key_values[val]] for i, val in enumerate(module.key_val_names_order)]
        defs += [[-1, 'done','']]
        print(tabulate(defs, headers = ['select','var name', 'var def', 'var value'], tablefmt = 'grid'))

        choice = int(input('which will you modify?\n'))

def update_vars(var_change_list):
    '''take a csv string <'key:val,key2:val2,....'> of vals and update the key values in the module'''
    global module

    vals = {v.split(':')[0]:v.split(':')[1] for v in var_change_list.split(',')}
    for key in vals.keys():
        module.key_values[key] = vals[key]

def update_rounds(round_number):
    global experiment_status
    global next_exp
    global csv_path

    experiment_status.loc[experiment_status.index ==next_exp, 'completed_rounds'] = round_number

    experiment_status.to_csv(csv_path, index = False)


#present the information of this script to the user, allow them to make changes
user_accepts = False

#dynamically import the script as a module
spec = importlib.util.spec_from_file_location(next_script,
            f'/home/pi/RPI_operant/{next_script}.py')
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)

while user_accepts == False:

    #if the user has defined modified variables, update the module.
    if  pd.notna(experiment_status.iloc[next_exp].modified_vars):
        print(f'{experiment_status.iloc[next_exp].modified_vars}')
        update_vars(experiment_status.iloc[next_exp].modified_vars)

    #are there rounds alread completed for this file?
    cr = experiment_status.iloc[next_exp].completed_rounds
    if  cr != 0 and pd.notna(cr):
        choose_unfinished()

    defs = [[val, module.key_values_def[val], module.key_values[val]] for val in module.key_val_names_order]

    print(f'''ok, looks like vole {next_vole} is up for day {next_day}
                         using script {next_script}. \n ''')
    print('do these settings look good? \n')
    print(tabulate(defs, headers = ['var name', 'var def', 'var value'], tablefmt = 'grid'))


    valid = False
    while valid == False:
        rr = input(f'''Should I:
                       run as is (<y>) \n
                       modify vars (<v>)\n
                       skip to next vole (<s>)\n''')
        if rr not in ['y','v','s']:
            print('Ooops, that wasnt a valid entry. use only: [y,r,s]')
        else:
            valid = True
    if rr == 'y':
        user_accepts = True
    elif rr == 'v':
        modify_vars()
    else:
        skip_vole()

#deal with number of rounds to run
if pd.isna(experiment_status.iloc[next_exp].rounds):
    num_rounds = module.key_values['num_rounds']
    experiment_status.loc[experiment_status.index == next_exp, 'rounds'] = num_rounds

    print(f'no rounds in experiment status. setting to {num_rounds}')

    experiment_status.to_csv(csv_path, index = False)
else:
    num_rounds = module.key_values['num_rounds']
    print(f'rounds isnt nan, its {num_rounds}')
    module.key_values['num_rounds'] = int(experiment_status.iloc[next_exp].rounds)

#get the file name for the output file
experiment_status.loc[experiment_status.index == next_exp, 'file'] = module.save_path
#get and define the values we will pass to the module to setup. Most of these
#will get passed along to the csv writer that will write the output file
module.comms_queue = queue.Queue()
user = experiment_status.iloc[next_exp].user
setup_dict = {'vole':next_vole,'day':next_day, 'experiment':next_script,
            'user':user, 'output_directory':output_dir}

module.setup(setup_dict)

#setup a thread to run our target script
script_thread = threading.Thread(target = module.run_script,daemon = True)
script_thread.start()

print('***************made it past the thread start**********')

while script_thread.isAlive() or not module.comms_queue.empty():
    if not module.comms_queue.empty():
        val = module.comms_queue.get()
        if 'round' in val:
            round = val.split(':')[1]
            update_rounds(round)
        else:
            print(f'comms_queue says: {val}')
    time.sleep(0.1)
experiment_status.loc[experiment_status.index == next_exp, 'done'] = 'yes'
print(experiment_status)
print(f'all finished with this experiment')
