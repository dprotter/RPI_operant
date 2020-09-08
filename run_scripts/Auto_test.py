import sys
sys.path.append('/home/pi/RPI_operant/')

import home_base.functions as FN
fn = FN.runtime_functions()


import threading
import time



start_time = 0
save_path = ''

comms_queue = None

setup_dictionary = None

default_setup_dict = {'vole':'000','day':1, 'experiment':'Test_two_doors',
                    'user':'Test User', 'output_directory':'/home/pi/test_outputs/'}


key_values = {'num_rounds': 1, 'round_time':8, 'timeII':2,
            'timeIV':2, 'pellet_tone_time':0.5, 'pellet_tone_hz':3000,
            'door_close_tone_time':0.25, 'door_close_tone_hz':6000,
            'door_open_tone_time':0.25,'door_open_tone_hz':10000,
            'round_start_tone_time':0.25, 'round_start_tone_hz':6000}

key_values_def = {'num_rounds':'number of rounds', 'round_time':'total round length',
            'timeII':'time after levers out before pellet',
            'timeIV':'''time after pellet delivered before levers retracted''',
            'pellet_tone_time':'in s', 'pellet_tone_hz':'in hz',
            'door_close_tone_time':'in s', 'door_close_tone_hz':'in hz',
            'door_open_tone_time':'in s','door_open_tone_hz':'in hz',
            'round_start_tone_time':'in s', 'round_start_tone_hz':'in hz'}

key_val_names_order = ['num_rounds', 'round_time', 'timeII', 'timeIV','pellet_tone_time',
                        'pellet_tone_hz','door_close_tone_time','door_close_tone_hz',
                        'door_open_tone_time','door_open_tone_hz', 'round_start_tone_time',
                        'round_start_tone_hz']

def setup(setup_dict = None):
    global setup_dictionary
    global key_val_names_order
    
    #run this to get the RPi.GPIO pins setup
    if setup_dict == None:
        #set the module setup dictionary to default values so we can access vals, 
        #like 'day' if necessary
        print('no dict given for setup')
        setup_dictionary = default_setup_dict
    else:
        print(f'dict given for setup ----- {setup_dict}')
        setup_dictionary = setup_dict
    print(setup_dictionary)
    
    
    #resolve issues if people add values to the key value dictionary and dont define them or put them in the name order list
    missing_def = [val for val in key_values if not val in key_values_def]
    if len(missing_def) > 0:
        print(f'no definition given for: {missing_def}')
    for val in missing_def:
        key_values_def[val] = 'unknown'

    missing_order = [val for val in key_values_def if not val in key_val_names_order]

    for val in missing_order:
        key_val_names_order += [val]
    
    fn.setup_pins()
    
    fn.setup_experiment(setup_dictionary)


def run_script():

    #buzz args passed as (time, hz, name), just to make
    #code a little cleaner
    round_buzz = (key_values['round_start_tone_time'],
                    key_values['round_start_tone_hz'],
                    'round_start_tone')

    pellet_buzz = (key_values['pellet_tone_time'],
                    key_values['pellet_tone_hz'],
                    'pellet_tone')

    door_open_buzz = (key_values['door_open_tone_time'],
                    key_values['door_open_tone_hz'],
                    'door_open_tone')

    door_close_buzz = (key_values['door_close_tone_time'],
                    key_values['door_close_tone_hz'],
                    'door_close_tone')

    #spin up a dedicated writer thread
    wrt = threading.Thread(target = fn.flush_to_CSV, daemon = True)
    wrt.start()

    or1 = threading.Thread(target = fn.override_door_1, daemon = True)
    or2 = threading.Thread(target = fn.override_door_2, daemon = True)
    or1.start()
    or2.start()

    #double check the doors are closed. close, if they arent
    print('resetting door states')
    fn.reset_doors()
    open_doors = [id for id in ['door_1', 'door_2'] if not fn.door_states[id]]
    if len(open_doors) > 0 :
        print(f'oh dip! theres a problem closing the doors: {open_doors}')
        raise

    #start the internal timer of the module
    fn.start_timing()

    for x in range(5):

        #spin up threads for the thread distributor
        t = threading.Thread(target = fn.thread_distributor)

        #when main thread finishes, kill these threads
        t.daemon = True
        t.start()
    ### master looper ###

    for i in range(1, key_values['num_rounds']+1,1):
        round_start = time.time()
        fn.round = i
        print("#-#-#-#-#-# new round #%i!!!-#-#-#-#-#"%i)
        fn.timestamp_queue.put(f'{fn.round}, Starting new round, {time.time()-fn.start_time}')
        fn.do_stuff_queue.put(('buzz',round_buzz))
        fn.do_stuff_queue.join()
        time.sleep(1)
        print('ok lets try and open door 1')

        fn.do_stuff_queue.put(('buzz',door_open_buzz))
        fn.do_stuff_queue.join()
        time.sleep(0.5)

        fn.do_stuff_queue.put(('open door',('door_1')))
        fn.do_stuff_queue.join()

        time.sleep(3)

        fn.do_stuff_queue.put(('buzz',door_close_buzz))
        fn.do_stuff_queue.put(('close door',('door_1')))
        fn.do_stuff_queue.join()

        time.sleep(2)
        
        print('ok lets try and open door 2')

        fn.do_stuff_queue.put(('buzz',door_open_buzz))
        fn.do_stuff_queue.join()
        time.sleep(0.5)

        fn.do_stuff_queue.put(('open door',('door_2')))
        fn.do_stuff_queue.join()
        
        time.sleep(3)

        fn.do_stuff_queue.put(('buzz',door_close_buzz))
        fn.do_stuff_queue.put(('close door',('door_2')))

        time.sleep(2)

        print('lets extend the food lever')
        print(f'unfinished1: {fn.do_stuff_queue.unfinished_tasks}')
        fn.do_stuff_queue.put(('extend lever',
                            ('food')))
        
        print(f'unfinished2: {fn.do_stuff_queue.unfinished_tasks}')

        fn.do_stuff_queue.put(('monitor_lever_test',
                            ('food')))
        
        time.sleep(2)
        
        fn.monitor = False
        print(f'unfinished3: {fn.do_stuff_queue.unfinished_tasks}')

        fn.do_stuff_queue.put(('retract lever',
                            ('food')))

        time.sleep(2)
        print(f'unfinished4: {fn.do_stuff_queue.unfinished_tasks}')
        
        print('lets extend door 1 lever')
        
        fn.do_stuff_queue.put(('extend lever',
                            ('door_1')))

        fn.do_stuff_queue.put(('monitor_lever_test',
                            ('door_1')))
       
        time.sleep(2)
        
        fn.monitor = False

        fn.do_stuff_queue.put(('retract lever',
                            ('door_1')))

        time.sleep(2)

        
        print('lets extend door 2 lever')
        
        fn.do_stuff_queue.put(('extend lever',
                            ('door_2')))

        
        
        fn.do_stuff_queue.put(('monitor_lever_test',
                            ('door_2')))
        
        
        time.sleep(2)
        
        fn.monitor = False
        
        
        
        fn.do_stuff_queue.put(('retract lever',
                            ('door_2')))
        time.sleep(1)
        print(f'unfinished3: {fn.do_stuff_queue.unfinished_tasks}')
        
       
        fn.do_stuff_queue.join()

if __name__ == '__main__':
    '''is_test = input('is this just a test? y/n\n')'''
    is_test = 'y'
    if is_test.lower() == 'y':
        setup_dict = default_setup
    setup(setup_dict)
    run_script()
