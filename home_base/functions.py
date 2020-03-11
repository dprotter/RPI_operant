"""all of the necessary functions for running the operant pi boxes"""
import RPi.GPIO as GPIO
import os
if os.system('sudo lsof -i TCP:8888'):
    os.system('sudo pigpiod')
import socket
import time
from home_base.operant_cage_settings import (kit, pins,
    lever_angles, continuous_servo_speeds,servo_dict)
import datetime
import csv
from home_base.email_push import email_push
import numpy as np
import queue
import random
import pigpio
pi = pigpio.pi()


#our queues for doign stuff and saving stuff
do_stuff_queue = queue.Queue()
timestamp_queue = queue.Queue()
lever_press_queue = queue.Queue()


user = None
this_path = ''

done = False

round = 0

start_time = None

#in case we need to interrupt after a lever press.
interrupt = False

#whether or not to monitor levers.
monitor = False

#is there a pellet currently in the trough?
pellet_state = False

#are we overriding the door activity?
door_override = {'door_1':False, 'door_2':False}


#true = closed, false = open
door_states = {'door_1':False, 'door_2':False}

#timeout for closing the doors
door_close_timeout = 10

def start_timing():
    global start_time
    start_time = time.time()


def setup_experiment(args_dict):

    global this_path

    if args_dict['user']=='':
        while no_user:
            user = input('no user listed. who is doing this experiment? \n')

            check = input('ok, double check its %s ? (y/n) \n'%user)
            if check.lower() in ['y', 'yes']:
                no_user = False
    else:
        user = args_dict['user']

    #unpack dict, but just to make string assembly cleaner for the first
    #line of the output file.
    vole = args_dict['vole']
    save_dir = args_dict['output_directory']
    exp = args_dict['experiment']
    day = args_dict['day']


    date = datetime.datetime.now()
    fdate = '%s_%s_%s__%s_%s_'%(date.month, date.day, date.year, date.hour, date.minute)
    print('date is: \n')
    print(datetime.date.today())

    fname = fdate+f'_vole_{vole}.csv'
    this_path = os.path.join(save_dir, fname)



    print('Path is: ')
    print(this_path)
    with open(this_path, 'w') as file:
        writer = csv.writer(file, delimiter = ',')
        writer.writerow(['user: %s'%user, 'vole: %s'%vole, 'date: %s'%date,
        'experiment: %s'%exp, 'Day: %i'%day, 'Pi: %s'%socket.gethostname()])

        writer.writerow(['Round, Event', 'Time'])


'''def skip_setup(exp = 'Generic Test', save_dir = '/home/pi/Operant_Output', day = 0, user = None):
    if you want to run a test script without entering any info
    #get user info
    #get vole number
    #push to email after done?

    user = 'Test'

    vole = '000'


    push = 'y'


    """fname will be of format m_d_y__h_m_vole_#_fresh.csv. fresh will be removed
    once the file has been send via email."""

    date = datetime.datetime.now()
    fdate = '%s_%s_%s__%s_%s_'%(date.month, date.day, date.year, date.hour, date.minute)

    fname = fdate+'_vole_%s.csv'%vole
    path = os.path.join(save_dir, fname)

    with open(path, 'w') as file:
        writer = csv.writer(file, delimiter = ',')
        writer.writerow(['user: %s'%user, 'vole: %s'%vole, 'date: %s'%date,
        'experiment: %s'%exp, 'Day: %i'%day, 'Pi: %s'%socket.gethostname()])
        writer.writerow(['Round, Event', 'Time'])

    return path'''

def setup_pins():
    '''here we get the gpio pins setup, and instantiate pigpio object.'''
    #setup our pins. Lever pins are input, all else are output
    GPIO.setmode(GPIO.BCM)


    for k in pins.keys():
        print(k)
        if 'lever' in k or 'switch' in k:
            print(k + ": IN")
            GPIO.setup(pins[k], GPIO.IN, pull_up_down=GPIO.PUD_UP)
        elif 'read' in k:
            print(k + ": IN")
            GPIO.setup(pins[k], GPIO.IN, pull_up_down=GPIO.PUD_UP)
        elif 'led' in k or 'dispense' in k :
            GPIO.setup(pins[k], GPIO.OUT)
            GPIO.output(pins[k], 0)
            print(k + ": OUT")
        else:
            GPIO.setup(pins[k], GPIO.OUT)
            print(k + ": OUT")

