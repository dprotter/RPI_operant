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
from operant_cage_settings import pins, servo_dict, continuous_servo_speeds

round_time = 120
pellet_tone_time = 2 #how long the pellet tone plays
timeII = 30 #time after levers out before pellet
timeIV = 0 #time after pellet delivered before levers retracted
loops = 15



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
    writer.writerow(['user: %s'%user, 'vole: %s'%vole, 'date: %s'%date, 'Experiment: Autoshape'])
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
    elif 'led' in k or 'dispence' in k or 'tone' in k:
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
                timestamp_queue.put('%s lever pressed with interrupt, %f'%(lever_ID, time.time()-start_time))
                while GPIO.input(pins["lever_%s"%lever_ID]):
                    'hanging till lever not pressed'
                lever = 0
            else:
                #we can still record from the lever until monitoring is turned
                #off. note that this wont place anything in the lever_press queue,
                #as that is just to tell the main thread the vole did something
                timestamp_queue.put('%s lever pressed, %f'%(lever_ID, time.time()-start_time))
                while GPIO.input(pins["lever_%s"%lever_ID]):
                    'hanging till lever not pressed'
                lever = 0

        time.sleep(25/1000.0)
    print('halting monitoring of %s lever'%lever_ID)

def extend_lever(q, args):
    global start_time
    global servo_dict
    lever_ID, retract, extend = args
    print('extending lever %s'%lever_ID)
    print('LEDs on')
    servo_dict[lever_ID].angle = extend
    GPIO.output(pins['led_%s'%lever_ID], 1)
    timestamp_queue.put('Levers out, %f'%(time.time()-start_time))
    q.task_done()

def retract_lever(q, args):
    global start_time
    global servo_dict
    lever_ID, retract, extend = args

    while GPIO.input(pins["lever_%s"%lever_ID]):
        'hanging till lever not pressed'
        time.sleep(0.05)

    GPIO.output(pins['led_%s'%lever_ID], 0)
    servo_dict[lever_ID].angle = retract
    timestamp_queue.put('Levers retracted, %f'%(time.time()-start_time))
    q.task_done()

def pellet_tone(q):
    global start_time
    print('starting pellet tone')
    GPIO.output(pins['pellet_tone'], 1)
    timestamp_queue.put('pellet tone start, %f'%(time.time()-start_time))
    time.sleep(2)
    GPIO.output(pins['pellet_tone'], 0)
    print('pellet tone complete')
    timestamp_queue.put('pellet tone complete, %f'%(time.time()-start_time))
    q.task_done()


def dispence_pellet(q):
    global start_time
    q.task_done()
    timeout = time.time()
    global pellet_state

    read = 0

    #only dispense if there is no pellet, otherwise skip
    if not pellet_state:
        print('starting pellet dispensing %f'%(time.time()-start_time))

        #we're just gonna turn the servo on and keep monitoring. probably
        #want this to be a little slow

        servo_dict['dispense_pellet'].throttle = forward

        #set a timeout on dispensing. with this, that will be a bit less than
        #6 attempts to disp, but does give the vole 2 sec in which they could nose
        #poke and trigger this as "dispensed"
        while time.time()-timeout < 3:

            if not GPIO.input(pins['read_pellet']):
                print('blocked')
                read +=1

            if read > 2:
                servo_dict['dispense_pellet'].throttle = stop
                timestamp_queue.put('Pellet dispensed, %f'%(time.time()-start_time))
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
        servo_dict['dispense_pellet'].throttle = stop
        timestamp_queue.put('Pellet dispense failure, %f'%(time.time()-start_time))
        return ''
    else:
        print("skipping pellet dispense due to pellet not retrieved")
        timestamp_queue.put('skip pellet dispense, %f'%(time.time()-start_time))
        return ''

def read_pellet(q):
    global start_time
    global pellet_state

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
            timestamp_queue.put('Pellet retrieved, %f'%(time.time()-start_time))

            #no pellet in trough
            pellet_state = False
            return ''

        if read_disp > 3:
            read_retr = 0
            read_disp = 0

        time.sleep(0.05)


    timestamp_queue.put('pellet retreival timeout, %f'%(time.time()-start_time))
    return ''




def experiment_start_tone(q):
    global start_time
    print('starting experiment tone')
    GPIO.output(pins['start_tone'], 1)
    timestamp_queue.put('experiment start tone start, %f'%(time.time()-start_time))

    for i in range(10):
        time.sleep(0.05)
        GPIO.output(pins['start_tone'], 1)
        time.sleep(0.1)
        GPIO.output(pins['start_tone'], 0)
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


for x in range(8):
    t = threading.Thread(target = thread_distributor)
    t.daemon = True
    t.start()
    print("started %i"%x )


### master looper ###
for i in range(loops):
    round_start = time.time()
    print("#-#-#-#-#-# new round #%i!!!-#-#-#-#-#"%i)
    timestamp_queue.put('Starting new round, %f'%(time.time()-start_time))
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
        if not interrupt and not lever_press_queue.empty():
            interrupt = True
            lever_ID = lever_press_queue.get()
            print('the %s lever was pressed! woweeeee'%lever_ID)
            timestamp_queue.put('a lever was pressed! woweeeee, %f'%(time.time()-start_time))
            do_stuff_queue.put(('pellet tone',))
            do_stuff_queue.put(('dispence pellet',))

            #wait 0.5 seconds for the vole to move before retracting lever
            time.sleep(0.5)
            do_stuff_queue.put(('retract lever',
                                ('food', lever_angles['food'][0],lever_angles['food'][1])))
            do_stuff_queue.join()
        time.sleep(0.05)

    #waited the interval for timeII, nothing happened
    if not interrupt:
        print('the vole is dumb and didnt press a lever')
        do_stuff_queue.put(('pellet tone',))
        do_stuff_queue.put(('dispence pellet',))
        do_stuff_queue.put(('retract lever',
                            ('food', lever_angles['food'][0],lever_angles['food'][1])))
        do_stuff_queue.join()

    time.sleep(0.05)



    time.sleep(timeIV)
    print('entering ITI')

    #wait for ITI to pass

    '''a good time to write some stuff to file'''
    with open(path, 'a') as csv_file:
        csv_writer = csv.writer(csv_file)
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

'''append current timestamp queue contents to csv file'''
with open(path, 'a') as file:
    writer = csv.writer(file, delimiter = ',')
    while not timestamp_queue.empty():
        line = timestamp_queue.get().split(',')
        print('writing ###### %s'%line)
        writer.writerow(line)

print("all Done")
#reset levers to retracted
kit.servo[0].angle = lever_angles['food'][0]
kit.continuous_servo[1].throttle = stop



if 'y' in push.lower():
    email_push.email_push(user = user)
