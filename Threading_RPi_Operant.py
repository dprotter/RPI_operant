import threading
import numpy as np
import queue
import time
import random
import os
import csv
import RPi.GPIO as GPIO
from adafruit_servokit import ServoKit
global kit
kit = ServoKit(channels=16)
##### double check which servo is which. I'm writing this as:
##### kit[0] = food lever
##### kit[1] = partner lever
##### kit[2] = door

servo_dict = {'food':kit.servo[0], 'social':kit.servo[1], 'door':kit.servo[2]}

GPIO.setmode(GPIO.BOARD)


round_time = 7
pellet_tone_time = 2 #how long the pellet tone plays
timeII = 2 #time after levers out before pellet
timeIV = 2 #time after pellet delivered before levers retracted
loops = 5



#our queues for doign stuff and saving
do_stuff_queue = queue.Queue()
timestamp_queue = queue.Queue()
lever_press_queue = queue.Queue()



#depricated for now, will try with a dedicated queue
global interrupt
interrupt = False

global monitor
monitor = False

global start_time
start_time = time.time()

#setup our pins. Lever pins are input, all else are output
pins = {'lever_food':36,'step':35,'direction':33, 'sleep':37, 'micro16':38,
'led_food':40, 'dispense_pellet':100, 'read_pellet_out':101,
'read_pellet_retrieve':101}
for k in pins.keys():
    if 'lever' or 'read' in k:
        GPIO.setup(pins[k], GPIO.IN, pull_up_down=GPIO.PUD_UP)
    elif 'led' or 'dispence' in k:
        GPIO.setup(pins[k], GPIO.OUT)
        GPIO.output(pins[k], 0)
    else:
        GPIO.setup(pins[k], GPIO.OUT)


#turn motor on
GPIO.output(pins['sleep'],0)
#turn on 1/16th microstepping
GPIO.output(pins['micro16'], 1)


def run_job(job, q, args = None):
    print('job: ' + str(job) + '    args: ' +str(args))

    '''parse and run jobs'''

    jobs = {'extend lever':extend_lever,
            'dispence pellet':dispence_pellet,
            'retract lever':retract_lever,
            'start tone':experiment_start_tone,
            'pellet tone':pellet_tone,
            'monitor lever':monitor_lever
            }
    if args:
        jobs[job](q, args)
    else:
        jobs[job](q)

def flush_timestamp_to_CSV(q):
    """flush the timestamp queue to a csv file"""

def monitor_lever(ds_queue, args):
    global monitor
    global start_time
    global interrupt

    monitor = True
    lever_q, lever_ID = args
    "monitor a lever. If lever pressed, put lever_ID in queue. "
    lever=0
    not_lever = 0

    ds_queue.task_done()
    while monitor:
        if GPIO.input(pins["lever_%s"%lever_ID]):
            not_lever +=1
        else:
            lever +=1

        #just guessing on this value, should probably check somehow empirically
        if lever > 4:
            if not interrupt:
                lever_q.put(lever_ID)
                timestamp_queue.put('%s lever pressed with interrupt, %f'%(time.time()-start_time))
                while GPIO.input(pins["lever_%s"%lever_ID]):
                    'hanging till lever not pressed'
                lever = 0
            else:
                #we can still record from the lever until monitoring is turned
                #off. note that this wont place anything in the lever_press queue,
                #as that is just to tell the main thread the vole did something
                timestamp_queue.put('%s lever pressed, %f'%(time.time()-start_time))
                while GPIO.input(pins["lever_%s"%lever_ID]):
                    'hanging till lever not pressed'
                lever = 0

        time.sleep(50/1000.0)
    print('halting monitoring of %s lever'%lever_ID)

def extend_lever(q, args):
    global start_time
    global servo_dict
    lever_ID = args[0]
    print('extending lever %s'%lever_ID)
    print('LEDs on')
    servo_dict{'lever_ID'}.angle = 145
    GPIO.output(pins['led_%s'%lever_ID], 1)
    timestamp_queue.put('Levers out, %f'%(time.time()-start_time))
    q.task_done()

def retract_lever(q, args):
    global start_time
    global servo_dict
    lever_ID = args[0]
    print('LEDs off')
    GPIO.output(pins['led_%s'%lever_ID], 0)
    servo_dict[lever_ID].angle(0)
    print('retracting levers')
    timestamp_queue.put('Levers retracted, %f'%(time.time()-start_time))
    q.task_done()

def pellet_tone(q):
    global start_time
    print('starting pellet tone')
    timestamp_queue.put('pellet tone start, %f'%(time.time()-start_time))
    time.sleep(1)
    print('pellet tone complete')
    timestamp_queue.put('pellet tone complete, %f'%(time.time()-start_time))
    q.task_done()

