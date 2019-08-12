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
import email_push
import datetime
from operant_cage_settings import pins, servo_dict, continuous_servo_speeds, lever_angles
import pigpio
import sys
#activates the pigpio daemon that runs PWM, unless its already running
if os.system('sudo lsof -i TCP:8888'):
    os.system('sudo pigpiod')


round_time = 120
door_close_tone_time = 2 #how long the door tone plays
timeII = 30 #time after levers out before door opens
timeIV = 0 #time after pellet delivered before levers retracted
loops = 15

move_animal_time = 20 #how long to give maya to move the animal (with some wiggle room)
time_after_move = 15 #how long we want to wait before the next test period. Sometimes
                    #the move animal time may bleed into this a bit



"""the following sets up the output file and gets some user input. """

save_dir = '/home/pi/Operant_Output/'
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

day = input('Which door-shaping training day is this? \n')
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
    writer.writerow(['user: %s'%user, 'vole: %s'%vole, 'date: %s'%date, 'Experiment: Door Shaping', 'Day: %i'%day])
    writer.writerow(['Event', 'Time'])




##### double check which servo is which. I'm writing this as:
##### kit[0] = food lever
##### kit[1] = partner lever
##### kit[2] = door
##### kit[3] = food dispenser


servo_dict['dispense_pellet'].throttle = continuous_servo_speeds['dispense_pellet']['stop']
servo_dict['door'].throttle = continuous_servo_speeds['door']['stop']
servo_dict['food'].angle = lever_angles['food'][0]
servo_dict['social'].angle = lever_angles['social'][0]

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
    elif 'led' in k or 'dispense' in k:
        GPIO.setup(pins[k], GPIO.OUT)
        GPIO.output(pins[k], 0)
        print(k + ": OUT")
    else:
        GPIO.setup(pins[k], GPIO.OUT)
        print(k + ": OUT")


#our queues for doign stuff and saving stuff
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

global pellet_state
pellet_state = False

global door_override
door_override = False

global round
round = 0

