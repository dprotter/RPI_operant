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


class runtime_functions:
    
    def __init__(self):
        self.pi = pigpio.pi()
        
        #our queues for doign stuff and saving stuff
        self.do_stuff_queue = queue.Queue()
        self.timestamp_queue = queue.Queue()
        self.lever_press_queue = queue.Queue()


        self.user = None
        self.this_path = ''

        self.done = False

        self.round = 0

        self.start_time = None

        #in case we need to interrupt after a lever press.
        self.interrupt = False

        #whether or not to monitor levers.
        self.monitor = False

        #is there a pellet currently in the trough?
        self.pellet_state = False

        #are we overriding the door activity?
        self.door_override = {'door_1':False, 'door_2':False}

        #true = closed, false = open
        self.door_states = {'door_1':False, 'door_2':False}

        #timeout for closing the doors
        self.door_close_timeout = 10



    def start_timing(self):
        self.start_time = time.time()


    def setup_experiment(self, args_dict):


        if args_dict['user']=='':
            while no_user:
                self.user = input('no user listed. who is doing this experiment? \n')

                check = input('ok, double check its %s ? (y/n) \n'%self.user)
                if check.lower() in ['y', 'yes']:
                    no_user = False
        else:
            self.user = args_dict['user']

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

        fname = fdate+f'_{exp}_vole_{vole}.csv'
        self.this_path = os.path.join(save_dir, fname)



        print('Path is: ')
        print(self.this_path)
        with open(self.this_path, 'w') as file:
            writer = csv.writer(file, delimiter = ',')
            
            
            
            writer.writerow(['user: %s'%self.user, 'vole: %s'%vole, 'date: %s'%date,
            'experiment: %s'%exp, 'Day: %i'%day, 'Pi: %s'%socket.gethostname()])

            settings_string = ''
            for key in args_dict.keys():
                settings_string+=f'{key}:{args_dict[key]}|'
            writer.writerow([settings_string,])
            
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

    def setup_pins(self):
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

    def close_doors(self):
        print('resetting door states')
        reset_doors()
        open_doors = [id for id in ['door_1', 'door_2'] if not self.door_states[id]]
        if len(open_doors) > 0 :
            print(f'oh dip! theres a problem closing the doors: {open_doors}')
            raise
        
    def reset_doors(self):

        #check if the doors are closed
        if not GPIO.input(pins['door_1_state_switch']):
            self.door_states['door_1'] = True

        if not GPIO.input(pins['door_2_state_switch']):
            self.door_states['door_2'] = True

        #get the open doors (door_state == False)
        open_doors = [id for id in ['door_1', 'door_2'] if not self.door_states[id]]

        for door_ID in open_doors:
            start = time.time()


            while not self.door_states[door_ID] and time.time()-start < self.door_close_timeout:
                    if not self.door_override[door_ID]:
                        servo_dict[door_ID].throttle = continuous_servo_speeds[door_ID]['close']

                    #we will close the door until pins for door close are raised, or until timeout
                    if not GPIO.input(pins[f'{door_ID}_state_switch']):
                        self.door_states[door_ID] = True
                        servo_dict[door_ID].throttle = continuous_servo_speeds[door_ID]['stop']

            if not self.door_states[door_ID]:
                print(f'ah crap, door {door_ID} didnt close!')



    def open_door(self, args):
        '''open a door!'''
        door_ID = args

        #double check the right number of args got passed
        if type(door_ID) is tuple:
            if len(door_ID) == 1:
                door_ID = door_ID[0]
            else:
                print(f'yo! you passed close_door() too many arguments! should get 1 (the door_ID), got {len(door_ID)}')
                raise

        self.timestamp_queue.put('%i, %s open begin, %f'%(self.round, door_ID, time.time()-self.start_time))
        servo_dict[door_ID].throttle = continuous_servo_speeds[door_ID]['open']
        open_time = continuous_servo_speeds[door_ID]['open time']
        start = time.time()

        while time.time() < ( start + open_time ) and not self.door_override[door_ID]:
            #wait for the door to open
            time.sleep(0.05)

        #door should be open!
        servo_dict[door_ID].throttle = continuous_servo_speeds[door_ID]['stop']

        print('exiting door open attempts')

        
        if not GPIO.input(pins[f'{door_ID}_state_switch']):
            if self.door_override[door_ID]:
                print(f'open {door_ID} stopped due to override!')
            print(f'{door_ID} failed to open!!!')
            self.timestamp_queue.put('%i, %s open failure, %f'%(self.round, door_ID, time.time()-self.start_time))
        else:
            self.timestamp_queue.put('%i, %s open finish, %f'%(self.round, door_ID, time.time()-self.start_time))
            self.door_states[door_ID] = False
        self.do_stuff_queue.task_done()



    def close_door(self, args):
        
        door_ID= args

        #double check the right number of args got passed
        if type(door_ID) is tuple:
            if len(door_ID) == 1:
                door_ID = door_ID[0]
            else:
                print(f'yo! you passed close_door() too many arguments! should get 1 (the door_ID), got {len(door_ID)}')
                raise

        self.timestamp_queue.put('%i, %s close begin, %f'%(self.round, door_ID, time.time()-self.start_time))

        start = time.time()

        #if its the first time the door has been overriden, we will open again slightly.
        first_override = True
        while not self.door_states[door_ID] and time.time()-start < self.door_close_timeout:
                if not self.door_override[door_ID]:
                    servo_dict[door_ID].throttle = continuous_servo_speeds[door_ID]['close']

                #we will close the door until pins for door close are raised, or until timeout
                if not GPIO.input(pins[f'{door_ID}_state_switch']):
                    self.door_states[door_ID] = True
                    servo_dict[door_ID].throttle = continuous_servo_speeds[door_ID]['stop']
                elif self.door_override[door_ID] and first_override:
                    servo_dict[door_ID].throttle = continuous_servo_speeds[door_ID]['open']
                    time.sleep(0.1)
                    servo_dict[door_ID].throttle = continuous_servo_speeds[door_ID]['stop']

        if not self.door_states[door_ID]:
            print(f'ah crap, door {door_ID} didnt close!')

        self.do_stuff_queue.task_done()


    #### run in a dedicated thread so we can open the doors whenever necessary
    def override_door_1(self):
        

        while True:
            if not GPIO.input(pins['door_1_override_open_switch']):
                self.door_override['door_1'] = True
                servo_dict['door_1'].throttle = continuous_servo_speeds['door_1']['open']
                while not GPIO.input(pins['door_1_override_open_switch']):
                    time.sleep(0.05)
                servo_dict['door_1'].throttle = continuous_servo_speeds['door_1']['stop']
            if not GPIO.input(pins['door_1_override_close_switch']):
                self.door_override['door_1'] = True
                servo_dict['door_1'].throttle = continuous_servo_speeds['door_1']['close_full']
                while not GPIO.input(pins[f'door_1_override_close_switch']):
                    time.sleep(0.05)
                servo_dict['door_1'].throttle = continuous_servo_speeds['door_1']['stop']
            self.door_override['door_1'] = False


            time.sleep(0.1)

    #### run in a dedicated thread so we can open the doors whenever necessary
    def override_door_2(self):
        

        while True:
            if not GPIO.input(pins['door_2_override_open_switch']):
                self.door_override['door_2'] = True
                servo_dict['door_2'].throttle = continuous_servo_speeds['door_2']['open']
                while not GPIO.input(pins['door_2_override_open_switch']):
                    time.sleep(0.05)
                servo_dict['door_2'].throttle = continuous_servo_speeds['door_2']['stop']
            if not GPIO.input(pins['door_2_override_close_switch']):
                self.door_override['door_2'] = True
                servo_dict['door_2'].throttle = continuous_servo_speeds['door_2']['close_full']
                while not GPIO.input(pins['door_2_override_close_switch']):
                    time.sleep(0.05)
                servo_dict['door_2'].throttle = continuous_servo_speeds['door_2']['stop']
            self.door_override['door_2'] = False


            time.sleep(0.1)


    def run_job(self, job,args = None):
        print('job: ' + str(job) + '    args: ' +str(args))

        '''parse and run jobs'''

        jobs = {'extend lever':self.extend_lever,
                'dispense pellet':self.dispense_pellet,
                'retract lever':self.retract_lever,
                'buzz':self.buzz,
                'monitor lever':self.monitor_lever,
                'monitor_lever_test':self.monitor_lever_test,
                'dispense pellet':self.dispense_pellet,
                'read pellet':self.read_pellet,
                'close door':self.close_door,
                'open door':self.open_door,
                'door override 1':self.override_door_1,
                'door override 2':self.override_door_2,
                'clean up':self.clean_up,

                }

        if args:
            jobs[job](args)
        else:
            jobs[job]()


    def thread_distributor(self):
        '''this is main thread's job. To look for shit to do and send it to a thread'''
        while True:
            if not self.do_stuff_queue.empty():
                do = self.do_stuff_queue.get()
                name = do[0]
                args = None
                if len(do) >1:
                    args = do[1]

                self.run_job(name, args)
                time.sleep(0.05)
            time.sleep(0.05)


    def monitor_lever_test(self, args):

        self.do_stuff_queue.task_done()
        
        self.monitor = True
        lever_ID = args
        "monitor a lever. If lever pressed, put lever_ID in queue. "
        lever=0
        
        while self.monitor:
            if not GPIO.input(pins["lever_%s"%lever_ID]):
                lever +=1

            #just guessing on this value, should probably check somehow empirically
            if lever > 2:
                if not self.interrupt:
                    #send the lever_ID to the lever_q to trigger a  do_stuff.put in
                    #the main thread/loop

                    self.lever_press_queue.put(lever_ID)

                    self.timestamp_queue.put('%i, %s lever pressed productive, %f'%(self.round, lever_ID, time.time()-self.start_time))
                    print(f'{lever_ID} pressed! neato.')
                    while not GPIO.input(pins["lever_%s"%lever_ID]):
                        'hanging till lever not pressed'
                        time.sleep(0.05)
                    lever = 0
                else:
                    #we can still record from the lever until monitoring is turned
                    #off. note that this wont place anything in the lever_press queue,
                    #as that is just to tell the main thread the vole did something
                    self.timestamp_queue.put('%i, %s lever pressed, %f'%(self.round, lever_ID, time.time()-self.start_time))
                    while GPIO.input(pins["lever_%s"%lever_ID]):
                        'hanging till lever not pressed'
                    lever = 0

            time.sleep(25/1000.0)
        print('halting monitoring of %s lever'%lever_ID)



    def monitor_lever(self, args):

        self.do_stuff_queue.task_done()
        
        self.monitor = True
        lever_ID = args
        "monitor a lever. If lever pressed, put lever_ID in queue. "
        lever=0

        
        while self.monitor:
            if not GPIO.input(pins["lever_%s"%lever_ID]):
                lever +=1

            #just guessing on this value, should probably check somehow empirically
            if lever > 2:
                if not self.interrupt:
                    #send the lever_ID to the lever_q to trigger a  do_stuff.put in
                    #the main thread/loop

                    self.lever_press_queue.put(lever_ID)

                    self.timestamp_queue.put('%i, %s lever pressed productive, %f'%(self.round, lever_ID, time.time()-self.start_time))
                    while not GPIO.input(pins["lever_%s"%lever_ID]):
                        'hanging till lever not pressed'
                        time.sleep(0.05)
                    lever = 0
                else:
                    #we can still record from the lever until monitoring is turned
                    #off. note that this wont place anything in the lever_press queue,
                    #as that is just to tell the main thread the vole did something
                    self.timestamp_queue.put('%i, %s lever pressed, %f'%(self.round, lever_ID, time.time()-self.start_time))
                    while not GPIO.input(pins["lever_%s"%lever_ID]):
                        'hanging till lever not pressed'
                        time.sleep(0.05)
                    lever = 0

            time.sleep(25/1000.0)
        print('halting monitoring of %s lever'%lever_ID)

    def extend_lever(self, args):

        lever_ID = args

        #double check the right number of args got passed
        if type(lever_ID) is tuple:
            if len(lever_ID) == 1:
                lever_ID = lever_ID[0]
            else:
                print(f'yo! you passed extend_lever() too many arguments! should get 1 (the lever_ID), got {args}')
                raise

        #get extention and retraction angles from the operant_cage_settings
        extend = lever_angles[lever_ID][0]
        retract = lever_angles[lever_ID][1]

        #we will wiggle the lever a bit to try and reduce binding and buzzing
        modifier = 15
        
        if extend > retract:
            retract_start = retract - modifier
            extend_start = extend + modifier
        else:
            retract_start = retract + modifier
            extend_start = extend - modifier

        print(f'extending lever {lever_ID}: extend[ {extend} ], retract[ {retract} ]')
        servo_dict[f'lever_{lever_ID}'].angle = extend_start
        self.timestamp_queue.put('%i, Levers out, %f'%(self.round, time.time()-self.start_time))
        time.sleep(0.1)
        servo_dict[f'lever_{lever_ID}'].angle = extend
        
        
        self.do_stuff_queue.task_done()

    def retract_lever(self, args):

        lever_ID = args
        timeout = 5
        #double check the right number of args got passed
        if type(lever_ID) is tuple:
            if len(lever_ID) == 1:
                lever_ID = lever_ID[0]
            else:
                print(f'yo! you passed extend_lever() too many arguments! should get 1 (the lever_ID), got {args}')
                raise

        #get extention and retraction angles from the operant_cage_settings
        extend = lever_angles[lever_ID][0]
        retract = lever_angles[lever_ID][1]

        #we will wiggle the lever a bit to try and reduce binding and buzzing
        modifier = 15
        
        if extend > retract:
            retract_start = retract - modifier
            extend_start = extend + modifier
        else:
            retract_start = retract + modifier
            extend_start = extend - modifier
            
        start = time.time()
        while not GPIO.input(pins[f'lever_{lever_ID}']) and time.time()-start < timeout:
            'hanging till lever not pressed'
            time.sleep(0.05)
            
        servo_dict[f'lever_{lever_ID}'].angle = retract
        self.timestamp_queue.put('%i, Levers retracted, %f'%(self.round, time.time()-self.start_time))
        self.do_stuff_queue.task_done()

    def buzz(self, args):
        '''take time (s), hz, and name as inputs'''

        buzz_len, hz, name = args

        print(f'starting {name} tone {hz} hz')

        #set a 50% duty cycle, pass desired hz
        self.pi.set_PWM_dutycycle(pins['speaker_tone'], 255/2)
        self.pi.set_PWM_frequency(pins['speaker_tone'], int(hz))

        self.timestamp_queue.put(f'{self.round}, {name} tone start {hz}:hz {buzz_len}:seconds, {time.time()-self.start_time}')

        time.sleep(buzz_len)

        #sound off
        self.pi.set_PWM_dutycycle(pins['speaker_tone'], 0)

        print(f'{name} tone complete')
        self.timestamp_queue.put(f'{self.round}, {name} tone complete {hz}:hz {buzz_len}:seconds, {time.time()-self.start_time}')
        self.do_stuff_queue.task_done()

    def door_close_tone(self):
        '''can replace with buzz()'''
        self.do_stuff_queue.task_done()

    def dispense_pellet(self):

        

        self.do_stuff_queue.task_done()
        timeout = time.time()


        read = 0

        #only dispense if there is no pellet, otherwise skip
        if not self.pellet_state:
            print('%i, starting pellet dispensing %f'%(self.round, time.time()-self.start_time))

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
                    self.timestamp_queue.put('%i, Pellet dispensed, %f'%(self.round, time.time()-self.start_time))
                    print('Pellet dispensed, %f'%(time.time()-self.start_time))

                    #now there is a pellet!
                    self.pellet_state = True

                    #offload monitoring to a new thread
                    self.do_stuff_queue.put(('read pellet',))
                    return ''

                else:
                    #wait to give other threads time to do stuff, but fast enough
                    #that we check pretty quick if there's a pellet
                    time.sleep(0.025)
            servo_dict['dispense_pellet'].throttle = continuous_servo_speeds['dispense_pellet']['stop']
            self.timestamp_queue.put(f'{self.round}, Pellet dispense failure, {time.time()-self.start_time}')
            return ''
        else:
            print("skipping pellet dispense due to pellet not retrieved")
            self.timestamp_queue.put(f'{self.round}, skip pellet dispense, {time.time()-self.start_time}')
            return ''

    def pulse_sync_line(self, length):
        '''not terribly accurate, but good enough. For now, this is called on every
        lever press or pellet retrieval. Takes length in seconds'''
        GPIO.output(pins['gpio_sync'], 1)
        time.sleep(length)
        GPIO.output(pins['gpio_sync'], 0)

    def clean_up(self):

        
        '''cleanup all servos etc'''
        servo_dict['lever_food'].angle = lever_angles['food'][1]
        servo_dict['lever_door_1'].angle = lever_angles['door_1'][1]
        servo_dict['lever_door_2'].angle = lever_angles['door_2'][1]
        servo_dict['door_1'].throttle = continuous_servo_speeds['door_1']['stop']
        servo_dict['door_2'].throttle = continuous_servo_speeds['door_2']['stop']
        servo_dict['dispense_pellet'].throttle = continuous_servo_speeds['dispense_pellet']['stop']
        self.done = True
        self.do_stuff_queue.task_done()

    def breakpoint_monitor_lever(self, args):
        '''this lever monitor function tracks presses and returns when breakpoint reached'''
        
        self.monitor = True
        lever_q, lever_ID= args
        "monitor a lever. If lever pressed, put lever_ID in queue. "
        lever=0
        self.do_stuff_queue.put(('extend lever',
                            (lever_ID)))

        self.do_stuff_queue.task_done()
        while self.monitor:
            if not GPIO.input(pins["lever_%s"%lever_ID]):
                lever +=1

            #just guessing on this value, should probably check somehow empirically
            if lever > 2:

                #send the lever_ID to the lever_q to trigger a  do_stuff.put in
                #the main thread/loop
                
                self.timestamp_queue.put('%i, %s lever pressed, %f'%(self.round, lever_ID, time.time()-self.start_time))


                self.do_stuff_queue.put(('retract lever',
                                    (lever_ID)))

                self.lever_press_queue.put(lever_ID)
                lever = 0
                self.monitor = False
                break

            time.sleep(25/1000.0)
        print('\nmonitor thread done')

    def read_pellet(self):
        

        disp_start = time.time()
        self.do_stuff_queue.task_done()
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
                self.pulse_sync_line(0.05)
                self.timestamp_queue.put(f'{self.round}, pellet retrieved,{time.time()-self.start_time}')
                print('Pellet taken! %f'%(time.time()-self.start_time))
                #no pellet in trough
                self.pellet_state = False
                return ''

            if read_disp > 3:
                read_retr = 0
                read_disp = 0

            time.sleep(0.05)


        self.timestamp_queue.put('%i, pellet retreival timeout, %f'%(self.round, time.time()-self.self.start_time))
        return ''


    def flush_to_CSV(self):
            '''a good time to write some stuff to file'''
            print('heres the path for the flush func\n%s'%self.this_path)


            while not self.done or not self.timestamp_queue.empty():
                if not self.timestamp_queue.empty():
                    with open(self.this_path, 'a') as csv_file:
                        csv_writer = csv.writer(csv_file, delimiter = ',')
                        while not self.timestamp_queue.empty():
                            line = self.timestamp_queue.get().split(',')
                            print('writing ###### %s'%line)
                            csv_writer.writerow(line)
                            time.sleep(0.005)
                time.sleep(0.01)
