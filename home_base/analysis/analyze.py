import pandas as pd
import traceback
import sys
import os
sys.path.append('/home/pi/RPI_operant/')
import home_base.analysis_scripts.analysis_script_lookup as asl




def run_analysis_script(filepath, custom_script = None, output_loc = None):
    '''fpath of csv output from operant experiment. Can direct to a custom 
    analysis script by passing its full path.'''
    header = get_header(filepath)
    
    #
    fname_sum, fname_by_round, df = prep_for_analysis(filepath, 
                                                      output_override_loc = output_loc)
    if not custom_script:
        exp = header['experiment']
        print(f'exp is {exp}')
        try:
            analysis_module = asl.script_lookup(exp)
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
            filepath_out = os.path.join(output_override_loc, 
                                    filepath.split('/')[-1])
        else:
            print(f'{output_override_loc} does not exist, falling back to file location directory:')
            print(filepath)
            
    fname_summary = append_name_general(filepath_out, 'summary')
    fname_by_round = append_name_general(filepath_out, 'analysis_by_round')
        
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
    
