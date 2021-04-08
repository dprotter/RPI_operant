import sys
sys.path.append('/home/pi/')

import RPI_operant.home_base.functions as FN
fn = FN.runtime_functions()

import threading
import time



default_setup_dict = {'vole':'000','day':1, 'experiment':'Autoshape',
                    'user':'Test User', 'output_directory':'/home/pi/test_outputs/'}



key_values = {'num_rounds': 20,
              'round_time':90, 
              'time_II':30,
              'pellet_tone_time':1, 
              'pellet_tone_hz':2500,
              'door_close_tone_time':1, 
              'door_close_tone_hz':7000,
              'door_open_tone_time':1,
              'door_open_tone_hz':10000,
              'round_start_tone_time':1, 
              'round_start_tone_hz':5000,
              'delay by day':[0,0,1,1,2],
              'delay default':2}

key_values_def = {'num_rounds':'number of rounds', 
                  'round_time':'total round length',
                  'time_II':'time after levers out before pellet',
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
key_val_names_order = ['num_rounds', 'round_time', 'time_II', 'pellet_tone_time',
                        'pellet_tone_hz','door_close_tone_time','door_close_tone_hz',
                        'door_open_tone_time','door_open_tone_hz', 'round_start_tone_time',
                        'round_start_tone_hz']


def setup(setup_dictionary = default_setup_dict, key_val_names_order = key_val_names_order,
                             key_values = key_values,
                             key_values_def = key_values_def):


    
    
    key_values_def, key_val_names_order = fn.check_key_value_dictionaries(key_values, 
                                                                          key_values_def,
                                                                          key_val_names_order)


    
    fn.setup_pins()
    
    fn.setup_experiment(setup_dictionary)
    return setup_dictionary


def run_script(setup_dictionary = None):
    
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
    
    day_num = int(setup_dictionary['day'])
    if day_num > len(key_values['delay by day']):
        delay = key_values['delay default']
    else:
        delay = key_values['delay by day'][day_num-1]
    

    #start the thread that will print out errors from within threads
    fn.monitor_workers()
    

    #double check the doors are closed. close, if they arent
    fn.reset_chamber()
    
    ##### start timing this session ######
    fn.start_timing()
    fn.pulse_sync_line(length = 0.5, event_name = 'experiment_start')
        
        
    key_values['num_rounds'] = int(key_values['num_rounds'])
    ### master looper ###
    print(f"range for looping: {[i for i in range(1, key_values['num_rounds']+1,1)]}")
    
    #start at round 1 instead of the pythonic default of 0 for readability
    for i in range(1, key_values['num_rounds']+1,1):
        round_start = time.time()
        fn.round = i
        print("#-#-#-#-#-# new round #%i!!!-#-#-#-#-#"%i)
        
        #round start buzz
        fn.timestamp_queue.put(f'{fn.round}, Starting new round, {time.time()-fn.start_time}') 
        fn.buzz(**round_buzz, wait = True)
        
        #extend and monitor for presses on food lever
        fn.extend_lever(lever_ID = 'food')
        fn.monitor_levers(lever_ID = 'food')
        
        
        time_II_start = time.time()
        
        #reset our info about whether the animal has pressed
        press = False

        approx_time = key_values['time_II'] - (time.time() - time_II_start)
        fn.countdown_timer(time_interval=approx_time, next_event='auto-reward')

        while time.time() - time_II_start < key_values['time_II']:
            if not fn.lever_press_queue.empty() and not press:
                
                fn.pulse_sync_line(length = 0.025, event_name = 'lever_press')
                
                #retract lever
                fn.monitor = False
                fn.retract_levers(lever_ID='food')
                
                #do not give reward until after delay
                time.sleep(delay)
                fn.buzz(**pellet_buzz)
                fn.dispense_pellet()
                
                #get the lever press tuple just to clear the queue
                lever_press = fn.lever_press_queue.get()
                press = True
                
            time.sleep(0.05)
            
        #if the vole didnt press:
        if press == False:
            fn.monitor = False
            fn.retract_levers(lever_ID='food')

            print('no lever press')
            fn.buzz(**pellet_buzz)
            fn.dispense_pellet()
            
        approx_time = key_values['round_time'] - (time.time() - round_start)
        fn.countdown_timer(time_interval=approx_time, next_event='next round')

        while time.time() - round_start < key_values['round_time']:
            time.sleep(0.1)
        
    if fn.pellet_state:
        fn.timestamp_queue.put('%i, final pellet not retrieved, %f'%(fn.round, time.time()-fn.start_time))
    
    fn.analyze()
    fn.clean_up()
    
    
if __name__ == '__main__':
    print('running directly, please enter relevant info.\n')
    
    test_run = input('is this just a quick test run? if so, we will just do 1 round. (y/n)\n')
    if test_run.lower() in ['y', 'yes']:
        print('ok, test it is!')
        key_values['num_rounds'] = 2
        key_values['round_time'] = 20
        key_values['time_II'] = 5
        day = input('Which autoshape training day is this? (for training)\n')
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