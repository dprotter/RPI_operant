import sys
sys.path.append('/home/pi/')

from RPI_operant.home_base.analysis.analysis_functions import assemble_names
import RPI_operant.home_base.analysis.analyze as ana
import argparse

parser = argparse.ArgumentParser(description='input directory')
parser.add_argument('--dir_in', '-d',type = str, 
                    help = 'directory of files to analyze',
                    action = 'store')
parser.add_argument('--file_in','-f', type = str, 
                    help = 'single file to analyze',
                    action = 'store')

args = vars(parser.parse_args())

def re_analyze_directory(directory):
    files = assemble_names(directory)
    file_list = [f for f in files if not 'summary' in f if not 'round' in f]
    for f in file_list:
        re_analyze_file(f)


def re_analyze_file(file):
    ana.run_analysis_script(file)


if __name__ == '__main__':
    if 'dir_in' in args.keys():
        re_analyze_directory(args['dir_in'])
    elif 'file_in' in args.keys():
        re_analyze_file(args['file_in'])
    else:
        print('no file or directory provdied (use flag -f or -d to point script to file or directory)')