def reset_doors():

    #check if the doors are closed
    if not GPIO.input(pins['door_1_state_switch']):
        door_states['door_1'] = True

    if not GPIO.input(pins['door_2_state_switch']):
        door_states['door_2'] = True

    #get the open doors (door_state == False)
    open_doors = [id for id in ['door_1', 'door_2'] if not door_states[id]]

    for door_ID in open_doors:
        start = time.time()

        #if its the first time the door has been overriden, we will open again slightly.
        first_override = True
        while not door_states[door_ID] and time.time()-start < door_close_timeout:
                if not door_override[door_ID]:
                    servo_dict[door_ID].throttle = continuous_servo_speeds[door_ID]['close']

                #we will close the door until pins for door close are raised, or until timeout
                if not GPIO.input(pins[f'{door_ID}_state_switch']):
                    door_states[door_ID] = True
                    servo_dict[door_ID].throttle = continuous_servo_speeds[door_ID]['stop']
                elif door_override[door_ID] and first_override:
                    servo_dict[door_ID].throttle = continuous_servo_speeds[door_ID]['open']
                    time.sleep(0.1)
                    servo_dict[door_ID].throttle = continuous_servo_speeds[door_ID]['stop']

        if not door_states[door_ID]:
            print(f'ah crap, door {door_ID} didnt close!')
        else:


def open_door(q, args):
    '''open a door!'''
    door_ID = args

    timestamp_queue.put('%i, %s open begin, %f'%(round, door_ID, time.time()-start_time))
    servo_dict[door_ID].throttle = continuous_servo_speeds[door_ID]['open']
    open_time = continuous_servo_speeds[door_ID]['open time']
    start = time.time()
    while time.time() < ( start + open_time ) and not door_override[door_ID]:
        servo_dict[door_ID].throttle = continuous_servo_speeds[door_ID]['stop']
    if not GPIO.input(pins[f'{door_ID}_state_switch']):
        print(f'{door_ID} failed to open!!!')
        timestamp_queue.put('%i, %s open failure, %f'%(round, door_ID, time.time()-start_time))
    else:
        timestamp_queue.put('%i, %s open finish, %f'%(round, door_ID, time.time()-start_time))
        door_states[door_ID] = False
    q.task_done()



def close_door(q, args):
    global door_states

    door_ID= args

    timestamp_queue.put('%i, %s close begin, %f'%(round, door_ID, time.time()-start_time))

    start = time.time()

    #if its the first time the door has been overriden, we will open again slightly.
    first_override = True
    while not door_states[door_ID] and time.time()-start < door_close_timeout:
            if not door_override[door_ID]:
                servo_dict[door_ID].throttle = continuous_servo_speeds[door_ID]['close']

            #we will close the door until pins for door close are raised, or until timeout
            if not GPIO.input(pins[f'{door_ID}_state_switch']):
                door_states[door_ID] = True
                servo_dict[door_ID].throttle = continuous_servo_speeds[door_ID]['stop']
            elif door_override[door_ID] and first_override:
                servo_dict[door_ID].throttle = continuous_servo_speeds[door_ID]['open']
                time.sleep(0.1)
                servo_dict[door_ID].throttle = continuous_servo_speeds[door_ID]['stop']

    if not door_states[door_ID]:
        print(f'ah crap, door {door_ID} didnt close!')

    q.task_done()


