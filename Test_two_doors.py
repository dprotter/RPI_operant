import sys
sys.path.append('/home/pi/RPI_operant/')

import home_base.functions as fn
from home_base.functions import do_stuff_queue, timestamp_queue, lever_press_queue, lever_angles
import threading
import time



start_time = 0
save_path = ''

comms_queue = None




key_values = {'num_rounds': 2, 'round_time':8, 'timeII':2,
            'timeIV':2, 'pellet_tone_time':2, 'pellet_tone_hz':4000,
            'door_close_tone_time':2, 'door_close_tone_hz':8000,
            'door_open_tone_time':2,'door_open_tone_hz':10000,
            'round_start_tone_time':2, 'round_start_tone_hz':6000}

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

def setup(setup_dictionary):
    #run this to get the RPi.GPIO pins setup
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

    door_open_buzz = (key_values['door_close_tone_time'],
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
        timestamp_queue.put(f'{fn.round}, Starting new round, {time.time()-fn.start_time}')
        do_stuff_queue.put(('buzz',round_buzz))
        time.sleep(1)
        print('ok lets try and open door 1')

        do_stuff_queue.put(('buzz',door_open_buzz))
        do_stuff_queue.join()
        time.sleep(0.5)

        do_stuff_queue.put(('open door',('door_1')))
        do_stuff_queue.join()

        print('ok is door 1 open? ill wait')
        input('just haning till you press enter. then ill close it.')

        do_stuff_queue.put(('buzz',door_close_buzz))
        do_stuff_queue.put(('close door',('door_1')))
        do_stuff_queue.join()

        print('ok is the door closed? ill wait')
        input('just haning till you press enter.')

        print('ok lets try and open door 2')

        do_stuff_queue.put(('buzz',door_open_buzz))
        do_stuff_queue.join()
        time.sleep(0.5)

        do_stuff_queue.put(('open door',('door_2')))
        do_stuff_queue.join()

        print('ok is the door 2 open? ill wait')
        input('just haning till you press enter. then ill close it.')

        do_stuff_queue.put(('buzz',door_close_buzz))
        do_stuff_queue.put(('close door',('door_1')))

        print('ok is the door 2 closed? ill wait')
        input('just haning till you press enter. Then we will try the levers')



        do_stuff_queue.put(('extend lever',
                            ('food',lever_angles['food'][0],lever_angles['food'][1])))

        do_stuff_queue.put(('monitor_lever_test'),(fn.lever_press_queue, 'food'))
        print('ok is the food lever out?')
        input('press any key to move on. feel free to press the lever')
        fn.monitor = False

        do_stuff_queue.put(('retract lever',
                            ('food', lever_angles['food'][0],lever_angles['food'][1])))

        print('ok is the food lever retracted?')
        input('press any key to move on.')

        do_stuff_queue.put(('extend lever',
                            ('door_1',lever_angles['door_1'][0],lever_angles['door_1'][1])))

        do_stuff_queue.put(('monitor_lever_test'),(fn.lever_press_queue, 'lever_1'))
        print('ok is the door_1 lever out?')
        input('press any key to move on. feel free to press the lever')
        fn.monitor = False

        do_stuff_queue.put(('retract lever',
                            ('door_1', lever_angles['door_1'][0],lever_angles['door_1'][1])))

        print('ok is the door_1 lever retracted?')
        input('press any key to move on.')

        do_stuff_queue.put(('extend lever',
                            ('door_2',lever_angles['door_2'][0],lever_angles['door_2'][1])))

        do_stuff_queue.put(('monitor_lever_test'),(fn.lever_press_queue, 'lever_2'))
        print('ok is the door_2 lever out?')
        input('press any key to move on. feel free to press the lever')
        fn.monitor = False

        do_stuff_queue.put(('retract lever',
                            ('door_2', lever_angles['door_2'][0],lever_angles['door_2'][1])))

        print('ok is the door_2 lever retracted?')
        input('press any key to move on.')



        '''do_stuff_queue.put(('start tone',))

        #wait till tone is done
        do_stuff_queue.join()

        do_stuff_queue.put(('extend lever',
                            ('food',lever_angles['food'][0],lever_angles['food'][1])))



        #for the timeII interval, monitor lever and overide pellet timing if pressed
        while time.time() - timeII_start < key_values['timeII']:
            #eventually, here we will call threads to monitor
            #vole position and the levers. here its just random
            if not fn.interrupt and not lever_press_queue.empty():
                fn.interrupt = True
                lever_ID = lever_press_queue.get()
                print('the %s lever was pressed! woweeeee'%lever_ID)
                timestamp_queue.put('%i, a lever was pressed! woweeeee, %f'%(fn.round, time.time()-fn.start_time))
                do_stuff_queue.put(('pellet tone',))
                do_stuff_queue.put(('dispense pellet',))
                do_stuff_queue.join()
            time.sleep(0.05)

        #waited the interval for timeII, nothing happened
        if not fn.interrupt:
            print('the vole is dumb and didnt press a lever')
            timestamp_queue.put('%i, no lever press, %f'%(fn.round, time.time()-fn.start_time))
            do_stuff_queue.put(('pellet tone',))
            do_stuff_queue.put(('dispense pellet',))
            time.sleep(0.05)
            do_stuff_queue.join()

        time.sleep(0.05)

        do_stuff_queue.put(('retract lever',
                            ('food', lever_angles['food'][0],lever_angles['food'][1])))

        time.sleep(key_values['timeIV'])
        print('entering ITI for #-#-# round #%i -#-#-# '%i )

        #wait for ITI to pass


        #reset our global values fn.interrupt and monitor. This will turn off the lever
        #if it is still being monitored. This resets the inerrupt value for the next
        #loop of the training.
        fn.interrupt = False
        fn.monitor = False
        if comms_queue != None:
            comms_queue.put(f'round:{i}')

    if fn.pellet_state:
        timestamp_queue.put('%i, final pellet not retrieved, %f'%(fn.round, time.time()-fn.start_time))

    do_stuff_queue.put(('clean up',))
    while not timestamp_queue.empty():

        time.sleep(0.05)
    #wait for the csv writer
    time.sleep(1)'''


if __name__ == '__main__':
    '''is_test = input('is this just a test? y/n\n')'''
    is_test = 'y'
    if is_test.lower() == 'y':
        setup_dict = {'vole':'000','day':1, 'experiment':'Test_two_doors',
                    'user':'Test User', 'output_directory':'/home/pi/RPI_Operant/test_outputs/'}
    setup(setup_dict)
    run_script()
