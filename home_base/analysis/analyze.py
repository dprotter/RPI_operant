import pandas as pd
import traceback
import sys
import os
sys.path.append('/home/pi/RPI_operant/')
import home_base.analysis_scripts.analysis_script_lookup as asl


def script_lookup(experiment):
    table = {'Door_test':asl.door_test()}

    return table[experiment]

def run_analysis_script(filepath, custom_script = None, output_loc = None):
    '''fpath of csv output from operant experiment. Can direct to a custom 
    analysis script by passing its full path.'''
    header = get_header(filepath)
    
    #
    fname_sum, fname_by_round, df = prep_for_analysis(filepath, 
                                                      output_override_loc = output_loc)
    if not custom_script:
        exp = header['experiment']
        try:
            analysis_module = script_lookup[exp]
        except:
            traceback.print_exc()
            print(f'couldnt lookup {exp}')
            
    else:
        analysis_module = asl.load_custom_script(custom_script)

    analysis_module.run_analysis(data_raw = df,
                                       head = header,
                                       by_round_fname = fname_by_round,
                                       summary_fname = fname_sum)

def prep_for_analysis(filepath, output_override_loc = None):
    if output_override_loc:
        if os.path.isdir(output_override_loc):
            filepath = os.path.join(output_override_loc, 
                                    filepath.split('/')[-1])
        else:
            print(f'{output_override_loc} does not exist, falling back to file location directory:')
            print(filepath)
            
    fname_summary = append_name_general(filepath, 'summary')
    fname_by_round = append_name_general(filepath, 'analysis_by_round')
        
    df = pd.read_csv(filepath, skiprows = 2)
    df.dropna(axis = 1, inplace = True)
    return fname_summary, fname_by_round, df
       


def append_name_general(input_name, append_str, sep = '_'):
        vals = input_name.split('.')
        return vals[0] + sep + append_str + '.' + vals[1]

def get_header(fname):
    """header looks like:
    
    vole:3558.0|day:4.0|experiment:Door_shape|user:protter|output_directory:/home/pi/Documents/operant_experiment|partner:door_1|novel_num:000|completed_rounds:nan|done:False|expected_date:10_2_20|experiment_status:nan|num_rounds:20.0|rounds_completed:nan|run_time:nan|script:Door_shape|
    """
    with open(fname) as f:
        #skip first line
        f.readline()
        header_vals = f.readline().split('|')
        header_dict = {}
        for val in header_vals:
            unpacked = val.split(':')
            if len(unpacked) == 2:
                header_dict[unpacked[0]] = unpacked[1]
            if len(unpacked) > 2:
                print(f'hmm, theres something weird going on in the header. Heres the value:{val}')
                
    return header_dict
    
def latency_by_round(df, event_1, event_2,  
                    new_col_name = None, 
                    include_missing_data_as_nan = False, 
                    selected_by = None,
                    get_rounds_from = 'first'
                ):
    '''get the latency from event_1 to event_2. event_1 should be whatever occurred first. If 
    there is a length mismatch of 1 this will assume the latency of the last index of event_1
    is missing. For example, a pellet was not retrieved before the end of the experiment. This
    event will be trimmed unless include_missing_data_as_nan is set to True. 
    
    This function assumes each round can have at most 1 latency to calculate.
    
    round number indicates round in which event_1 happened
    
    include_missing_data_as_nan = True --> final value of returned array will be np.nan selected_by 
                                           should be a list of events to select your desired rounds by. 
                                           For example, if we want to choose lever press latency we 
                                           should only select rounds on which a lever was pressed, 
                                           and will pass that as [<lever_press_event_string>]. 
    
    in contrast, if we want to get the pellet retrieval we should ignore this, as retrievals
    can happen on different rounds than when the pellet was dispensed. (Pellet dispensed on round 2,
    retrieved on round 5, for example)
    
    get_rounds_from : str, 'first' or 'second'. Which event to get the round numbers from. For example,
                      if a pellet is dispensed in round 1 and retrieved in round 4, we can use 'first'
                      to assign the round in the output to 1, or use 'second' to assign the round in
                      the output to 4.
                      
    selected_by : event_string. If you want to limit the rounds analyzed to rounds on which an event occurred. For example, 
                  if we want to limit lever_press analysis to only rounds on which a lever was pressed, ignoring
                  rounds on which a lever wasnt pressed, we can use "selected_by = <door_2 leverpress string>"  

    '''
    
    if get_rounds_from not in ('first', 'second'):
        raise TypeError('get_rounds_from tells this function which event to use when noting the round corresponding to latency. Must be "first" or "second"')
    
    if not new_col_name:
        new_col = f'latency_from_|{event_1}|_to_|{event_2}|'
    else:
        new_col = new_col_name
    
    '''new_df_blank = np.asarray([[r, np.nan] for r in df.Round.unique()])
    new_df = pd.DataFrame(data = new_df_blank, columns = ['Round',new_col_name])'''
    
    if selected_by:
        rounds = df.loc[df.Event == selected_by, 'Round'].unique()
        sli_1 = df.loc[(df.Event == event_1)&(df.Round.isin(rounds))].copy()
        sli_2 = df.loc[(df.Event == event_2)&(df.Round.isin(rounds))].copy()
    else:
        sli_1 = df.loc[(df.Event == event_1)]
        sli_2 = df.loc[(df.Event == event_2)]
    
        
    if len(sli_1) == len(sli_2):
        if get_rounds_from == 'first':
            sli_1[new_col] = sli_2.Time.values - sli_1.Time.values
            return sli_1
        else:
            sli_2[new_col] = sli_2.Time.values - sli_1.Time.values
            return sli_2
        
    elif len(sli_1) == len(sli_2) + 1:
        if get_rounds_from == 'first':
            sli_1[new_col] = np.nan
            lat = sli_2.Time.values - sli_1.Time.values[:-1]
            sli_1.iloc[:-1, new_col] = lat
            return sli_1
        else:
            sli_2[new_col] = np.nan
            lat = sli_2.Time.values - sli_1.Time.values[:-1]
            sli_2.iloc[:-1, new_col] = lat
            return sli_2
    else:
        raise IndexError('these two events have an unequal number of recordings (diff > 1).')
    
    
def count_event(df, event):
    return len(df.loc[df.Event == event])
    
def roundwise_join(df1, df2, new_col_name):
    new_df = df1.copy()
    new_df[new_col_name] = np.nan
    if len(df2.Round.unique()) != len(df2):
        raise IndexError('impossible to match on Round, as there are duplicate rounds.')
    for index, row in df2.iterrows():
        r = int(row.Round)
        val = row[new_col_name]
        new_df.loc[new_df.Round == r, new_col_name] = val
    
    return new_df

