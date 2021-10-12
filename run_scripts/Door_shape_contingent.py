import sys
sys.path.append('/home/pi/')

import RPI_operant.home_base.functions as FN
fn = FN.runtime_functions()

import threading
import time
import numpy as np



default_setup_dict = {'vole':'000','day':1, 'experiment':'Door_shape_contingent',
                    'user':'Test User', 'output_directory':'/home/pi/test_outputs/', 'partner':'door_1', 'novel_num':'000'}


key_values = {'num_rounds': 0,
              'repetitions':5,
              'sets':2,
              'round_time':2*60,
              'reward_time':60,
              'move_time':20,
              'ITI':30,
              'pellet_tone_time':1, 
              'pellet_tone_hz':2500,
              'door_close_tone_time':1, 
              'door_close_tone_hz':7000,
              'door_open_tone_time':1,
              'door_open_tone_hz':10000,
              'round_start_tone_time':1, 
              'round_start_tone_hz':5000,
              'delay by day':[1,2,3,5,5],
              'delay default':5}

key_values['num_rounds'] = 2 * key_values['repetitions'] * key_values['sets']

key_values_def = {'num_rounds':'number of rounds',
                  'repetitions':'number of consecutive rounds',
                  'sets':'number of sets of training (1 set = partner reps + novel reps)',
                  'round_time':'total round length',
                  'reward_time':'time door is left open',
                  'move_time':'seconds to move the vole back to the lever room',
                  'ITI':'time immediately preceeding the start of a new round',
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
key_val_names_order = ['num_rounds', 'repetitions','round_time', 'time_II', 'move_time','pellet_tone_time',
                        'ITI','pellet_tone_hz','door_close_tone_time','door_close_tone_hz',
                        'door_open_tone_time','door_open_tone_hz', 'round_start_tone_time',
                        'round_start_tone_hz']



def setup(setup_dictionary = default_setup_dict, key_val_names_order = key_val_names_order,
                             key_values = key_values,
                             key_values_def = key_values_def):
    
    
    key_values_def, key_val_names_order = fn.check_key_value_dictionaries(key_values, 
                                                                          key_values_def,
                                                                          key_val_names_order)
    
    fn.setup_pins()
    
    ####vvvvvvvv reversed vvvvvvv########
    fn.reverse_lever_position()
    
    
    fn.setup_experiment(setup_dictionary)



    
    return setup_dictionary
    


def run_script(setup_dictionary = None):
    
    #buzz args passed as (time, hz, name), just to make
    #code a little cleaner
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
    
    rep_count = 0
    this_door = 'door_1'
    next_door = 'door_2'



    
    #start at round 1 instead of the pythonic default of 0 for readability
    for i in range(1, key_values['num_rounds']+1,1):
        
        
        if rep_count == key_values['repetitions']:
            'swap doors if we have reach the rep count'
            d = this_door
            this_door = next_door
            next_door = d
            rep_count = 1
        else:
            rep_count += 1

        round_start = time.time()
        
        fn.round = i
        fn.pulse_sync_line(length = 0.1, event_name = 'new_round')
        print(f"\n\n\n#-#-#-#-#-# new round #{i}, rep {rep_count} {this_door}!!!-#-#-#-#-#\n\n\n")
        
        #round start buzz
        fn.timestamp_queue.put(f'{fn.round}, Starting new round, {time.time()-fn.start_time}') 
        fn.buzz(**round_buzz, wait = True)
        
        
        #extend and monitor for presses on whichever door lever we are using on this round
        fn.extend_lever(lever_ID = this_door)
        fn.monitor_levers(lever_ID = this_door)
        
        
        time_II_start = time.time()
        
        #reset our info about whether the animal has pressed
        press = False

        while time.time() - time_II_start < key_values['round_time']:
            if not fn.lever_press_queue.empty() and not press:
                fn.monitor_first_beam_breaks()
                #retract lever
                fn.monitor = False
                
                fn.pulse_sync_line(length = 0.025, event_name = 'lever_press')
                fn.retract_levers(lever_ID=this_door)
                fn.buzz(**door_open_buzz, wait = True)
                #do not give reward until after delay
                time.sleep(delay)
                
                
                #get the lever press tuple just to clear the queue
                lever_press = fn.lever_press_queue.get()

                fn.open_door(door_ID = lever_press)
                
                press = True
                
            time.sleep(0.05)
            
        #if the vole didnt press:
        if press == False:
            fn.monitor = False
            fn.retract_levers(lever_ID = this_door)

        fn.monitor = False
        if press:
            approx_time = key_values['reward_time'] - (time.time() - round_start)
            fn.countdown_timer(time_interval=approx_time, next_event='end of social interaction')
        
            #give the voles interaction time
            while time.time() - round_start < key_values['reward_time']:
                time.sleep(0.5)

        #must stop monitoring beams so we dont trip them when moving the animal
        #(doesnt really matter when only using monitor_first_beam_breaks(), but if continuously monitoring
        # this would be important)
        fn.monitor_beams = False
        
        if press:
            fn.buzz(**door_close_buzz)
            fn.close_door(door_ID = this_door, wait = True)
        
        time.sleep(0.5)
        
        
        print('\n\ntime to move that vole over!')
        fn.timestamp_queue.put(f'{fn.round}, start of move animal time, {time.time()-fn.start_time}')
        
        #time to move the animal
        move_ani_start = time.time()
        approx_time_left = np.round(key_values['move_time'] - (time.time()-move_ani_start))
        fn.countdown_timer(time_interval=approx_time_left, next_event = 'ITI')

        while time.time() - move_ani_start < key_values['move_time']:
            time.sleep(1)
        print('\nvole should be moved now')

        
        ITI_start = time.time()
        approx_time_left = np.round(key_values['ITI'] - (time.time()-ITI_start))
        fn.countdown_timer(time_interval=approx_time_left, next_event = 'next round')
        fn.timestamp_queue.put(f'{fn.round}, start of ITI, {time.time()-fn.start_time}')

        while time.time() - ITI_start < key_values['ITI']:
            time.sleep(1)
        
    
    fn.analyze()
    fn.clean_up()
    time.sleep(1)
    
    
if __name__ == '__main__':
    print('running directly, please enter relevant info.\n')
    
    test_run = input('is this just a quick test run? if so, we will just do 1 round. (y/n)\n')
    if test_run.lower() in ['y', 'yes']:
        print('ok, test it is!')
        key_values['num_rounds'] = 4
        key_values['round_time'] = 10

        key_values['repetitions'] = 2
        key_values['move_time'] = 4
        key_values['ITI'] = 4
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
        default_setup_dict['day'] = day
        default_setup_dict['output_directory'] = '/home/pi/Operant_Output/script_runs/'

    setup_dict = setup()
    
    run_script(setup_dict)
