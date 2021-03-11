
import pandas as pd
import numpy as np
import importlib
import queue
from tabulate import tabulate
import os
import time as time
import traceback
import threading
import datetime

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
        self.exp_index = self.cur_row.index.values[0]
        
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
        self.modify_setup_dict_from_csv()
        self.modify_module_key_values()
      
    def next_experiment(self):
        
        self.unfinished_loc += 1
        if self.unfinished_loc not in list(self.unfinished.index.values):
            print('wow, think we are out of experiments to run! you must be all done.')
            return False
        self.cur_row = self.unfinished.iloc[[self.unfinished_loc]]
        
        #here we get the index value in the dataframe of our next experiment, 
        #starting with the first experiment listed as unfinished. 
        self.exp_index = self.cur_row.index.values[0]
        
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
        self.current_setup_dictionary['output_directory'] = self.output_location
        
        #overwrite the default setup dict with values from the csv file
        self.instantiate_experiment()
        #change any values in the modules variable dictionary as necessary from the csv column
        #var_change
        self.modify_setup_dict_from_csv()
        self.modify_module_key_values()
        return True
    
    def modify_setup_dict_from_csv(self):
        '''read and update vars from var_change column of csv'''
        mods = self.vals['var_changes']
    
        print(f'vals are {self.vals}')

        for mod in mods.keys():
            try:
                self.current_setup_dictionary[mod] = mods[mod]
            except:
                print(f'couldnt update var changes {mod}:{mods[mod]}')
                
    def modify_module_key_values(self):
        '''must be numbers!!!! will convert to float'''
        vals_to_mod = [key for key in self.current_setup_dictionary.keys() 
                       if key in self.module.key_values.keys()]
        
        
        for key in vals_to_mod:
            
            self.module.key_values[key] = float(self.current_setup_dictionary[key])
    
    def user_modify_module_key_values(self):
        ''' manually update variables. these will get put in the var_change column, as well'''
        track_changes = {}
        defs = self.print_vals()
        mod_index = int(input('\n\n\nmodify which value?\n'))
        
        acceptable_values = [i for i in range(len(defs)-1)] + [-1]
        
        while mod_index != -1:
            if not mod_index in acceptable_values:
                print(f'whoops, that was input ( {mod_index} ) was not acceptedy. try again!')
                continue
            else:
                key = defs[mod_index][1]
                val = input(f'\nwhat do you want to set {key} to?\n')
                
                if type(self.module.key_values[key]) == int:
                    self.module.key_values[key] = int(val)
                    track_changes[key] = val
                elif type(self.module.key_values[key]) == float:
                    self.module.key_values[key] = float(val)
                    track_changes[key] = val
                elif type(self.module.key_values[key]) == str:
                    self.module.key_values[key] = str(val)
                    track_changes[key] = val
                else:
                    print('cant identify the datatype for this key value. cant properly change it.')
            defs = self.print_vals()
            mod_index = int(input('\n\n\nmodify which value?\n'))
        print('adding changed variabls to "var_canges" in csv files')
        
        #####need to read in current variable changes and overwrite with manual changes here
        current_vals = self.cur_row['var_changes'].values[0]
        cur_dict = {kv.split(':')[0]:kv.split(':')[1] for kv in current_vals.split(',')}
        for key in track_changes.keys():
            cur_dict[key] = track_changes[key]
        
        new_str = ''
        for key in cur_dict.keys():
            new_str += f'{key}:{cur_dict[key]},'
        #remove trailing comma
        new_str = new_str[:-1]
        
        #update experiment csv
        self.experiment_status.loc[self.experiment_status.index ==self.exp_index, 'var_changes'] = new_str
        self.experiment_status.to_csv(self.file, index = False)
        
        #update current row, since we've made changes
        self.cur_row = self.unfinished.iloc[[self.unfinished_loc]]
    
    def user_modify_setup_dict(self):
            ''' manually update setup dictionary. '''
        
            defs = self.print_setup_dict()
            
            
            mod_index = int(input('\n\n\nmodify which value?\n'))
            
            acceptable_values = [i for i in range(len(defs)-1)] + [-1]
            track_changes = {}
            
            while mod_index != -1:
                if not mod_index in acceptable_values:
                    print(f'whoops, that was input ( {mod_index} ) was not acceptedy. try again!')
                    continue
                else:
                    key = defs[mod_index][1]
                    val = input(f'\nwhat do you want to set {key} to?\n')
                    
                    key_type = type(self.current_setup_dictionary[key])
                    
                    if key_type == int or key_type == np.int64:
                        self.current_setup_dictionary[key] = int(val)
                        track_changes[key] = val
                    elif key_type == float or key_type == np.float64:
                        self.current_setup_dictionary[key] = float(val)
                        track_changes[key] = val
                    elif key_type == str:
                        self.current_setup_dictionary[key] = str(val)
                        track_changes[key] = val
                    else:
                        print(f'cant identify the datatype for <{key}> key. getting {type(self.current_setup_dictionary[key])} cant properly change it.')
                defs = self.print_setup_dict()
                mod_index = int(input('\n\n\nmodify which value?\n'))
            print('adding changed variabls to csv files')
            for key in track_changes.keys():
                if key in self.experiment_status.columns:
                    self.experiment_status.loc[self.experiment_status.index ==self.exp_index, key] = track_changes[key]
                self.experiment_status.to_csv(self.file, index = False)
    
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
        update = {}
        self.convert_var_changes()
        for key in self.vals.keys():
            if key != 'var_changes':
                update[key] = self.vals[key]
            
            for key in self.vals['var_changes'].keys():
                update[key] = self.vals['var_changes'][key]
        self.current_setup_dictionary.update(update)
    
    def convert_var_changes(self):
        '''check if self.vals['var_changes'] is a dict. if not, make it one'''
        current_vals = self.vals['var_changes']
        converted = {}
        if not isinstance(current_vals, dict):
            if is instance(current_vals, str):
                'if we have a string of key:value pairs, split on "," and iterate over them.'
                for pair in current_vals.split(','):
                    key, value = pair.split(':')
                    self


        if not type(current_vals) == dict:
            if not type(current_vals) == np.float64:
                self.vals['var_changes'] = {kv.split(':')[0]:kv.split(':')[1] for kv in current_vals.split(',')}
            else:
                self.vals['var_changes'] = {}
            
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
        
        self.print_vals()
        print(self.current_setup_dictionary)
        print('\n\n\n\nshould we run this experiment?\ny (yes)\nn (no)\nm (modify key value)\nd (modify setup dictionary)')
        
        resp = input('').lower()
        
        if resp == 'y':
            return True
        elif resp == 'n': 
            return False
        elif resp == 'm':
            self.user_modify_module_key_values()
            return self.ask_to_run()
        elif resp == 'd':
            self.user_modify_setup_dict()
            return self.ask_to_run()
        else:
            print('\n\n\nhmmm, not a valid response, (y/n). try again.')
            return self.ask_to_run()
        
    
    def print_vals(self):
        
        defs = [[i, val, self.module.key_values_def[val], self.module.key_values[val]] for i, val in enumerate(self.module.key_val_names_order)]
        defs += [[-1, 'done','','']]
        print(tabulate(defs, headers = ['select','var name', 'var def', 'var value'], tablefmt = 'grid'))
        print(f'\n\nrunning script {self.current_setup_dictionary["script"]}\n\nvole: {self.current_setup_dictionary["vole"]}\n\nday:{self.current_setup_dictionary["day"]}\n\n')
        return defs
    
    def print_setup_dict(self):
        defs = [[i, key, self.current_setup_dictionary[key]] for i, key in enumerate(self.current_setup_dictionary.keys())]
        defs += [[-1, 'done','','']]
        print(tabulate(defs, headers = ['select','key', 'value'], tablefmt = 'grid'))
        return defs
    
    def update_rounds(self, round_number):
        print(f'\n\n\n\n-------updating csv log, new round completed {round_number}----------\n\n\n')
        self.experiment_status.loc[self.experiment_status.index ==self.exp_index, 'rounds_completed'] = round_number
        self.experiment_status.to_csv(self.file, index = False)
    
    
    def track_script_progress(self):
        
        current_round = 0
        while not self.module.fn.done:
            if self.module.fn.round != current_round:
                self.update_rounds(current_round)
                current_round = self.module.fn.round
            time.sleep(0.1)
        self.update_rounds(self.module.fn.round)
        self.experiment_finished()
    
    def experiment_finished(self):
        
        self.experiment_status.loc[self.experiment_status.index == self.exp_index, 'done'] = True
        self.experiment_status.to_csv(self.file, index = False)
    
    
    def run(self):
        self.module.setup(self.current_setup_dictionary)
        csv_up = threading.Thread(target = self.track_script_progress, daemon = True)
        csv_up.start()
        
        
        date = datetime.datetime.now()
        fdate = '%s_%s_%s__%s_%s'%(date.month, date.day, date.year, date.hour, date.minute)
        self.experiment_status.loc[self.experiment_status.index ==self.exp_index, 'run_time'] = fdate
        self.experiment_status.to_csv(self.file, index = False)
        self.module.run_script()
        self.experiment_finished()
        