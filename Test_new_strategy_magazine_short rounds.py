import home_base.functions as fn
from home_base.functions import do_stuff_queue, timestamp_queue, lever_press_queue, lever_angles
import threading
import time
start_time = 0
save_path = ''

round_time = 10
pellet_tone_time = 2 #how long the pellet tone plays
timeII = 2 #time after levers out before pellet
timeIV = 2 #time after pellet delivered before levers retracted
loops = 3

#run this to get the RPi.GPIO pins setup
fn.setup_pins()
path = fn.skip_setup()
fn.this_path = path
wrt = threading.Thread(target = fn.flush_to_CSV)
wrt.daemon = True
wrt.start()

for x in range(7):
    t = threading.Thread(target = fn.thread_distributor)
    t.daemon = True
    t.start()



fn.start_time()
### master looper ###
for i in range(loops):
    round_start = time.time()
    fn.round = i
    print("#-#-#-#-#-# new round #%i!!!-#-#-#-#-#"%i)
    timestamp_queue.put('%i, Starting new round, %f'%(fn.round, time.time()-fn.start_time))
    do_stuff_queue.put(('start tone',))

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

    timeII_start = time.time()

    #for the timeII interval, monitor lever and overide pellet timing if pressed
    while time.time() - timeII_start < timeII:
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
        timestamp_queue.put('%i, no lever press, %f'%(fn.round, time.time()-start_time))
        do_stuff_queue.put(('pellet tone',))
        do_stuff_queue.put(('dispence pellet',))
        time.sleep(0.05)
        do_stuff_queue.join()

    time.sleep(0.05)

    do_stuff_queue.put(('retract lever',
                        ('food', lever_angles['food'][0],lever_angles['food'][1])))

    time.sleep(timeIV)
    print('entering ITI for #-#-# round #%i -#-#-# '%i )

    #wait for ITI to pass


    #reset our global values fn.interrupt and monitor. This will turn off the lever
    #if it is still being monitored. This resets the inerrupt value for the next
    #loop of the training.
    fn.interrupt = False
    fn.monitor = False


if fn.pellet_state:
    timestamp_queue.put('%i, final pellet not retrieved, %f'%(round, time.time()-start_time))

do_stuff_queue.put(('clean up',))
while not timestamp_queue.empty():
    '''hanging till queue empty'''
    time.sleep(0.05)
#wait for the csv writer
time.sleep(1)