#### run in a dedicated thread so we can open the doors whenever necessary
def override_door_1():
    global door_override

    while True:
        if not GPIO.input(pins['door_1_override_open_switch']):
            door_override['door_1'] = True
            servo_dict['door_1'].throttle = continuous_servo_speeds['door_1']['open']
            while not GPIO.input(pins['door_1_override_open']):
                time.sleep(0.05)
            servo_dict['door_1'].throttle = continuous_servo_speeds['door_1']['stop']
        if not GPIO.input(pins['door_1_override_close']):
            door_override['door_1'] = True
            servo_dict['door_1'].throttle = continuous_servo_speeds['door_1']['close_full']
            while not GPIO.input(pins[f'door_1_override_close']):
                time.sleep(0.05)
            servo_dict['door_1'].throttle = continuous_servo_speeds['door_1']['stop']
        door_override['door_1'] = False


        time.sleep(0.1)

#### run in a dedicated thread so we can open the doors whenever necessary
def override_door_2():
    global door_override

    while True:
        if not GPIO.input(pins['door_2_override_open_switch']):
            door_override['door_2'] = True
            servo_dict['door_2'].throttle = continuous_servo_speeds['door_2']['open']
            while not GPIO.input(pins['door_1_override_open']):
                time.sleep(0.05)
            servo_dict['door_2'].throttle = continuous_servo_speeds['door_2']['stop']
        if not GPIO.input(pins['door_1_override_close']):
            door_override['door_2'] = True
            servo_dict['door_2'].throttle = continuous_servo_speeds['door_2']['close_full']
            while not GPIO.input(pins['door_2_override_close']):
                time.sleep(0.05)
            servo_dict['door_2'].throttle = continuous_servo_speeds['door_2']['stop']
        door_override['door_2'] = False


        time.sleep(0.1)


def run_job(job, q, args = None):
    print('job: ' + str(job) + '    args: ' +str(args))

    '''parse and run jobs'''

    jobs = {'extend lever':extend_lever,
            'dispense pellet':dispense_pellet,
            'retract lever':retract_lever,
            'buzz':buzz,
            'monitor lever':monitor_lever,
            'dispense pellet':dispense_pellet,
            'read pellet':read_pellet,
            'close door':close_door,
            'open door':open_door,
            'door override 1':override_door_1,
            'door override 2':override_door_2,
            'clean up':clean_up
            }

    if args:
        jobs[job](q, args)
    else:
        jobs[job](q)

def monitor_lever_test(q, args):
    global monitor

    monitor = True
    lever_ID = args
    "monitor a lever. If lever pressed, put lever_ID in queue. "
    lever=0

    do_stuff_queue.task_done()
    while monitor:
        if not GPIO.input(pins["lever_%s"%lever_ID]):
            lever +=1

        #just guessing on this value, should probably check somehow empirically
        if lever > 2:
            if not interrupt:
                #send the lever_ID to the lever_q to trigger a  do_stuff.put in
                #the main thread/loop

                lever_press_queue.put(lever_ID)

                timestamp_queue.put('%i, %s lever pressed productive, %f'%(round, lever_ID, time.time()-start_time))
                print(f'{lever_ID} pressed! neato.')
                while not GPIO.input(pins["lever_%s"%lever_ID]):
                    'hanging till lever not pressed'
                    time.sleep(0.05)
                lever = 0
            else:
                #we can still record from the lever until monitoring is turned
                #off. note that this wont place anything in the lever_press queue,
                #as that is just to tell the main thread the vole did something
                timestamp_queue.put('%i, %s lever pressed, %f'%(round, lever_ID, time.time()-start_time))
                while GPIO.input(pins["lever_%s"%lever_ID]):
                    'hanging till lever not pressed'
                lever = 0

        time.sleep(25/1000.0)
    print('halting monitoring of %s lever'%lever_ID)

