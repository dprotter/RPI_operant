"""all of the necessary functions for running the operant pi boxes"""
import RPi.GPIO as GPIO
import os
if os.system('sudo lsof -i TCP:8888'):
    os.system('sudo pigpiod')
import time
from home_base.operant_cage_settings import (kit, pins,
lever_angles, continuous_servo_speeds,servo_dict )
import datetime
import csv

import numpy as np
import queue
import random
import pigpio
pi = pigpio.pi()
#our queues for doign stuff and saving stuff
do_stuff_queue = queue.Queue()
timestamp_queue = queue.Queue()
lever_press_queue = queue.Queue()

global round
round = 0

global start_time
start_time = None

#in case we need to interrupt after a lever press.
global interrupt
interrupt = False

#whether or not to monitor levers.
global monitor
monitor = False

#is there a pellet currently in the trough?
global pellet_state
pellet_state = False

path = ''

def start_time():
    global start_time
    start_time = time.time()


def setup_experiment(exp = 'Generic Test', save_dir = '/home/pi/Operant_Output', day = 0):

    #get user info
    #get vole number
    #push to email after done?

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

    day = input(f'Which {exp} training day is this? (starts at day 1)\n')
    day = int(day)

    push = input('should I push the results folder to email after this session? (y/n) \n')

    if push.lower() in 'y':
        print("ok, your results will be emailed to you after this session.")
    else:
        print("Ok, I won't email you.")

    """fname will be of format m_d_y__h_m_vole_#_fresh.csv. fresh will be removed
    once the file has been send via email."""

    date = datetime.datetime.now()
    fdate = '%s_%s_%s__%s_%s_'%(date.month, date.day, date.year, date.hour, date.minute)
    print('date is: \n')
    print(datetime.date.today())

    fname = fdate+'_vole_%s_fresh.csv'%vole
    path = os.path.join(save_dir, fname)
    print('Path is: ')
    print(path)
    with open(path, 'w') as file:
        writer = csv.writer(file, delimiter = ',')
        writer.writerow(['user: %s'%user, 'vole: %s'%vole, 'date: %s'%date, 'experiment: %s'%exp, 'Day: %i'%day])
        writer.writerow(['Round, Event', 'Time'])

    return path

def skip_setup(exp = 'Generic Test', save_dir = '/home/pi/Operant_Output', day = 0):
    '''if you want to run a test script without entering any info'''
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
        writer.writerow(['user: %s'%user, 'vole: %s'%vole, 'date: %s'%date, 'experiment: %s'%exp, 'Day: %i'%day])
        writer.writerow(['Round, Event', 'Time'])

    return path
