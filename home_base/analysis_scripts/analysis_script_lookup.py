import sys
import os
sys.path.append('/home/pi/')
import traceback
import importlib

def script_lookup(experiment):
    table = {'Door_test':door_test,
             'Door_test_anne':door_test,
             'Autoshape':autoshape,
             'Door_shape':door_shape,
             'Magazine':magazine,
             'progressive_ratio':progressive_ratio,
             'Autoshape_contingent':autoshape_contingent,
             'Door_shape_contingent':door_shape_contingent}

    return table[experiment]()

def magazine():
    try:
        print('importing magazine analysis module')
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

def autoshape_contingent():
    try:
        import RPI_operant.home_base.analysis_scripts.autoshape_contingent_analysis as autoshape
    except:
        traceback.print_exc()
        print('couldnt import Autoshape analysis script')
        raise
    return autoshape

def door_shape():
    try:
        print('importing door_shape analysis module')
        import RPI_operant.home_base.analysis_scripts.door_shape_analysis as door_shape
    except:
        traceback.print_exc()
        print('couldnt import door_shape analysis script')
        raise
    return door_shape

def door_shape_contingent():
    try:
        print('importing door_shape analysis module')
        import RPI_operant.home_base.analysis_scripts.door_shape_contingent_analysis as door_shape_contingent
    except:
        traceback.print_exc()
        print('couldnt import door_shape_contingent analysis script')
        raise
    return door_shape_contingent
    
def door_test():
    try:
        import RPI_operant.home_base.analysis_scripts.door_test_analysis as door_test
    except:
        traceback.print_exc()
        print('couldnt import door_test analysis script')
        raise
    return door_test

def progressive_ratio():
    try:
        import RPI_operant.home_base.analysis_scripts.progressive_ratio_analysis as progressive_ratio
    except:
        traceback.print_exc()
        print('couldnt import door_test analysis script')
        raise
    return progressive_ratio

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