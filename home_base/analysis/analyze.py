import pandas as pd
import traceback

def script_lookup(experiment):
    table = {'Door_shape':door_test}

    return table[experiment]

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

def run_analysis_script(filepath, custom_script = None):
    '''fpath of csv output from operant experiment. Can direct to a custom analysis script by passing its full path.'''
    header = get_header(filepath)
    print(header)
    if not custom_script:
        exp = header['experiment']
        try:
            script_lookup(exp)(filepath)
        except:
            traceback.print_exc()
            print('whoops couldnt run that analysis')
    else:
        exp = custom_script

def prep_for_analysis(filepath):
    fname_summary = append_name_general(filepath, 'summary')
    fname_by_round = append_name_general(filepath, 'analysis_by_round')
    df = pd.read_csv(filepath, skiprows = 2)
    df.dropna(axis = 1, inplace = True)
    return fname_summary, fname_by_round, df


def door_test(fname):
    fsum, fround, data = prep_for_analysis(fname)
    ''''''