def setup_pins():
    '''here we get the gpio pins setup, and instantiate pigpio object.'''
    #setup our pins. Lever pins are input, all else are output
    GPIO.setmode(GPIO.BCM)


    for k in pins.keys():
        print(k)
        if 'lever' in k:
            print(k + ": IN")
            GPIO.setup(pins[k], GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
        elif 'read' in k:
            print(k + ": IN")
            GPIO.setup(pins[k], GPIO.IN, pull_up_down=GPIO.PUD_UP)
        elif 'led' in k or 'dispence' in k :
            GPIO.setup(pins[k], GPIO.OUT)
            GPIO.output(pins[k], 0)
            print(k + ": OUT")
        else:
            GPIO.setup(pins[k], GPIO.OUT)
            print(k + ": OUT")

def run_job(job, q, args = None):
    print('job: ' + str(job) + '    args: ' +str(args))

    '''parse and run jobs'''

    jobs = {'extend lever':extend_lever,
            'dispence pellet':dispence_pellet,
            'retract lever':retract_lever,
            'start tone':experiment_start_tone,
            'pellet tone':pellet_tone,
            'monitor lever':monitor_lever,
            'dispense pellet':dispence_pellet,
            'read pellet':read_pellet
            }

    if args:
        jobs[job](q, args)
    else:
        jobs[job](q)

def monitor_lever(ds_queue, args):
    global monitor
    global start_time
    global interrupt
    global round

    monitor = True
    lever_q, lever_ID = args
    "monitor a lever. If lever pressed, put lever_ID in queue. "
    lever=0

    ds_queue.task_done()
    while monitor:
        if GPIO.input(pins["lever_%s"%lever_ID]):
            lever +=1

        #just guessing on this value, should probably check somehow empirically
        if lever > 2:
            if not interrupt:
                #send the lever_ID to the lever_q to trigger a  do_stuff.put in
                #the main thread/loop
                lever_q.put(lever_ID)
                timestamp_queue.put('%i, %s lever pressed productive, %f'%(round, lever_ID, time.time()-start_time))
                while GPIO.input(pins["lever_%s"%lever_ID]):
                    'hanging till lever not pressed'
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

def extend_lever(q, args):
    global start_time
    global servo_dict
    global round

    lever_ID, retract, extend = args
    print('extending lever %s'%lever_ID)
    print('LEDs on')
    servo_dict[lever_ID].angle = extend
    GPIO.output(pins['led_%s'%lever_ID], 1)
    timestamp_queue.put('%i, Levers out, %f'%(round, time.time()-start_time))
    q.task_done()

def retract_lever(q, args):
    global start_time
    global servo_dict
    global round

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

def pellet_tone(q):
    global start_time
    global round

    print('starting pellet tone')
    pi.set_PWM_dutycycle(pins['pellet_tone'], 255/2)
    pi.set_PWM_frequency(pins['pellet_tone'], 2000)

    timestamp_queue.put('%i, pellet tone start, %f'%(round, time.time()-start_time))
    time.sleep(2)
    pi.set_PWM_dutycycle(pins['pellet_tone'], 0)

    print('pellet tone complete')
    timestamp_queue.put('%i, pellet tone complete, %f'%(round, time.time()-start_time))
    q.task_done()

def experiment_start_tone(q):
    global start_time
    print('starting experiment tone')
    pi.set_PWM_dutycycle(pins['pellet_tone'], 255/2)
    pi.set_PWM_frequency(pins['pellet_tone'], 3000)
    timestamp_queue.put('%i, experiment start tone start, %f'%(round, time.time()-start_time))
    time.sleep(2)
    pi.set_PWM_dutycycle(pins['pellet_tone'], 0)
    print('experiment tone complete')
    timestamp_queue.put('%i, experiment start tone start complete, %f'%(round, time.time()-start_time))
    q.task_done()

def dispence_pellet(q):
    global start_time
    q.task_done()
    timeout = time.time()
    global pellet_state
    global round

    read = 0

    #only dispense if there is no pellet, otherwise skip
    if not pellet_state:
        print('%i, starting pellet dispensing %f'%(round, time.time()-start_time))

        #we're just gonna turn the servo on and keep monitoring. probably
        #want this to be a little slow

        servo_dict['dispense_pellet'].throttle = continuous_servo_speeds['dispense_pellet']['forward']

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


def breakpoint_monitor_lever(ds_queue, args):
    '''this lever monitor function tracks presses and returns when breakpoint reached'''

    global monitor
    global start_time
    global interrupt
    global round

    monitor = True
    lever_q, lever_ID= args
    "monitor a lever. If lever pressed, put lever_ID in queue. "
    lever=0
    do_stuff_queue.put(('extend lever',
                        ('social',lever_angles['social'][0],lever_angles['social'][1])))

    ds_queue.task_done()
    while monitor:
        if GPIO.input(pins["lever_%s"%lever_ID]):
            lever +=1

        #just guessing on this value, should probably check somehow empirically
        if lever > 2:

            #send the lever_ID to the lever_q to trigger a  do_stuff.put in
            #the main thread/loop

            timestamp_queue.put('%i, %s lever pressed, %f'%(round, lever_ID, time.time()-start_time))


            do_stuff_queue.put(('retract lever',
                                ('social', lever_angles['social'][0],lever_angles['social'][1])))

            lever_q.put(lever_ID)
            lever = 0
            monitor = False
            break

        time.sleep(25/1000.0)
    print('\nmonitor thread done')

def cleanup(q):
    '''cleanup all servos etc'''
    servo_dict['food'].angle = lever_angles['food'][0]
    servo_dict['social'].angle = lever_angles['social'][0]
    servo_dict['door'].throttle = continuous_servo_speeds['door']['stop']
    servo_dict['dispense_pellet'].throttle = continuous_servo_speeds['dispense_pellet']['stop']
    q.task_done()

def read_pellet(q):
    global start_time
    global pellet_state
    global round

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
            print('Pellet taken! %f'%(time.time()-start_time))
            timestamp_queue.put('%i, Pellet retrieved, %f'%(round, time.time()-start_time))

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

def flush_to_CSV(path):
        '''a good time to write some stuff to file'''
        with open(path, 'a') as csv_file:
            csv_writer = csv.writer(csv_file)
            while time.time() - round_start < round_time:
                if not timestamp_queue.empty():
                    line = timestamp_queue.get().split(',')
                    print('writing ###### %s'%line)
                    csv_writer.writerow(line)
                time.sleep(0.01)
