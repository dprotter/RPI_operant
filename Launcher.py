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
import tabulate
import os
print(os.cwd())
def insert_row(row_number, df, row_values):
    df_top_copy = df.loc[df.index<=row_number].copy()
    df_bottom_copy = df.loc[df.index>=row_number].copy()
    df_bottom_copy.index = df_bottom_copy.index + 1
    if row_values!=None:
        new_row_cols = row_values.keys()

    for col in df.columns:
        if col in new_row_cols:
            df_top_copy.loc[df_top_copy.index == row_number, col] = row_values[col]
        else:
            df_top_copy.loc[df_top_copy.index == row_number, col]=''

    # return the dataframe
    return df_top_copy.append(df_bottom_copy)

def skip_vole():
    experiment_status.iloc[next_exp].experiment_status = 'skipped'
    experiment_status.to_csv(csv_path)

    #of the list of unfinished indexes, start at the min and move through.
    next_exp = unfinished.index.values[loc]
    loc+=1

    next_vole = experiment_status.iloc[next_exp].vole
    next_script = experiment_status.iloc[next_exp].script
    next_day = experiment_status.iloc[next_exp].day

def choose_unfinished(index, mod):
    '''check if this script has previously be run'''
    print(f'''script {next_script} for vole {next_vole} may have previously been run.
    only {experiment_status.iloc[next_exp].completed_rounds} of
    {experiment_status.iloc[next_exp].rounds} were completed. \n\n''')

    rounds_left = (experiment_status.iloc[next_exp].rounds -
                     experiment_status.iloc[next_exp].completed_rounds)
    valid = False
    while valid == False:
        rr = input(f'''Should I: run {next_scipt} for {rounds_left} more rounds (<y>) \n
                        restart from round 0 (<r>)\n
                        skip to next vole (<s>)\n''')
        if rr not in ['y','r','s']:
            print('Ooops, that wasnt a valid entry. use only: [y,r,s]')
        else:
            valid = True

    if rr == 'y':
        mod.key_values_def['rounds'] = rounds_left
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

        experiment_status.to_csv(csv_path)

        next_vole = experiment_status.iloc[next_exp+1].vole
        next_script = experiment_status.iloc[next_exp+1].script
        next_day = experiment_status.iloc[next_exp+1].day
        next_exp = next_exp + 1

def modify_vars(var_list, mod):
    defs = [[i, val, mod.key_values_def[val]] for i, val in enumerate(mod.key_val_names_order)]
    defs += [-1, 'done','']
    print(tabulate(defs), header = ['var name', 'var def'], tablefmt = 'grid')

    choice = int(input('which will you modify?\n'))

    while choice != -1:
        key = mod.key_val_names_order[choice]

        val = int(f'print new value for {key}?\n')
        mod.key_values_def[key] = val

        print('\n\n******************\n\n')

        defs = [[i, val, mod.key_values_def[val]] for i, val in enumerate(mod.key_val_names_order)]
        defs += [-1, 'done','']
        print(tabulate(defs), header = ['var name', 'var def'], tablefmt = 'grid')

        choice = int(input('which will you modify?\n'))

def update_vars(var_change_list, mod):
    '''take a csv string <'key:val,key2:val2,....'> of vals and update the key values in the module'''
    vals = {v.split(':')[0]:v.split(':')[1] for v in var_change_list.split(',')}
    for key in vals.keys():
        mod.key_values_def[key] = vals[key]

csv_path = 'csv_test.csv'
experiment_status = pd.read_csv(csv_path)

unfinished = experiment_status.loc[experiment_status.Done != 'y']

loc = 0
next_exp = unfinished.index.values[loc]

next_vole = experiment_status.iloc[next_exp].vole
next_script = experiment_status.iloc[next_exp].script
next_day = experiment_status.iloc[next_exp].day
updated_rounds = None


#present the information of this script to the user, allow them to make changes
user_accepts = False
while user_accepts == False:

    #dynamically import the script as a module
    spec = importlib.util.spec_from_file_location(next_script,
                f'/home/pi/RPI_Operant/{next_script}.py')
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)

    #if the user has defined modified variables, update the module.
    if experiment_status.iloc[next_exp].modified_vars!=None:
        update_vars(experiment_status.iloc[next_exp].modified_vars, module)

    if experiment_status.iloc[next_exp].completed_rounds != 0:
        choose_unfinished(loc,module)

    defs = [[val, module.key_values_def[val]] for val in module.key_val_names_order]

    print(f'''ok, looks like vole {next_vole} is up for day {next_day}
                         using script {next_script}. \n ''')
    print('do these settings look good? \n')
    print(tabulate(defs), header = ['var name', 'var def'], tablefmt = 'grid')


    valid = False
    while valid == False:
        rr = input(f'''Should I: run as is (<y>) \n
                        modify vars (<v>)\n
                        skip to next vole (<s>)\n''')
        if rr not in ['y','v','s']:
            print('Ooops, that wasnt a valid entry. use only: [y,r,s]')
        else:
            valid = True
    if rr == 'y':
        user_accepts = True
    elif rr == 'v':
        modify_vars(defs, module)
    else:
        skip_vole()
