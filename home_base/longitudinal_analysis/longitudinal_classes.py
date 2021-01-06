import pandas as pd
import numpy as np
import sys
import os
sys.path.append('/home/pi/RPI_operant/')
import home_base.analysis.analysis_functions as af
import home_base.analysis.analyze as ana
import traceback

#longitudinal functions
def read_summary_csv(filepath):
    head = af.get_header(filepath, skiplines = 0)
    df = pd.read_csv(filepath, header = 1)
    df.set_index('Unnamed: 0', inplace = True)
    return head, df.transpose()
    
    
def read_round_csv(filepath):
    head = af.get_header(filepath, skiplines = 0)
    df = pd.read_csv(filepath, header = 1)
    
    return head, df

class LongitudinalAnalysis:
    
    def __init__(self, experiment_name):
        self.experiment = experiment_name
        self.metrics = {}
        self.metrics_by_round = {}
        self._plottable_metrics = []
    
    def plottable_metrics(self):
            return self._plottable_metrics
        
    def set_plottable_metrics(self):
        for metric in self.metrics.keys():
            if metric in self._plottable_metrics:
                continue
                
            elif self.metrics[metric].plottable:
                self._plottable_metrics += [metric]
            
            else:
                continue

    def add_summary_csv(self, file):
        head, df = read_summary_csv(file)
        animal = df.loc[df.var_name == 'animal_ID', 'var'].values[0]
        experiment = df.loc[df.var_name == 'experiment', 'var'].values[0]
        day = df.loc[df.var_name == 'day', 'var'].values[0]
        
        for var_n in df.var_name.unique():
            value = df.loc[df.var_name == var_n, 'var'].values[0]
            new_row = {'animal':[animal], 'day':[day], 'value':[value],
                      'experiment':[experiment], 'file':[file]}
            if var_n in self.metrics.keys():
                metric = self.metrics[var_n]
                
                try:
                    metric.add_data(new_row)
                except:
                    pass
                    traceback.print_exc()
            else:
                value = df.loc[df.var_name == var_n, 'var'].values[0]
                name = var_n
                desc = df.loc[df.var_name == var_n, 'var_desc'].values[0]
                
                new_metric = Metric(name, desc)
                try:
                    new_metric.add_data(new_row)
                except:
                    pass
                    traceback.print_exc()
                
                self.metrics[var_n] = new_metric
            self.set_plottable_metrics()
        
        def add_by_round_csv(self, file):
            
            head, df = read_round_csv(file)
            animal = head['animal']
            experiment = head['experiment']
            day = head['day']
        
            for var_n in df.var_name.unique():
                value = df.loc[df.var_name == var_n, 'var'].values[0]

                if var_n in self.metrics.keys():
                    metric = self.metrics[var]
                    metric.add_data(animal, day, value, file)

                else:
                    value = df.loc[df.var_name == var_n, 'var'].values[0]
                    name = var_n
                    desc = df.loc[df.var_name == var_n, 'var_desc'].values[0]

                    new_metric = Metric(name, desc)
                    new_metric.add_data(animal, day, value)

                    self.metrics[var_n] = new_metric
        
        
        

class Metric:
    '''An object that is a single metric from the summary datasets. contains some basic
    information about the metric and some attributes that are useful for longitudinal experiments.'''
    
    def __init__(self, name, var_desc):
        self.name = name
        self.description = var_desc
        self.data = pd.DataFrame(columns=['animal', 'day','value','experiment', 'file'])
        self.data_type = str
        self.plottable = False
        self._do_not_plot = ['day', 'date']
        self._plottable_types = [int, float]
    
    def check_plottable(self):
        if self.name in self._do_not_plot:
            self.plottable = False
        
        elif self.data_type in self._plottable_types:
            self.plottable = True
            
        else:
            self.plottable = False
            print(f"{self.name} is {self.data_type} and plottable:{self.plottable}")
    
    '''def add_data(self, animal_num, day, value, experiment, file):'''
    def add_data(self, new_row):
        
        animal_num = new_row['animal'][0]
        day = new_row['day'][0]
        exp = new_row['experiment'][0]
        #check if this day is already occupied within this metric
        if len(self.data.loc[(self.data.animal == animal_num) & 
                             (self.data.day == day) &
                             (self.data.experiment == exp), 'value']) > 0:
            old_val = self.data.loc[(self.data.animal == animal_num) & (self.data.day == day), 'value'].values[0]
            old_file = self.data.loc[(self.data.animal == animal_num) & (self.data.day == day), 'file'].values[0]
            value = new_row['value']
            file = new_row['file']
            
            raise DuplicateData(self.name, animal_num, day,old_val , value, old_file, file, exp)
        
        ''' new_row = pd.DataFrame(data = {'animal':[animal_num],
                                       'day':[day],
                                       'value':[value],
                                       'file':[file],
                                       'experiment':[experiment]
                                       }, index=[len(self.data)+1])'''
        new_row = pd.DataFrame(data = new_row, index=[len(self.data)+1])
        
        dtype = self.intuit_dtype(new_row)
        if dtype != self.data_type:
            self.data_type = dtype
        self.check_plottable()
        
        self.data = self.data.append(new_row)
        
        self.data = self.data.astype({'day':float})
        self.data = self.data.astype({'value':self.data_type, 'day':int})
        
        self.data.sort_values(['animal','experiment','day'], inplace = True)
        
        
    
    def intuit_dtype(self, new_row):
        val = new_row.value.values[0]
        try:
            b = int(val)
        except Exception as e:
            
            try:
                a = float(val)
            except Exception as e:
                
                return str
            else:
                if np.isnan(a): 
                    return float
                
                elif int(a) == a:
                    return int
                
                else:
                    return float
        return int
        
        
    
class DuplicateData(Exception):
    """The day and animal that was passed to this Metric is already present."""
    def __init__(self, metric_name, animal, day, old_val, new_val, old_file, new_file):
        self.metric_name = metric_name
        self.old_file = old_file
        self.new_file = new_file
        self.ani = animal
        self.day = day
        self.old_val = old_val
        self.new_val = new_val
        self.message = ''
        super().__init__(self.message)

    def __str__(self):
        return f'metric: {self.metric_name}\nday: {self.day}\nanimal: {self.ani}\nold value: {self.old_val}\nnew value passed: {self.new_val}\nold_file:{self.old_file}\nnew_file:{self.new_file}'

class Metric_by_round:
    '''An object that '''
    def __init__(self, name, var_desc):
        self.name = name
        self.description = var_desc
        self.data = pd.DataFrame(columns=['animal', 'day','round','value','file'])
    
    def add_data(self, animal_num, day, rnd, value, file):
        anis = self.data.animal.unique()
        days = self.data.day.unique()
        
        if animal_num in anis and day in days:
            raise DuplicateData
        
        new_row = pd.DataFrame(data = {'animal':[animal_num],
                                       'day':[day],
                                       'round':[rnd],
                                       'value':[value],
                                       'file':[file]})
        self.data = self.data.append(new_row)
        self.data.sort_values(['animal','day'], inplace = True)