import sys
sys.path.append('/home/pi/')

import RPI_operant.home_base.functions as FN
fn = FN.runtime_functions()

import threading
import time
import numpy as np



default_setup_dict = {'vole':'000','day':1, 'experiment':'Door_test',
                    'user':'Test User', 'output_directory':'/home/pi/test_outputs/', 'partner':'door_1', 'novel_num':'000'}

setup_dictionary = None

key_values = {'num_rounds': 30,
              'round_time':90, 
              'time_II':30,
              'move_time':20,
              'pellet_tone_time':1, 
              'pellet_tone_hz':2500,
              'door_close_tone_time':1, 
              'door_close_tone_hz':7000,
              'door_open_tone_time':1,
              'door_open_tone_hz':10000,
              'round_start_tone_time':1, 
              'round_start_tone_hz':5000,
              'delay by day':[],
              'delay default':1}

key_values_def = {'num_rounds':'number of rounds',
                  'round_time':'total round length',
                  'time_II':'time after levers out before reward',
                  'move_time':'seconds to move the vole back to the lever room',
                  'pellet_tone_time':'in s', 
                  'pellet_tone_hz':'in hz',
                  'door_close_tone_time':'in s', 
                  'door_close_tone_hz':'in hz',
                  'door_open_tone_time':'in s',
                  'door_open_tone_hz':'in hz',
                  'round_start_tone_time':'in s', 
                  'round_start_tone_hz':'in hz',
                  'delay by day':'delay between lever press and reward',
                  'delay default':'delay between lever press and reward if beyond delay by day length'}

#for display purposes. put values you think are most likely to be changed early
key_val_names_order = ['num_rounds', 'time_II', 'move_time','pellet_tone_time',
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
    
    day_num = int(setup_dictionary['day'])
    if day_num > len(key_values['delay by day']):
        delay = key_values['delay default']
    else:
        delay = key_values['delay by day'][day_num-1]
    
    #spin up a dedicated writer thread
    wrt = threading.Thread(target = fn.flush_to_CSV, daemon = True)
    wrt.start()

    or1 = threading.Thread(target = fn.override_door_1, daemon = True)
    or2 = threading.Thread(target = fn.override_door_2, daemon = True)
    or1.start()
    or2.start()

    #double check the doors are closed. close, if they arent
    fn.reset_doors()
    
    ##### start timing this session ######
    fn.start_timing()
    fn.pulse_sync_line(0.1)
    
    for x in range(5):

        #spin up threads for the thread distributor
        t = threading.Thread(target = fn.thread_distributor)

        #when main thread finishes, kill these threads
        t.daemon = True
        t.start()
        
        
    key_values['num_rounds'] = int(key_values['num_rounds'])
    ### master looper ###
    print(f"range for looping: {[i for i in range(1, key_values['num_rounds']+1,1)]}")
    

    #start at round 1 instead of the pythonic default of 0 for readability
    for i in range(1, key_values['num_rounds']+1,1):
        

        round_start = time.time()
        
        fn.round = i
        fn.pulse_sync_line(0.1)
        print(f"\n\n\n#-#-#-#-#-# new round #{i}!!!-#-#-#-#-#\n\n\n")
        
        #round start buzz
        fn.timestamp_queue.put(f'{fn.round}, Starting new round, {time.time()-fn.start_time}') 
        fn.do_stuff_queue.put(('buzz',round_buzz))
        fn.do_stuff_queue.join()
        
        fn.do_stuff_queue.put(('extend lever',
                            ('door_1')))
        
        fn.do_stuff_queue.put(('monitor lever',
                           ('door_1')))
        
        fn.do_stuff_queue.put(('extend lever',
                            ('door_2')))
        
        fn.do_stuff_queue.put(('monitor lever',
                           ('door_2')))

        time_II_start = time.time()
        
        #reset our info about whether the animal has pressed
        press = False
        while time.time() - time_II_start < key_values['time_II']:
            if not fn.lever_press_queue.empty() and not press:

                #get which door was pressed    
                lever_press = fn.lever_press_queue.get()

                fn.pulse_sync_line(0.025)
                
                #retract lever
                fn.monitor = False
                fn.do_stuff_queue.put(('retract lever',
                                    ('door_1')))
                fn.do_stuff_queue.put(('retract lever',
                                    ('door_2')))
                
                #do not give reward until after delay
                time.sleep(delay)
                fn.do_stuff_queue.put(('buzz', door_open_buzz))
                fn.do_stuff_queue.join()

                #open the door of the lever that was pressed 
                fn.do_stuff_queue.put(('open door', 
                                       (lever_press)))
                
                press = True
                
            time.sleep(0.05)
            
        #if the vole didnt press:
        if press == False:
            print('no lever press')
            fn.monitor = False
            
            fn.do_stuff_queue.put(('retract lever',
                                    ('door_1')))
            fn.do_stuff_queue.put(('retract lever',
                                ('door_2')))
            
        while time.time() - round_start < key_values['round_time']:
            sys.stdout.write(f"\r{np.round(key_values['round_time'] - (time.time()-round_start))} seconds left before moving")
            time.sleep(1)
            sys.stdout.flush()
            time.sleep(1)
        
        #if the door was opened, close it
        if press:
            fn.do_stuff_queue.put(('buzz',door_close_buzz))
            fn.do_stuff_queue.join()
            time.sleep(0.5)
            fn.do_stuff_queue.put(('close door', 
                                  (lever_press)))
        
        
        
        print('\n\ntime to move that vole over!')
        fn.timestamp_queue.put(f'{fn.round}, start of move animal time, {time.time()-fn.start_time}')
        
        move_ani_start = time.time()
        while time.time() - move_ani_start < key_values['move_time']:
            sys.stdout.write(f"\r{np.round(key_values['move_time'] - (time.time()-move_ani_start))} seconds left before next round")
            time.sleep(1)
            sys.stdout.flush()
        print('\nvole should be moved now')
    
    
    fn.do_stuff_queue.put(('clean up',))
    fn.do_stuff_queue.join()
    
    
if __name__ == '__main__':
    print('running directly, please enter relevant info.\n')
    
    test_run = input('is this just a quick test run? if so, we will just do 1 round. (y/n)\n')
    if test_run.lower() in ['y', 'yes']:
        print('ok, test it is!')
        key_values['num_rounds'] = 3
        key_values['round_time'] = 10
        key_values['time_II'] = 5
        key_values['move_time'] = 4
        exp = default_setup_dict['experiment']
        day = input(f'Which {exp} training day is this? (for training)\n')
        day = int(day)
        default_setup_dict['day'] = day
        
    
    else:
        no_user = True
        while no_user:
            user = input('who is doing this experiment? \n')
            check = input('so send the data to %s ? (y/n) \n'%user)
            if check.lower() in ['y', 'yes']:
                no_user = False

        
        no_vole = True
        while no_vole:
            vole = input('Vole number? \n')
            check = input('vole# is %s ? (y/n) \n'%vole)
            if check.lower() in ['y', 'yes']:
                no_vole = False


        day = input('Which magazine training day is this? (starts at day 1)\n')
        day = int(day)
        
        
        default_setup_dict['vole'] = vole
        default_setup_dict['user'] = user
        default_setup_dict['output_directory'] = '/home/pi/Operant_Output/script_runs/'

    setup(setup_dict=default_setup_dict)
    
    run_script()