def monitor_lever(q, args):
    global monitor

    monitor = True
    lever_ID = args
    "monitor a lever. If lever pressed, put lever_ID in queue. "
    lever=0

    do_stuff_queue.task_done()
    while monitor:
        if not GPIO.input(pins["lever_%s"%lever_ID]):
            lever +=1

        #just guessing on this value, should probably check somehow empirically
        if lever > 2:
            if not interrupt:
                #send the lever_ID to the lever_q to trigger a  do_stuff.put in
                #the main thread/loop

                lever_press_queue.put(lever_ID)

                timestamp_queue.put('%i, %s lever pressed productive, %f'%(round, lever_ID, time.time()-start_time))
                while not GPIO.input(pins["lever_%s"%lever_ID]):
                    'hanging till lever not pressed'
                    time.sleep(0.05)
                lever = 0
            else:
                #we can still record from the lever until monitoring is turned
                #off. note that this wont place anything in the lever_press queue,
                #as that is just to tell the main thread the vole did something
                timestamp_queue.put('%i, %s lever pressed, %f'%(round, lever_ID, time.time()-start_time))
                while not GPIO.input(pins["lever_%s"%lever_ID]):
                    'hanging till lever not pressed'
                    time.sleep(0.05)
                lever = 0

        time.sleep(25/1000.0)
    print('halting monitoring of %s lever'%lever_ID)

def extend_lever(q, args):

    lever_ID, retract, extend = args
    print('extending lever %s'%lever_ID)
    print('LEDs on')
    servo_dict[lever_ID].angle = extend
    GPIO.output(pins['led_%s'%lever_ID], 1)
    timestamp_queue.put('%i, Levers out, %f'%(round, time.time()-start_time))
    q.task_done()

def retract_lever(q, args):

    lever_ID, retract, extend = args
    while GPIO.input(pins["lever_%s"%lever_ID]):
        'hanging till lever not pressed'
        time.sleep(0.05)
    print('LEDs off')
    GPIO.output(pins['led_%s'%lever_ID], 0)
    servo_dict[lever_ID].angle = retract
    print('retracting levers')
    timestamp_queue.put('%i, Levers retracted, %f'%(round, time.time()-start_time))
    q.task_done()

def buzz(q, args):
    '''take time (s), hz, and name as inputs'''

    buzz_len, hz, name = args

    print(f'starting {name} tone {hz} hz')

    #set a 50% duty cycle, pass desired hz
    pi.set_PWM_dutycycle(pins['speaker_tone'], 255/2)
    pi.set_PWM_frequency(pins['speaker_tone'], hz)

    timestamp_queue.put(f'{round}, {name} tone start {hz}:hz {buzz_len}:seconds, {time.time()-start_time}')

    time.sleep(buzz_len)

    #sound off
    pi.set_PWM_dutycycle(pins['speaker_tone'], 0)

    print(f'{name} tone complete')
    timestamp_queue.put(f'{round}, {name} tone complete {hz}:hz {buzz_len}:seconds, {time.time()-start_time}')
    q.task_done()


def door_close_tone(q):
    '''can replace with buzz()'''

    q.task_done()

def dispense_pellet(q):

    global pellet_state

    q.task_done()
    timeout = time.time()


    read = 0

    #only dispense if there is no pellet, otherwise skip
    if not pellet_state:
        print('%i, starting pellet dispensing %f'%(round, time.time()-start_time))

        #we're just gonna turn the servo on and keep monitoring. probably
        #want this to be a little slow

        servo_dict['dispense_pellet'].throttle = continuous_servo_speeds['dispense_pellet']['fwd']

        #set a timeout on dispensing. with this, that will be a bit less than
        #6 attempts to disp, but does give the vole 2 sec in which they could nose
        #poke and trigger this as "dispensed"
        while time.time()-timeout < 3:

            if not GPIO.input(pins['read_pellet']):
                print('blocked')
                read +=1

            if read > 2:
                servo_dict['dispense_pellet'].throttle = continuous_servo_speeds['dispense_pellet']['stop']
                timestamp_queue.put('%i, Pellet dispensed, %f'%(round, time.time()-start_time))
                print('Pellet dispensed, %f'%(time.time()-start_time))

                #now there is a pellet!
                pellet_state = True

                #offload monitoring to a new thread
                do_stuff_queue.put(('read pellet',))
                return ''

            else:
                #wait to give other threads time to do stuff, but fast enough
                #that we check pretty quick if there's a pellet
                time.sleep(0.025)
        servo_dict['dispense_pellet'].throttle = continuous_servo_speeds['dispense_pellet']['stop']
        timestamp_queue.put('%i, Pellet dispense failure, %f'%(round, time.time()-start_time))
        return ''
    else:
        print("skipping pellet dispense due to pellet not retrieved")
        timestamp_queue.put('%i, skip pellet dispense, %f'%(round, time.time()-start_time))
        return ''

