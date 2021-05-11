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


def setup(setup_dictionary = default_setup_dict, 
                            key_val_names_order = key_val_names_order,
                             key_values = key_values,
                             key_values_def = key_values_def):
    
    
    key_values_def, key_val_names_order = fn.check_key_value_dictionaries(key_values, 
                                                                          key_values_def,
                                                                          key_val_names_order)
    
    fn.setup_pins()
    fn.setup_experiment(setup_dictionary)
    return setup_dictionary
    


def run_script(setup_dictionary = None):
    key_values['num_rounds'] = int(key_values['num_rounds'])
    #buzz args passed as (time, hz, name), just to make
    #code a little cleaner
    round_buzz = {'buzz_length':key_values['round_start_tone_time'],
                    'hz':key_values['round_start_tone_hz'],
                    'name':'round_start_tone'}

    pellet_buzz = {'buzz_length':key_values['pellet_tone_time'],
                    'hz':key_values['pellet_tone_hz'],
                    'name':'pellet_tone'}

    door_open_buzz = {'buzz_length':key_values['door_open_tone_time'],
                    'hz':key_values['door_open_tone_hz'],
                    'name':'door_open_tone'}

    door_close_buzz = {'buzz_length':key_values['door_close_tone_time'],
                    'hz':key_values['door_close_tone_hz'],
                    'name':'door_close_tone'}
    


    #double check the doors are closed. close, if they arent
    fn.reset_chamber()
    
    ##### start timing this session ######
    fn.start_timing()
    fn.pulse_sync_line(length = 0.1, event_name = 'experiment_start')
        
        
    key_values['num_rounds'] = int(key_values['num_rounds'])


    #set delay between lever_press and reward
    day_num = int(setup_dictionary['day'])
    if day_num > len(key_values['delay by day']):
        delay = key_values['delay default']
    else:
        delay = key_values['delay by day'][day_num-1]

    ### master looper ###
    print(f"range for looping: {[i for i in range(1, key_values['num_rounds']+1,1)]}")
    

    #start at round 1 instead of the pythonic default of 0 for readability
    for i in range(1, key_values['num_rounds']+1,1):
        fn.monitor_first_beam_breaks()

        round_start = time.time()
        
        fn.round = i
        fn.pulse_sync_line(length = 0.1, event_name = 'new_round')
        print(f"\n\n\n#-#-#-#-#-# new round #{i}!!!-#-#-#-#-#\n\n\n")
        
        #round start buzz
        fn.timestamp_queue.put(f'{fn.round}, Starting new round, {time.time()-fn.start_time}') 
        fn.buzz(**round_buzz, wait = True)
        
        
        fn.extend_lever(lever_ID = ['door_1', 'door_2'])
        fn.monitor_levers(lever_ID = ['door_1', 'door_2'])

        time_II_start = time.time()
        
        #reset our info about whether the animal has pressed
        press = False
        fn.countdown_timer(time_interval = key_values['time_II'], 
                            next_event = 'levers retracted')
        while time.time() - time_II_start < key_values['time_II']:
            if not fn.lever_press_queue.empty() and not press:

                #get which door was pressed    
                lever_press = fn.lever_press_queue.get()

                fn.pulse_sync_line(length = 0.025, event_name = 'lever_press')
                
                #retract lever
                fn.monitor = False
                fn.retract_levers(lever_ID = ['door_1', 'door_2'])
                
                #do not give reward until after delay
                time.sleep(delay)
                fn.buzz(**door_open_buzz, wait = True)

                #open the door of the lever that was pressed 
                fn.open_door(door_ID = lever_press)

                approx_time_left = np.round(key_values['round_time'] - (time.time()-round_start) )
                fn.countdown_timer(time_interval = approx_time_left, next_event = 'move animal')

                press = True
                
            time.sleep(0.05)
            
        #if the vole didnt press:
        if press == False:
            print('no lever press')
            fn.monitor = False
            
            fn.retract_levers(lever_ID = ['door_1', 'door_2'])

            approx_time_left = np.round(key_values['round_time'] - (time.time()-round_start) )
            fn.countdown_timer(time_interval = approx_time_left, next_event = 'move animal')

        while time.time() - round_start < key_values['round_time']:

            time.sleep(0.5)
        
        #if the door was opened, close it
        if press:
            fn.buzz(**door_close_buzz, wait = True)
            time.sleep(0.5)
            fn.close_doors(door_ID = lever_press)
        
        
        
        print('\n\ntime to move that vole over!')
        fn.timestamp_queue.put(f'{fn.round}, start of move animal time, {time.time()-fn.start_time}')
        
        move_ani_start = time.time()
        approx_time_left = np.round(key_values['move_time'] - (time.time()-move_ani_start) )
        fn.countdown_timer(time_interval=approx_time_left, next_event = 'next round')

        while time.time() - move_ani_start < key_values['move_time']:
            time.sleep(1)
        print('\nvole should be moved now')
    
    
    fn.clean_up(wait = True)
    
    
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
        day = input(f'Which {exp} day is this? (for training)\n')
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

    setup_dict = setup()
    
    run_script(setup_dict)
