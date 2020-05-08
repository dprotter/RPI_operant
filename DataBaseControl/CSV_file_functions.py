
import pandas as pd
import importlib
import queue
from tabulate import tabulate
import os
import time as time


class Experiment:
    def __init__(self, csv_location, output_loc = None, start_index = 0):
        self.file = csv_location
        self.location = start_index
        self.experiment_status = pd.read_csv(self.file)
        self.unfinished = self.experiment_status.loc[experiment_status.done != True]
        self.unfinished_loc = 0
        if output_loc == None:
            output_loc = '/home/pi/Documents/'
        
        #here we get the index value in the dataframe of our next experiment, 
        #starting with the first experiment listed as unfinished. 
        self.next_exp_index = unfinished.index.values[unfinished_loc]
        self.next_vole = experiment_status.iloc[next_exp_index].vole
        self.next_script = experiment_status.iloc[next_exp_index].script
        self.module = None
        



    


    print(f'next_script: {next_script}')
    next_day = experiment_status.iloc[next_exp_index].day
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
        
        self.experiment_status.loc[experiment_status.index == next_exp_index, 'experiment_status']= 'skipped'
        self.experiment_status.to_csv(csv_path, index = False)

        #of the list of unfinished indexes, start at the min and move through.
        unfinished_loc+=1
        next_exp_index = unfinished.index.values[unfinished_loc]

        next_vole = experiment_status.iloc[next_exp_index].vole
        next_script = experiment_status.iloc[next_exp_index].script
        next_day = experiment_status.iloc[next_exp_index].day

        #dynamically reload the module with the new vole info.
        spec = importlib.util.spec_from_file_location(next_script,
                    f'/home/pi/RPI_operant/{next_script}.py')
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)

    def choose_unfinished():
        '''check if this script has previously be run'''
        global next_script
        global next_vole
        global next_exp_index
        global experiment_status
        global module

        print(f'''script {next_script} for vole {next_vole} may have previously been run.
        only {experiment_status.iloc[next_exp_index].completed_rounds} of
        {experiment_status.iloc[next_exp_index].rounds} were completed. \n\n''')

        rounds_left = (experiment_status.iloc[next_exp_index].rounds -
                        experiment_status.iloc[next_exp_index].completed_rounds)
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
            experiment_status = insert_row(experiment_status, next_exp_index+1, row_values = {})

            #copy the old row to the new row, reset soem values
            experiment_status.iloc[next_exp_index+1] = experiment_status.iloc[next_exp_index]
            experiment_status.iloc[next_exp_index+1].completed_rounds = 0
            experiment_status.iloc[next_exp_index+1].file = ''
            experiment_status.iloc[next_exp_index+1].done = ''

            experiment_status.to_csv(csv_path, index = False)

            next_vole = experiment_status.iloc[next_exp_index+1].vole
            next_script = experiment_status.iloc[next_exp_index+1].script
            next_day = experiment_status.iloc[next_exp_index+1].day
            next_exp_index = next_exp_index + 1

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
        global next_exp_index
        global csv_path

        experiment_status.loc[experiment_status.index ==next_exp_index, 'completed_rounds'] = round_number

        experiment_status.to_csv(csv_path, index = False)