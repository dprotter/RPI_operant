import sys
sys.path.append('/home/pi/')

import RPI_operant.home_base.analysis.analysis_functions as af
from RPI_operant.home_base.lookup_classes import Operant_event_strings as oes
import pandas as pd
import numpy as np


def run_analysis(data_raw, head, by_round_fname, summary_fname):
    data = data_raw
    
    #quick hack for some issues in specific datasets where some days used the string " food lever pressed" and some used " food lever pressed productive"
    if len(data.loc[data.Event == oes.food_leverpress_prod]) == len(data.loc[data.Event == oes.food_leverpress]):
        press_string = oes.food_leverpress_prod
    elif len(data.loc[data.Event == oes.food_leverpress_prod]) > len(data.loc[data.Event == oes.food_leverpress]): 
        press_string = oes.food_leverpress_prod
    else:
        press_string = oes.food_leverpress
    
    #calculations: food lever lat, pellet lat, percent press
    event_1 = oes.lever_out
    event_2 = press_string
    
    col_name = 'food_lever_press_latency'
    

    new_col, new_data = af.latency_by_round(data, event_1, event_2, 
                                             new_col_name = col_name, 
                                             selected_by = event_2)

    new_df_blank = np.asarray([[r, np.nan] for r in data.Round.unique()])
    
    new_df = pd.DataFrame(data = new_df_blank, columns = ['Round',new_col])
    new_df = new_df.astype({'Round':int})
    new_df = af.roundwise_join(new_df, new_data, new_col)

    # pellet lat
    event_1 = oes.disp
    event_2 = oes.retr
    col_name = 'pellet_latency'
    new_col, new_data = af.latency_by_round(data, event_1, event_2, new_col_name = col_name)
    round_df = af.roundwise_join(new_df, new_data, new_col)


    summary = []

    total_rounds = data.Round.max()
    summary += [['number of rounds in experiment', 'rounds', total_rounds]]

    '''calculate the values for the days summary'''
    #calculate number of presses
    total_presses = len(data.loc[data.Event == press_string])
    summary += [['total number of lever presses', 'total_lever_press', total_presses]]
    
    non_presses = total_rounds - total_presses
    summary += [['rounds without a press', 'non_press_rounds', non_presses]]
    
    prop_presses = total_presses/total_rounds
    summary += [['proportion of rounds with a lever press', 'prop_presses_by_rounds', non_presses]]
    
    prop_non_presses = non_presses/total_rounds
    summary += [['proportion of rounds without a lever press', 'prop_non_presses_by_rounds', prop_non_presses]]

    food_lever_press_prop_of_rounds = total_presses / total_rounds
    summary += [['proportion of rounds on which food lever was pressed', 
                'percent_food_presses', 
                food_lever_press_prop_of_rounds]]

    summary+= [['mean food lever press latency (excludes NaN)',
            'mean_food_lever_press_latency',
                round_df.food_lever_press_latency.mean()]]
    
    summary+= [['median food lever press latency (excludes NaN)',
            'median_food_lever_press_latency',
                round_df.food_lever_press_latency.median()]]

    summary+= [['mean pellet retrieval latency (excludes NaN)',
            'mean_pellet_latency',
                round_df.pellet_latency.mean()]]
    
    summary+= [['median pellet retrieval latency (excludes NaN)',
            'median_pellet_latency',
                round_df.pellet_latency.median()]]
    
    pel_retrievals = af.count_event(data, oes.retr)
    summary+= [['number of times a pellet was retrieved',
            'num_pellet_retrieved',
                pel_retrievals]]
    
    summary+= [['proportion of rounds when a pellet was retrieved',
            'proportion_round_pellet_retrieved',
                pel_retrievals / total_rounds]]
    
    dispensed = af.count_event(data, oes.disp)
    summary+= [['proportion of pellets retrieved',
            'proportion_pellet_retrieved',
                pel_retrievals / dispensed]]
    
    
    summary+= [['animal ID',
            'animal_ID',
                head['vole']]]

    summary+= [['experiment day entered by experimenter',
            'day',
                head['day']]]
    summary+= [['experiment script name',
            'experiment',
                head['experiment']]]
    summary+= [['time of run',
            'date',
                head['run_time']]]


    summary_df = pd.DataFrame(data = summary, columns = ['var_desc','var_name','var'])
    summary_df = summary_df.transpose()
    
    
    round_df.to_csv(by_round_fname)
    header_string = af.create_header_string(head)
    af.line_prepender(by_round_fname, header_string)
    
    summary_df.to_csv(summary_fname)
    af.line_prepender(summary_fname, header_string)


    