'''def dispence_pellet(q):
    print('sending dispence pellet signal')
    print('monitoring pellet arrival over serial')
    timestamp_queue.put('pellet out, %f'%(time.time()-start_time))
    time.sleep(random.randrange(5,10,1)/2)
    timestamp_queue.put('pellet taken, %f'%(time.time()-start_time))
    q.task_done()'''

'''def dispence_pellet(q):
    "this needs a timestamp"
    global start_time
    GPIO.output(pins['sleep'],1)
    print('dispencing pellet')
    start = time.time()
    seq =[]
    for i in range(200):
        GPIO.output(pins['step'], 1)
        time.sleep(5.0/1000)
        GPIO.output(pins['step'], 0)
        time.sleep(5.0/1000)
        seq.append(time.time()-start)
        start = time.time()

    mean_step_t = np.asarray(seq).mean()
    print("pellet dispensed succesfully with %f ms mean step"%(mean_step_t))
    GPIO.output(pins['sleep'],0)
    q.task_done()'''

def dispence_pellet(q):
    print('sending dispence pellet signal')
    GPIO.output(pins['dispense_pellet'], 1)
    q.task_done()
    start_mon = time.time()
    timeout = round_time - timeII - timeIV - 1 #round time minus intervals and start tone time
    pellet_out = False

    while time.time()- start_mon  < timeout:
        if GPIO.input(pins['read_pellet_out']):
            not_lever +=1
        else:
            lever +=1
        #just guessing on this value, should probably check somehow empirically
        if lever > 4:
            GPIO.output(pins['dispense_pellet'], 0)
            timestamp_queue.put('pellet out, %f'%(time.time()-start_time))
            print('pellet out')
            break
        time.sleep(0.05)


    if pellet_out:
        print('monitoring pellet arrival over serial')
        while time.time()- start_time  < timeout:
            if GPIO.input(pins['read_pellet_retrieve']):
                not_lever +=1
            else:
                lever +=1
            #just guessing on this value, should probably check somehow empirically
            if lever > 4:
                GPIO.output(pins['dispense_pellet'], 0)
                timestamp_queue.put('pellet taken, %f'%(time.time()-start_time))
                print('pellet out')
                break
            time.sleep(0.05)
    else:
        print('animal did not retrieve pellet before end of ITI!!!')

    return ''


def experiment_start_tone(q):
    global start_time
    print('starting experiment tone')
    timestamp_queue.put('experiment start tone start, %f'%(time.time()-start_time))
    time.sleep(2)
    print('experiment tone complete')
    timestamp_queue.put('experiment start tone start complete, %f'%(time.time()-start_time))
    q.task_done()


def thread_distributor():
    '''this is main thread's job. To look for shit to do and send it to a thread'''
    while True:
        if not do_stuff_queue.empty():
            do = do_stuff_queue.get()
            name = do[0]
            args = None
            if len(do) >1:
                args = do[1]

            run_job(name, do_stuff_queue, args)
            time.sleep(0.05)


for x in range(4):

    t = threading.Thread(target = thread_distributor)
    t.daemon = True
    t.start()
    print("started %i"%x )


### master looper ###
for i in range(loops):
    round_start = time.time()
    print("new round #%i!!!"%i)
    timestamp_queue.put('Starting new round, %f'%(time.time()-start_time))
    do_stuff_queue.put(('start tone',))

    #wait till tone is done
    do_stuff_queue.join()


    do_stuff_queue.put(('extend lever', ('food',)))

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
        if not interrupt and not lever_press_queue.empty():
            interrupt = True
            lever_ID = lever_press_queue.get()
            print('the %s lever was pressed! woweeeee'%lever_ID)
            timestamp_queue.put('a lever was pressed! woweeeee, %f'%(time.time()-start_time))
            do_stuff_queue.put(('pellet tone',))
            do_stuff_queue.put(('dispence pellet',))
            do_stuff_queue.join()
        time.sleep(0.05)

    #waited the interval for timeII, nothing happened
    if not interrupt:
        print('the vole is dumb and didnt press a lever')
        do_stuff_queue.put(('pellet tone',))
        do_stuff_queue.put(('dispence pellet',))
        time.sleep(0.05)
        do_stuff_queue.join()

    time.sleep(0.05)

    do_stuff_queue.put(('retract lever', ('food',)))

    time.sleep(timeIV)
    print('entering ITI')

    #wait for ITI to pass
    while time.time() - round_start < round_time:
        '''just hanging'''

    #reset our global values interrupt and monitor. This will turn off the lever
    #if it is still being monitored. This resets the inerrupt value for the next
    #loop of the training.
    interrupt = False
    monitor = False


print("all Done")
'''os.chdir('/Users/davidprotter/Desktop/Testing Pi stuff/')

with open('output.txt', 'w') as csv_file:
    csv_writer = csv.writer(csv_file)
    while not timestamp_queue.empty():
        csv_writer.writerow(timestamp_queue.get().split(','))'''
