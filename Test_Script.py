import sys
sys.path.append('/home/pi/RPI_operant/')

import home_base.functions as fn
from home_base.functions import do_stuff_queue, timestamp_queue, lever_press_queue, lever_angles
import threading
import time



start_time = 0
save_path = ''

comms_queue = None



pellet_tone_time = 2 #how long the pellet tone plays


key_values = {'num_rounds': 3, 'round_time':10, 'timeII':2,
            'timeIV':2}

key_values_def = {'num_rounds':'number of rounds', 'round_time':'total round length',
            'timeII':'time after levers out before pellet', 'timeIV':'''time after pellet delivered before levers retracted'''}

key_val_names_order = ['num_rounds', 'round_time', 'timeII', 'timeIV']



def setup():
    #run this to get the RPi.GPIO pins setup
    fn.setup_pins()

    #this path will eventually be passed from the launcher
    path = fn.skip_setup()
    temp_override_path = '/home/pi/iter2_test/output/test_script_output.csv'
    fn.this_path = temp_override_path

def run_script():

    fn.start_time()
    #spin up threads
    for x in range(7):
        #spin up a dedicated writer thread
        wrt = threading.Thread(target = fn.flush_to_CSV)
        wrt.daemon = True
        wrt.start()
        t = threading.Thread(target = fn.thread_distributor)

        #when main thread finishes, kill these threads
        t.daemon = True
        t.start()
    ### master looper ###

    for i in range(1, key_values['num_rounds']+1,1):
        round_start = time.time()
        fn.round = i
        print("#-#-#-#-#-# new round #%i!!!-#-#-#-#-#"%i)
        timestamp_queue.put('%i, Starting new round, %f'%(fn.round, time.time()-fn.start_time))
        '''do_stuff_queue.put(('start tone',))

        #wait till tone is done
        do_stuff_queue.join()

        do_stuff_queue.put(('extend lever',
                            ('food',lever_angles['food'][0],lever_angles['food'][1])))

        #wait till levers are out before we do anything else. Depending on how
        #fast the voles react to the lever, we may start monitoring before it is
        #actually out.
        do_stuff_queue.join()

        #begin tracking the lever in a thread
        do_stuff_queue.put(('monitor lever', (lever_press_queue, 'food',)))
        '''
        
        timeII_start = time.time()

        do_stuff_queue.put(('dispence pellet',))

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
                do_stuff_queue.put(('dispence pellet',))
                do_stuff_queue.join()
            time.sleep(0.05)

        #waited the interval for timeII, nothing happened
        if not fn.interrupt:
            print('the vole is dumb and didnt press a lever')
            timestamp_queue.put('%i, no lever press, %f'%(fn.round, time.time()-fn.start_time))
            do_stuff_queue.put(('pellet tone',))
            do_stuff_queue.put(('dispence pellet',))
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
        '''hanging till queue empty'''
        time.sleep(0.05)
    #wait for the csv writer
    time.sleep(1)

if __name__ == '__main__':
    setup()
    run_script()