def run_job(job, q, args = None):
    print('job: ' + str(job) + '    args: ' +str(args))

    '''parse and run jobs'''

    jobs = {'extend lever':extend_lever,
            'dispense pellet':dispense_pellet,
            'retract lever':retract_lever,
            'start tone':experiment_start_tone,
            'pellet tone':pellet_tone,
            'monitor lever':monitor_lever,
            'dispense pellet':dispense_pellet,
            'read pellet':read_pellet,
            'close door':close_door,
            'open door':open_door,
            'door close tone': door_close_tone,
            'door override':override_door
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
                    time.sleep(0.05)
                lever = 0
            else:
                #we can still record from the lever until monitoring is turned
                #off. note that this wont place anything in the lever_press queue,
                #as that is just to tell the main thread the vole did something
                timestamp_queue.put('%i, %s lever pressed, %f'%(round, lever_ID, time.time()-start_time))
                while GPIO.input(pins["lever_%s"%lever_ID]):
                    'hanging till lever not pressed'
                    time.sleep(0.05)
                lever = 0

        time.sleep(25/1000.0)
    print('halting monitoring of %s lever'%lever_ID)

def extend_lever(q, args):
    global start_time
    global servo_dict
    global round

    lever_ID, retract, extend = args

    servo_dict[lever_ID].angle = extend
    GPIO.output(pins['led_%s'%lever_ID], 1)
    timestamp_queue.put('%i, Levers out, %f'%(round, time.time()-start_time))
    q.task_done()

def override_door(q):
    global start_time
    global door_override
    q.task_done()
    while True:
        if GPIO.input(pins['lever_door_override_open']):
            door_override = True
            servo_dict['door'].throttle = continuous_servo_speeds['door']['open']
            while GPIO.input(pins['lever_door_override_open']):
                time.sleep(0.05)
            servo_dict['door'].throttle = continuous_servo_speeds['door']['stop']
        if GPIO.input(pins['lever_door_override_close']):
            door_override = True
            servo_dict['door'].throttle = continuous_servo_speeds['door']['close_full']
            while GPIO.input(pins['lever_door_override_close']):
                time.sleep(0.05)
            servo_dict['door'].throttle = continuous_servo_speeds['door']['stop']
        door_override = False
        time.sleep(0.1)


def open_door(q):
    global start_time
    global servo_dict
    global round
    timestamp_queue.put('%i, Door open begin, %f'%(round, time.time()-start_time))
    servo_dict['door'].throttle = continuous_servo_speeds['door']['open']
    time.sleep(continuous_servo_speeds['door']['open time'])
    servo_dict['door'].throttle = continuous_servo_speeds['door']['stop']
    timestamp_queue.put('%i, Door open finish, %f'%(round, time.time()-start_time))
    q.task_done()

def close_door(q):
    global start_time
    global servo_dict
    global door_override
    global round

    timestamp_queue.put('%i, Door close begin, %f'%(round, time.time()-start_time))
    if not door_override:
        start = time.time()
        servo_dict['door'].throttle = continuous_servo_speeds['door']['close']
        while time.time()-start < continuous_servo_speeds['door']['close time'] and not door_override:
            '''just hanging around'''
            time.sleep(0.05)
        if not door_override:
            servo_dict['door'].throttle = continuous_servo_speeds['door']['stop']

    q.task_done()

def retract_lever(q, args):
    global start_time
    global servo_dict
    global round
    lever_ID, retract, extend = args

    while GPIO.input(pins["lever_%s"%lever_ID]):
        'hanging till lever not pressed'
        time.sleep(0.05)

    GPIO.output(pins['led_%s'%lever_ID], 0)
    servo_dict[lever_ID].angle = retract
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

def door_close_tone(q):
    global start_time
    print('starting door close tone')

    pi.set_PWM_frequency(pins['pellet_tone'], 3500)
    for i in range(5):
        pi.set_PWM_dutycycle(pins['pellet_tone'], 255/2)
        time.sleep(0.5)
        pi.set_PWM_dutycycle(pins['pellet_tone'], 0)
        time.sleep(0.25)
    timestamp_queue.put('%i, door close tone start, %f'%(round, time.time()-start_time))
    time.sleep(2)
    pi.set_PWM_dutycycle(pins['pellet_tone'], 0)
    print('door close tone complete')
    timestamp_queue.put('%i, experiment start tone start complete, %f'%(round, time.time()-start_time))
    q.task_done()

def dispense_pellet(q):
    global start_time
    global round
    global pellet_state

    q.task_done()

    timeout = time.time()
    read = 0

    #only dispense if there is no pellet, otherwise skip
    if not pellet_state:
        print('%i, starting pellet dispensing %f'%(time.time()-start_time))

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
    timeout = 200

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


for x in range(9):
    t = threading.Thread(target = thread_distributor)
    t.daemon = True
    t.start()
    print("started %i"%x )

do_stuff_queue.put(('door override',))


####note that we will add in time after the press, increasing by day up to 3s
delay = [0, 0, 1, 2, 3]

### master looper ###
for i in range(loops):
    round_start = time.time()
    round = i

    print("#-#-#-#-#-# new round #%i!!!-#-#-#-#-#"%i)
    timestamp_queue.put('%i, Starting new round, %f'%(round, time.time()-start_time))
    do_stuff_queue.put(('start tone',))

    #wait till tone is done
    do_stuff_queue.join()


    do_stuff_queue.put(('extend lever',
                        ('social',lever_angles['social'][0],lever_angles['social'][1])))

    #wait till levers are out before we do anything else. Depending on how
    #fast the voles react to the lever, we may start monitoring before it is
    #actually out.
    do_stuff_queue.join()

    #begin tracking the lever in a thread
    do_stuff_queue.put(('monitor lever', (lever_press_queue, 'social',)))

    timeII_start = time.time()

    #for the timeII interval, monitor lever and overide pellet timing if pressed
    while time.time() - timeII_start < timeII:
        #eventually, here we will call threads to monitor
        #vole position and the levers. here its just random
        if not interrupt and not lever_press_queue.empty():
            interrupt = True
            lever_ID = lever_press_queue.get()
            print('the %s lever was pressed! woweeeee'%lever_ID)
            timestamp_queue.put('%i, a lever was pressed! woweeeee, %f'%(round, time.time()-start_time))
            time.sleep(delay[day-1])
            do_stuff_queue.put(('open door',))


            #wait 0.5 seconds for the vole to move before retracting lever
            time.sleep(0.5)
            do_stuff_queue.put(('retract lever',
                                ('social', lever_angles['social'][0],lever_angles['social'][1])))
            do_stuff_queue.join()
        time.sleep(0.05)

    #waited the interval for timeII, nothing happened
    if not interrupt:
        print('the vole is dumb and didnt press a lever')
        timestamp_queue.put('%i, no lever press, %f'%(round, time.time()-start_time))
        do_stuff_queue.put(('open door',))
        do_stuff_queue.put(('retract lever',
                            ('social', lever_angles['social'][0],lever_angles['social'][1])))

        do_stuff_queue.join()

    time.sleep(0.05)


    print('entering ITI for #-#-# round #%i -#-#-# '%i )

    #wait for ITI to pass
    '''a good time to write some stuff to file'''
    with open(path, 'a') as csv_file:
        csv_writer = csv.writer(csv_file)

        #this keeps going through the while loop until ITI finished
        while time.time() - round_start < round_time:
            if not timestamp_queue.empty():
                line = timestamp_queue.get().split(',')
                print('writing ###### %s'%line)
                csv_writer.writerow(line)
            time.sleep(0.01)

    #reset our global values interrupt and monitor. This will turn off the lever
    #if it is still being monitored. This resets the inerrupt value for the next
    #loop of the training.
    interrupt = False
    monitor = False

    #close the door, wait 20s to manually move the vole
    do_stuff_queue.put(('door close tone',))
    time.sleep(1)
    do_stuff_queue.put(('close door',))
    print('time to move that vole over!')

    timestamp_queue.put('%i, start of move animal time, %f'%(round, time.time()-start_time))
    for i in range(move_animal_time):
        sys.stdout.write('\r'+str(move_animal_time - i)+' seconds left  ')
        time.sleep(1)
        sys.stdout.flush()
    print('vole should be moved now')

    time.sleep(time_after_move)




'''append current timestamp queue contents to csv file'''
with open(path, 'a') as file:
    writer = csv.writer(file, delimiter = ',')
    while not timestamp_queue.empty():
        line = timestamp_queue.get().split(',')
        print('writing ###### %s'%line)
        writer.writerow(line)

print("all Done")
#reset levers to retracted
servo_dict['food'].angle = lever_angles['food'][0]
servo_dict['social'].angle = lever_angles['social'][0]
servo_dict['door'].throttle = continuous_servo_speeds['door']['stop']
servo_dict['dispense_pellet'].throttle = continuous_servo_speeds['dispense_pellet']['stop']



if 'y' in push.lower():
    email_push.email_push(user = user)
