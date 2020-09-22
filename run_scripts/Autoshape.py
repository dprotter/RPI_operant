import sys
sys.path.append('/home/pi/RPI_operant/')

import home_base.functions as FN
fn = FN.runtime_functions()

import threading
import time




default_setup = setup_dict = {'vole':'000','day':1, 'experiment':'Autoshape',
                    'user':'Test User', 'output_directory':'/home/pi/test_outputs/'}


key_values = {'num_rounds': 15, 
              'round_time':120, 
              'time_II':30,
              'time_IV':0, 
              'pellet_tone_time':1, 
              'pellet_tone_hz':5000,
              'door_close_tone_time':1, 
              'door_close_tone_hz':7000,
              'door_open_tone_time':1,
              'door_open_tone_hz':10000,
              'round_start_tone_time':1, 
              'round_start_tone_hz':3000}

key_values_def = {'num_rounds':'number of rounds', 
                  'round_time':'total round length',
                  'time_II':'time after levers out before pellet',
                  'time_IV':'''time after pellet delivered before levers retracted''',
                  'pellet_tone_time':'in s', 
                  'pellet_tone_hz':'in hz',
                  'door_close_tone_time':'in s', 
                  'door_close_tone_hz':'in hz',
                  'door_open_tone_time':'in s',
                  'door_open_tone_hz':'in hz',
                  'round_start_tone_time':'in s', 
                  'round_start_tone_hz':'in hz'}

#for display purposes. put values you think are most likely to be changed early
key_val_names_order = ['num_rounds', 'round_time', 'time_II', 'time_IV','pellet_tone_time',
                        'pellet_tone_hz','door_close_tone_time','door_close_tone_hz',
                        'door_open_tone_time','door_open_tone_hz', 'round_start_tone_time',
                        'round_start_tone_hz']

def setup(setup_dictionary = None):
    #run this to get the RPi.GPIO pins setup
    if setup_dictionary == None:
        setup_dictionary = default_setup
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
    fn.close_door()
    
    ##### start timing this session ######
    fn.start_timing()
    fn.pulse_sync_line(0.1)
    
    for x in range(5):

        #spin up threads for the thread distributor
        t = threading.Thread(target = fn.thread_distributor)

        #when main thread finishes, kill these threads
        t.daemon = True
        t.start()
        
        

    ### master looper ###
    print(f"range for looping: {[i for i in range(1, key_values['num_rounds']+1,1)]}")
    
    #start at round 1 instead of the pythonic default of 0 for readability
    for i in range(1, key_values['num_rounds']+1,1):
        round_start = time.time()
        fn.round = i
        print("#-#-#-#-#-# new round #%i!!!-#-#-#-#-#"%i)
        
        #round start buzz
        fn.timestamp_queue.put(f'{fn.round}, Starting new round, {time.time()-fn.start_time}') 
        fn.do_stuff_queue.put(('buzz',round_buzz))
        fn.do_stuff_queue.join()
        
        fn.do_stuff_queue.put(('extend lever',
                            ('food')))
        
        fn.do_stuff_queue.put(('monitor lever',
                           ('food')))
        
        
        time_II_start = time.time()
        
        #reset our info about whether the animal has pressed
        press = False
        while time.time() - time_II_start < key_values['time_II']:
            if not fn.lever_press_queue.empty() and not press:
                fn.pulse_sync_line(0.025)
                fn.do_stuff_queue.put(('buzz', pellet_buzz))
                fn.monitor = False
                
                fn.do_stuff_queue.put(('retract lever',
                                    ('food')))
                fn.do_stuff_queue.put(('dispense pellet',))
                
                press = True
            time.sleep(0.05)
            
        #if the vole didnt press:
        if press == False:
            print('no lever press')
            fn.do_stuff_queue.put(('buzz', pellet_buzz))
            fn.do_stuff_queue.put(('dispense pellet',))
        
        time.sleep(key_values['time_IV'])
        
        if press == False:
            fn.monitor = False
            fn.do_stuff_queue.put(('retract lever',
                                    ('food')))
        
        while time.time() - round_start < key_values['round_time']:
            time.sleep(0.1)
        
    if fn.pellet_state:
        fn.timestamp_queue.put('%i, final pellet not retrieved, %f'%(fn.round, time.time()-fn.start_time))
    
    fn.do_stuff_queue.put(('clean up',))
    fn.do_stuff_queue.join()
    
    
if __name__ == '__main__':
    print('running directly, please enter relevant info.\n')
    
    test_run = input('is this just a quick test run? if so, we will just do 1 round. (y/n)\n')
    if test_run.lower() in ['y', 'yes']:
        print('ok, test it is!')
        key_values['num_rounds'] = 1
        key_values['round_time'] = 20
        
    
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
        
        
        default_setup['vole'] = vole
        default_setup['user'] = user
        default_setup['output_directory'] = '/home/pi/Operant_Output/script_runs/'

    setup(setup_dictionary=default_setup)
    run_script()