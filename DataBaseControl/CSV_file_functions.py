
import pandas as pd
import importlib
import queue
from tabulate import tabulate
import os
import time as time
import traceback

class Experiment:
    def __init__(self, csv_location, output_loc = None, start_index = 0):
        self.path_to_scripts ='/home/pi/RPI_operant/run_scripts'
        self.file = csv_location
        self.location = start_index
        self.experiment_status = pd.read_csv(self.file)
        
        #list of all unfinished scripts
        self.unfinished = self.experiment_status.loc[self.experiment_status.done != True]
        
        #iterator to access list of unfinished
        self.unfinished_loc = 0
        
        self.cur_row = self.unfinished.iloc[[self.unfinished_loc]]
        
        #here we get the index value in the dataframe of our next experiment, 
        #starting with the first experiment listed as unfinished. 
        self.exp_index = self.cur_row.index.values[self.unfinished_loc]
        
        #sometimes a dictionary is just easier to deal with than a pandas row
        self.vals = {col:self.cur_row[col].values[0] for col in sorted(self.cur_row.columns)}
        if self.vals['experiment_status'] == 'skipped':
            print('this experiment was previously skipped.')
        print(f"next_script: {self.vals['script']}")

        #dynamically reload the module with the new vole info.
        spec = importlib.util.spec_from_file_location(self.vals["script"],
                    f'{self.path_to_scripts}/{self.vals["script"]}.py')
        self.module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(self.module)
        
        #default setup dictionary for this module
        self.default_setup_dict = self.module.default_setup_dict
        
        #setup dictionary for the current experiment row
        self.current_setup_dictionary = self.default_setup_dict
        
        #if passed an explicit save location, use that
        if output_loc:
            self.output_location = output_loc
        else:
            self.output_location = '/home/pi/test_outputs/'
        
        self.current_setup_dictionary['output_directory'] = self.output_location

        #overwrite the default setup dict with values from the csv file
        self.instantiate_experiment()
        #change any values in the modules variable dictionary as necessary from the csv column
        #var_change
        self.modify_vars_from_csv()
      
    def next_experiment(self):
        
        self.unfinished_loc += 1
        self.cur_row = self.unfinished.iloc[[self.unfinished_loc]]
        
        #here we get the index value in the dataframe of our next experiment, 
        #starting with the first experiment listed as unfinished. 
        self.exp_index = self.cur_row.index.values[self.unfinished_loc]
        
        #sometimes a dictionary is just easier to deal with than a pandas row
        self.vals = {col:self.cur_row[col].values[0] for col in sorted(self.cur_row.columns)}
        if self.vals['experiment_status'] == 'skipped':
            print('this experiment was previously skipped.')
        print(f"next_script: {self.vals['script']}")

        #dynamically reload the module with the new vole info.
        spec = importlib.util.spec_from_file_location(self.vals["script"],
                    f'{self.path_to_scripts}/{self.vals["script"]}.py')
        self.module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(self.module)
          
        #overwrite the default setup dict with values from the csv file
        self.instantiate_experiment()
        #change any values in the modules variable dictionary as necessary from the csv column
        #var_change
        self.modify_vars_from_csv()
    
    def modify_vars_from_csv(self):
        '''read and update vars from var_change column of csv'''
        mods = self.vals['var_changes']
        for mod in mods.split(','):
            key, value = mods.split(':')
            try:
                self.module.key_values[key] = value
            except:
                print(f'couldnt update {key} : {value}')
                
    def modify_vars(self, var_dict):
        '''to manually update variables. these will get put in the var_change column, as well'''
        
        for key in var_dict.keys():
            value = var_dict[value]
            try:
                self.module.key_val[choice]
            except:
                print(f'couldnt update {key}:{value}')
                traceback.print_exec()
            
    def instantiate_experiment(self):
        '''take values from the csv file and put them in the setup dict'''   
        for key in self.vals.keys():
            if key in self.current_setup_dictionary:
                self.current_setup_dictionary[key] = self.vals[key]
            else:
                print(f'adding {key}:{self.vals[key]} to setup dictionary')
                self.current_setup_dictionary[key] = self.vals[key]
        
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

        
    def skip_vole(skip_forever = False):
        
        self.experiment_status.loc[experiment_status.index == next_exp_index, 'experiment_status'] = 'skipped'
        if skip_forever:
            self.experiment_status.loc[experiment_status.index == next_exp_index, 'done'] = True
        
        #save the new CSV file, overwritting the old one.
        self.experiment_status.to_csv(self.file, index = False)
        
        #of the list of unfinished indexes, go to the next one
        self.unfinished_loc+=1
        
        #this will update all our class values with our new index_loc
        update_next_experiment()
    
    def ask_to_run(self):
        
        print('\n\n\n\nshould we run this experiment? (y/n)\n\n')
        self.print_vals()
        
        resp = input('').lower()
        
        if resp == 'y':
            return True
        elif resp == 'n': 
            return False
        else:
            print('\n\n\nhmmm, not a valid response, (y/n). try again.')
            return ask_to_run()
        
    
    def print_vals(self):
        print(self.cur_row)
        defs = [[i, val, self.module.key_values_def[val], self.module.key_values[val]] for i, val in enumerate(self.module.key_val_names_order)]
        defs += [[-1, 'done','','']]
        print(tabulate(defs, headers = ['select','var name', 'var def', 'var value'], tablefmt = 'grid'))
    
    def update_rounds(self, round_number):
        self.experiment_status.loc[self.experiment_status.index ==next_exp_index, 'completed_rounds'] = round_number

        self.experiment_status.to_csv(csv_path, index = False)
    
    def experiment_finished(self):
        self.experiment_status.loc[self.experiment_status.index ==next_exp_index, 'done'] = True
        self.experiment_status.to_csv(csv_path, index = False)
    
    def run(self):
        self.module.setup(self.current_setup_dictionary)
        self.module.run_script()
        
        round = 1
        while not module.fn.done:
            if self.module.fn.round != round:
                self.update_rounds(round)
            time.sleep(0.1)
        self.experiment_finished()
        
        
    #####-------------------undone--------------#####
    """def choose_unfinished(self):
        
        print(f'''script {self.vals['script']} for vole {self.vars['vole']} may have previously been run.
        only {self.cur_row['rounds_completed']} of
        {self.cur_row['rounds']} were completed. \n\n''')

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
            self.module.key_values['num_rounds'] = rounds_left
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

    def modify_varsxxx(self):
        '''give the user the opportunity to update the module values before running'''

        defs = [[i, val, self.module.key_values_def[val], self.module.key_values[val]] for i, val in enumerate(self.module.key_val_names_order)]
        defs += [[-1, 'done','','']]
        print(defs)
        print(tabulate(defs, headers = ['select','var name', 'var def', 'var value'], tablefmt = 'grid'))

        choice = int(input('which will you modify?\n'))


        while choice != -1:
            '''!!!implement a check on input here'''
            key = self.module.key_val_names_order[choice]

            val = int(input(f'new value for {key}?\n'))
            '''!!!implement a check on input here'''
            self.module.key_values[key] = val

            print('\n\n******************\n\n')

            defs = [[i, val, self.module.key_values_def[val],self.module.key_values[val]] for i, val in enumerate(self.module.key_val_names_order)]
            defs += [[-1, 'done','']]
            print(tabulate(defs, headers = ['select','var name', 'var def', 'var value'], tablefmt = 'grid'))

            choice = int(input('which will you modify?\n'))

    def update_vars(self):
        '''take a csv string <'key:val,key2:val2,....'> of vals and update the key values in the module'''
        
        #get our var_string
        var_string = self.experiment_status.iloc[self.next_exp_index].var_changes
        
        #check if empty
        if var_string == '' or var_string == None:
            return
        
        #make a dictionary of values if they exist
        vals = {v.split(':')[0]:v.split(':')[1] for v in var_string.split(',')}
        
        #go through the 
        for key in vals.keys():
            try:
                self.module.key_values[key] = vals[key]
            except:
                print(f'couldnt update {key} with value {vals[key]}\ndouble check the var name in the csv file')

    
    
    
        """