def pulse_sync_line():
    '''not terribly accurate, but good enough. For now, this is called on every
    lever press or pellet retrieval. I can't imagine a situation yet'''
    GPIO.output(pins['gpio_sync'], 1)
    time.sleep(0.08)
    GPIO.output(pins['gpio_sync'], 0)

def clean_up(q):
    global done

    done = True
    '''cleanup all servos etc'''
    servo_dict['food'].angle = lever_angles['food'][0]
    servo_dict['door_1'].angle = lever_angles['door_1'][0]
    servo_dict['door_2'].angle = lever_angles['door_2'][0]
    servo_dict['door_1'].throttle = continuous_servo_speeds['door_1']['stop']
    servo_dict['door_2'].throttle = continuous_servo_speeds['door_2']['stop']
    servo_dict['dispense_pellet'].throttle = continuous_servo_speeds['dispense_pellet']['stop']
    q.task_done()

def breakpoint_monitor_lever(q,args):
    '''this lever monitor function tracks presses and returns when breakpoint reached'''
    global monitor
    monitor = True
    lever_q, lever_ID= args
    "monitor a lever. If lever pressed, put lever_ID in queue. "
    lever=0
    do_stuff_queue.put(('extend lever',
                        (lever_ID,lever_angles[lever_ID][0],lever_angles[lever_ID][1])))

    do_stuff_queue.task_done()
    while monitor:
        if not GPIO.input(pins["lever_%s"%lever_ID]):
            lever +=1

        #just guessing on this value, should probably check somehow empirically
        if lever > 2:

            #send the lever_ID to the lever_q to trigger a  do_stuff.put in
            #the main thread/loop
            pulse_sync_line()
            timestamp_queue.put('%i, %s lever pressed, %f'%(round, lever_ID, time.time()-start_time))


            do_stuff_queue.put(('retract lever',
                                (lever_ID, lever_angles[lever_ID][0],lever_angles[lever_ID][1])))

            lever_press_queue.put(lever_ID)
            lever = 0
            monitor = False
            break

        time.sleep(25/1000.0)
    print('\nmonitor thread done')

def read_pellet(q):
    global pellet_state

    disp_start = time.time()
    q.task_done()
    disp = False
    #retrieved, IE empty trough
    read_retr = 0

    #dispensed pellet there, IE full trough
    read_disp = 0
    timeout = 2000

    while time.time() - disp_start < timeout:
        #note this is opposite of the dispense function
        if GPIO.input(pins['read_pellet']):
            read_retr += 1
        else:
            read_disp += 1

        if read_retr > 5:
            pulse_sync_line()
            timestamp_queue.put('%i, Pellet retrieved, %f'%(round, time.time()-start_time))
            print('Pellet taken! %f'%(time.time()-start_time))
            #no pellet in trough
            pellet_state = False
            return ''

        if read_disp > 3:
            read_retr = 0
            read_disp = 0

        time.sleep(0.05)


    timestamp_queue.put('%i, pellet retreival timeout, %f'%(round, time.time()-start_time))
    return ''

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
        time.sleep(0.05)

def flush_to_CSV():
        '''a good time to write some stuff to file'''
        print('heres the path for the flush func\n%s'%this_path)


        while not done or not timestamp_queue.empty():
            if not timestamp_queue.empty():
                with open(this_path, 'a') as csv_file:
                    csv_writer = csv.writer(csv_file, delimiter = ',')
                    while not timestamp_queue.empty():
                        line = timestamp_queue.get().split(',')
                        print('writing ###### %s'%line)
                        csv_writer.writerow(line)
                        time.sleep(0.005)
            time.sleep(0.01)
