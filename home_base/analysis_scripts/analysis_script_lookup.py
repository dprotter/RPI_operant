import sys
import os
sys.path.append('/home/pi/')
import traceback
import importlib

def script_lookup(experiment):
    table = {'Door_test':door_test(),
             'Autoshape':autoshape(),
             'Door_shape':door_shape(),
             'Magazine':magazine()}

    return table[experiment]

def magazine():
    try:
        import RPI_operant.home_base.analysis_scripts.magazine_analysis as magazine
    except:
        traceback.print_exc()
        print('couldnt import magazine analysis script')
        raise
    return magazine

def autoshape():
    try:
        import RPI_operant.home_base.analysis_scripts.autoshape_analysis as autoshape
    except:
        traceback.print_exc()
        print('couldnt import Autoshape analysis script')
        raise
    return autoshape

def door_shape():
    try:
        import RPI_operant.home_base.analysis_scripts.door_shape_analysis as door_shape
    except:
        traceback.print_exc()
        print('couldnt import Autoshape analysis script')
        raise
    return door_shape
    
def door_test():
    try:
        import RPI_operant.home_base.analysis_scripts.door_test_analysis as door_test
    except:
        traceback.print_exc()
        print('couldnt import door_test analysis script')
        raise
    return door_test

def load_custom_script(fpath):
    '''this will directly load a module from an fpath for using custom analysis scripts
    outside of the RPi_Operant package.'''
    #dynamically load a module from its filepath
    try:
        spec = importlib.util.spec_from_file_location(fpath)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
    except:
        traceback.print_exc()
        print(f'couldnt import custom script {fpath}')
    
        return None
    return module