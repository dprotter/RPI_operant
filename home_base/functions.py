"""all of the necessary functions for running the operant pi boxes"""

import RPi.GPIO as GPIO
import os
if os.system('sudo lsof -i TCP:8888'):
    os.system('sudo pigpiod')

import sys
sys.path.append('/home/pi/')
from concurrent.futures import ThreadPoolExecutor
import threading
import socket
import time
import datetime
import csv
import numpy as np
import queue
import random
import pigpio
import traceback
import inspect

from RPI_operant.home_base.operant_cage_settings import (kit, pins,
    lever_angles, continuous_servo_speeds,servo_dict)

import RPI_operant.home_base.analysis.analysis_functions as af
import RPI_operant.home_base.analysis.analyze as ana
from RPI_operant.home_base.lookup_classes import Operant_event_strings as oes
from RPI_operant.home_base.bonsai_serial_sender import sender


class lever:
    def __init__(self, lever_ID, rtf_object, inter_press_timeout = 0.5):
        self.name = lever_ID
        self.pin = pins["lever_%s"%lever_ID]
        self.end_monitor = True
        self.lever_presses = queue.Queue()
        self.threads = ThreadPoolExecutor(max_workers=6)
        self.inter_press_timeout = inter_press_timeout
        self.rtf = rtf_object
        self.current_futures = []
        self.presses_reached = False
    
    def delay(self, value):
        time.sleep(value)
        
    def lever_thread_it(func, *args, **kwargs):
        '''simple decorator to pass function to our thread distributor via a queue. 
        these 4 lines took about 4 hours of googling and trial and error.
        the returned 'future' object has some useful features, such as its own task-done monitor. '''
        def pass_to_thread(self, *args, **kwargs):
            future = self.threads.submit(func, *args, **kwargs)
            return future
        return pass_to_thread
    
    def extend(self):
        lever_ID = self.name
        
        #get extention and retraction angles from the operant_cage_settings
        extend = lever_angles[lever_ID][0]
        retract = lever_angles[lever_ID][1]
        
        wiggle = 5
        extend_start = max(0, extend-wiggle)
 
        print(f'\n\n**** extending lever {lever_ID}: extend[ {extend} ], retract[ {retract} ]**** ')
        self.rtf.timestamp_queue.put('%i, Levers out, %f'%(self.rtf.round, time.time()-self.rtf.start_time))
        servo_dict[f'lever_{lever_ID}'].angle = extend_start
        time.sleep(0.05)
        servo_dict[f'lever_{lever_ID}'].angle = extend
        
    def retract(self):
        lever_ID = self.name
        timeout = 2


        #get extention and retraction angles from the operant_cage_settings
        extend = lever_angles[lever_ID][0]
        retract = lever_angles[lever_ID][1]
        
        #slightly wiggle the servo to try and relieve any binding
        wiggle = 10
        retract_start = max(180, retract + wiggle)
        
        start = time.time()
        while not GPIO.input(pins[f'lever_{lever_ID}']) and time.time()-start < timeout:
            'hanging till lever not pressed'
            time.sleep(0.05)
        servo_dict[f'lever_{lever_ID}'].angle = retract_start
        time.sleep(0.05)
        servo_dict[f'lever_{lever_ID}'].angle = retract
        self.rtf.timestamp_queue.put(f'{self.rtf.round}, Lever retracted|{lever_ID}, {time.time()-self.rtf.start_time}')
    
    def wait_for_n_presses(self, number_presses=1, target_functions = None,
                           other_levers = None):
        fut = self._wait_for_n_presses(self, number_presses=number_presses, target_functions = target_functions,
                           other_levers = other_levers)
        return fut

    @lever_thread_it
    def _wait_for_n_presses(self, number_presses, target_functions,
                           other_levers):
        
        '''target functions and args can be lists. 
        functions = list of functions  and arguments, passed with same syntax as if you were running the func itself, preceeded by lambda. ex: [ lambda:fn.buzz(**door_buzz) ]   .
        other levers = list of other lever objects to shut down if this one reaches n presses'''
        
        presses = 0
        self.end_monitor = False
        
        self.current_futures.append(self.threads.submit(self.watch_lever_pin))
        
        while self.end_monitor == False:

            if self.lever_presses.empty() == False:
                while  self.lever_presses.empty() == False and self.end_monitor == False:

                    presses+=1
                    print(f'\n^^^^{self.name} lever at {presses} of {number_presses}\n^^^^^^')
                    
                    if presses < number_presses:

                        self.rtf.timestamp_queue.put('%i, %s lever pressed, %f'%(self.rtf.round, self.name, time.time()-self.rtf.start_time))
                        self.rtf.pulse_sync_line(length = 0.025, event_name = f'{self.name}_lever_pressed')
                        _ = self.lever_presses.get()
                    
                    else:
                        print('\n^^^^^^^^^^^^^^^presses reached^^^^^^^^^^^^^^^^^^')
                        self.end_monitor = True
                        
                        self.rtf.timestamp_queue.put('%i, %s lever pressed productive, %f'%(self.rtf.round, self.name, time.time()-self.rtf.start_time))
                        self.rtf.timestamp_queue.put('%i, %s lever presses reached|%i, %f'%(self.rtf.round, self.name, presses, time.time()-self.rtf.start_time))
                        self.rtf.pulse_sync_line(length = 0.025, event_name = f'{self.name}_lever_pressed_productive')
                        
                        self.presses_reached = True
                        
                        if other_levers:
                            if isinstance(other_levers, list):
                                for lever in other_levers:
                                    lever.end_monitor = True
                            else:
                                other_levers.end_monitor = True

                        if isinstance(target_functions, list):
                           
                            for func in target_functions:
                                
                                print(f'\nrunning target function {func}')
                                func()
                        elif target_functions:
                            
                            target_functions()
                        else:
                            pass
                    time.sleep(0.025)
                            
            time.sleep(0.025)
        #clear out the queue to shutdown
        while not self.lever_presses.empty():
            _ = self.lever_presses.get()
        
        time.sleep(0.25)
        
        for fut in self.current_futures:
            if fut.done():
                self.current_futures.remove(fut)
            else:
                print(f'uhoh, a {self.name} lever future is not done when it should be.')
            
            
    def watch_lever_pin(self):
        print(f'\n()()()() watching a pin for {self.name} ()()()()\n')
        while self.end_monitor == False:
            if not GPIO.input(self.pin):
                print(f'{self.name}pressed!')
                self.rtf.click_on()
                
                while not GPIO.input(self.pin) and self.end_monitor == False:
                    '''waiting for vole to get off lever'''
                    time.sleep(0.025)
                self.rtf.click_off()
                self.lever_presses.put('pressed')
                time.sleep(self.inter_press_timeout)
            time.sleep(0.025)
        print(f'\n:::::: done watching a pin for {self.name}:::::\n')
                
    
class runtime_functions:
    
    def __init__(self):
        self.pi = pigpio.pi()
        self.serial_sender = sender()
        #self.serial_sender.start()
        #our queues for doign stuff and saving stuff
        
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
        self.monitor_beams = False

        #is there a pellet currently in the trough?
        self.pellet_state = False

        #are we overriding the door activity?
        self.door_override = {'door_1':False, 'door_2':False}

        #true = closed, false = open
        self.door_states = {'door_1':False, 'door_2':False}

        #timeout for closing the doors
        self.door_close_timeout = 10

        self.args_dict = None
        self.thread_executor = ThreadPoolExecutor(max_workers=20)
        self.worker_queue = queue.Queue()

    def thread_it(func, *args, **kwargs):
        '''simple decorator to pass function to our thread distributor via a queue. 
        these 4 lines took about 4 hours of googling and trial and error.
        the returned 'future' object has some useful features, such as its own task-done monitor. '''
        def pass_to_thread(self, *args, **kwargs):
            future = self.thread_executor.submit(func, *args, **kwargs)
            self.worker_queue.put((future, func.__name__, self.round))
            return future
        return pass_to_thread


    def start_timing(self):
        '''set the start time of experiment'''
        self.start_time = time.time()


    def setup_experiment(self, args_dict_in):
        self.args_dict = args_dict_in
        
        if self.args_dict['user']=='':
            no_user = True
            while no_user:
                self.user = input('no user listed. who is doing this experiment? \n')

                check = input('ok, double check its %s ? (y/n) \n'%self.user)
                if check.lower() in ['y', 'yes']:
                    no_user = False
        else:
            self.user = self.args_dict['user']
        
        #create the output file path
        save_dir = self.args_dict['output_directory']
        fname, date = self.generate_filename()
        self.this_path = os.path.join(save_dir, fname)
        self.args_dict['run_time'] = date
        
        print('\n\nPath is: ')
        print(self.this_path)
        print('\n')

        with open(self.this_path, 'w') as file:
            writer = csv.writer(file, delimiter = ',')

            writer.writerow([f"user: {self.user}", 
                            f"vole: {self.args_dict['vole']}", 
                            f'date: {date}',
                            f"experiment: {self.args_dict['experiment']}", 
                            f"Day: {self.args_dict['day']}", 
                            f"Pi: {socket.gethostname()}"])

            settings_string = self.create_header_string()
            writer.writerow([settings_string,])
            
            writer.writerow(['Round', 'Event', 'Time'])


            #spin up a dedicated writer thread
            wrt = threading.Thread(target = self.flush_to_CSV, daemon = True)
            wrt.start()

            or1 = threading.Thread(target = self.override_door_1, daemon = True)
            or2 = threading.Thread(target = self.override_door_2, daemon = True)
            or1.start()
            or2.start()

    def check_key_value_dictionaries(self, key_values, key_values_def, key_val_names_order):
        '''resolve issues if people add values to the key value dictionary and dont define them or put them in the name order list'''
        missing_def = [val for val in key_values if not val in key_values_def]
        if len(missing_def) > 0:
            print(f'no definition given for: {missing_def}')
        for val in missing_def:
            key_values_def[val] = 'unknown'

        missing_order = [val for val in key_values_def if not val in key_val_names_order]

        for val in missing_order:
            key_val_names_order += [val]

        return key_values_def, key_val_names_order

    def generate_filename(self):
        
        #unpack dict, but just to make string assembly cleaner for the first
        #line of the output file.
        vole = self.args_dict['vole']
        save_dir = self.args_dict['output_directory']
        exp = self.args_dict['experiment']
        day = int(self.args_dict['day'])
        
        date = datetime.datetime.now()
        fdate = '%s_%s_%s__%s_%s_'%(date.month, date.day, date.year, date.hour, date.minute)

        fname = fdate+f'_{exp}_vole_{int(vole)}.csv'
        return fname, fdate
    
    def create_header_string(self):
        '''make a file header from a header_dict'''   
        return af.create_header_string(self.args_dict)
    
    def setup_pins(self, verbose = True):
        '''here we get the gpio pins setup, and instantiate pigpio object.'''
        #setup our pins. Lever pins are input, all else are output
        GPIO.setmode(GPIO.BCM)

        for k in pins.keys():
            
            if 'lever' in k or 'switch' in k:
                if verbose:
                    print(k + ": IN")
                GPIO.setup(pins[k], GPIO.IN, pull_up_down=GPIO.PUD_UP)
            elif 'read' in k:
                if verbose:
                    print(k + ": IN")
                GPIO.setup(pins[k], GPIO.IN, pull_up_down=GPIO.PUD_UP)
            elif 'led' in k or 'dispense' in k :
                GPIO.setup(pins[k], GPIO.OUT)
                GPIO.output(pins[k], 0)
                if verbose:
                    print(k + ": OUT")
            else:
                GPIO.setup(pins[k], GPIO.OUT)
                if verbose:
                    print(k + ": OUT")

    def close_doors(self, door_ID = None, wait = False):
        '''close a door. can past a list of door IDs to open more than one door at once.'''

        workers = []
        if isinstance(door_ID, list):
            for arg in door_ID:
                workers+= [self._close_doors(self, door_ID = arg)]
                
        elif not door_ID:
            print('you must specify a door ID to open it.')
        else:
            workers+= [self._close_doors(self, door_ID = door_ID)]
        
        if wait:
            name = inspect.currentframe().f_code.co_name
            self.wait(workers, name)
    
    @thread_it
    def _close_doors(self, **kwargs):
        print('resetting door states')
        self.reset_doors()
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

    def reset_chamber(self):
        '''reset levers and doors. useful when preparing to run.'''

        servo_dict['lever_food'].angle = lever_angles['food'][1]
        servo_dict['lever_door_1'].angle = lever_angles['door_1'][1]
        servo_dict['lever_door_2'].angle = lever_angles['door_2'][1]

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
    
    
    def open_door(self, door_ID = None, wait = False):
        '''open a door. can past a list of door IDs to open more than one door at once.'''

        workers = []
        if isinstance(door_ID, list):
            for arg in door_ID:
                workers+= [self._open_door(door_ID = arg)]
        elif isinstance(door_ID, tuple):
            
            #tuples coming from press queue
            if len(door_ID)>1:
                print('too many door_IDs passed')
                raise
            else:
                workers+= [self._open_door(self, door_ID = door_ID)]

        elif not door_ID:
            print('you must specify a door ID to open it.')
        else:
            print(f"this is the door ID arg:   #{door_ID}#")
            workers+= [self._open_door(self, door_ID = door_ID)]
        
        if wait:
            name = inspect.currentframe().f_code.co_name
            self.wait(workers, name)

    @thread_it
    def _open_door(self, **kwargs):
        '''open a door!'''
        door_ID = kwargs['door_ID']
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
        


    def close_door(self, door_ID = ['door_1', 'door_2'], wait = True):
        '''can close doors'''
        workers = []
        if isinstance(door_ID, list):
            for arg in door_ID:
                workers+= [self._close_door(self, door_ID = arg)]
        elif isinstance(door_ID, tuple):
            
            #tuples coming from press queue
            if len(door_ID)>1:
                print('too many door_IDs passed')
                raise
            else:
                workers+= [self._close_door(self, door_ID = door_ID)]

        elif not door_ID:
            print('you must specify a door ID to open it.')
        else:
            print(f"this is the door ID arg:   #{door_ID}#")
            workers+= [self._close_door(self, door_ID = door_ID)]
        
        if wait:
            name = inspect.currentframe().f_code.co_name
            self.wait(workers, name)

    @thread_it
    def _close_door(self, **kwargs):
        door_ID = kwargs['door_ID']

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
                servo_dict['door_1'].throttle = continuous_servo_speeds['door_1']['close']
                while not GPIO.input(pins[f'door_1_override_close_switch']):
                    time.sleep(0.05)
                servo_dict['door_1'].throttle = continuous_servo_speeds['door_1']['stop']
            self.door_override['door_1'] = False


            time.sleep(0.25)

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
                servo_dict['door_2'].throttle = continuous_servo_speeds['door_2']['close']
                while not GPIO.input(pins['door_2_override_close_switch']):
                    time.sleep(0.05)
                servo_dict['door_2'].throttle = continuous_servo_speeds['door_2']['stop']
            self.door_override['door_2'] = False


            time.sleep(0.25)


    def monitor_beam_breaks(self):
        '''monitor any beam breaks until monitor_beams is set to False'''
        _ = self._monitor_beam_breaks(self)

    @thread_it
    def _monitor_beam_breaks(self):
        

        self.monitor_beams = True
        beam_1 = False
        beam_2 = False

        while self.monitor_beams:
            
            #if led blocked (1 -> 0) and last state was unblocked, write timestamp
            if not GPIO.input(pins['read_ir_1']) and not beam_1:
                self.timestamp_queue.put(f'{self.round}, beam_break_1_crossed, {time.time()-self.start_time}')
                self.serial_sender.send_data('cross_door_1')
                beam_1 = True
            
            #led no longer blocked
            elif GPIO.input(pins['read_ir_1']):
                beam_1 = False
            
            #led still blocked, dont reset
            else:
                pass

            #if led blocked (1 -> 0) and last state was unblocked, write timestamp
            if not GPIO.input(pins['read_ir_2']) and not beam_2:
                self.timestamp_queue.put(f'{self.round}, beam_break_2_crossed, {time.time()-self.start_time}')
                self.serial_sender.send_data('cross_door_2')
                beam_2 = True
            
            #led no longer blocked
            elif GPIO.input(pins['read_ir_2']):
                beam_2 = False
            
            #led still blocked, dont reset
            else:
                pass
        
            time.sleep(0.05)
        

    def monitor_first_beam_breaks(self):
        _ = self._monitor_first_beam_breaks(self)

    @thread_it
    def _monitor_first_beam_breaks(self):
        '''run monitor_beam_break until either beam is broken, and then stop'''

        self.monitor_beams = True
        beam_1 = False
        beam_2 = False

        while self.monitor_beams:
            if not GPIO.input(pins['read_ir_1']) and not beam_1:
                self.timestamp_queue.put(f'{self.round},{oes.beam_break_1}, {time.time()-self.start_time}')
                self.serial_sender.send_data('cross_door_1')
                beam_1 = True
                break
            

            if not GPIO.input(pins['read_ir_2']) and not beam_2:
                self.timestamp_queue.put(f'{self.round},{oes.beam_break_2}, {time.time()-self.start_time}')
                self.serial_sender.send_data('cross_door_2')
                beam_2 = True
                break
        self.monitor_beams = False
        time.sleep(0.05)

    def click_on(self):

        hz = 900
        self.pi.set_PWM_dutycycle(pins['speaker_tone'], 255/2)
        self.pi.set_PWM_frequency(pins['speaker_tone'], int(8000))

        time.sleep(0.02)
        self.pi.set_PWM_frequency(pins['speaker_tone'], int(hz))
        time.sleep(0.02)

        self.pi.set_PWM_dutycycle(pins['speaker_tone'], 0)
    
    def click_off(self):
        hz = 900
        self.pi.set_PWM_dutycycle(pins['speaker_tone'], 255/2)
        self.pi.set_PWM_frequency(pins['speaker_tone'], int(hz))
        time.sleep(0.02)
        self.pi.set_PWM_frequency(pins['speaker_tone'], int(hz/3))
        time.sleep(0.02)

        self.pi.set_PWM_dutycycle(pins['speaker_tone'], 0)

    def monitor_levers(self, lever_ID):
        '''monitor a lever. lever_IDs can be "food", "door_1", "door_2", or a list containing a combination (ie ["food", "door_1"]'''

        workers = []
        if isinstance(lever_ID, list):
            for arg in lever_ID:
                _ = self._monitor_levers(self, lever_ID = arg)
        else:
            _ = self._monitor_levers(self, lever_ID = lever_ID)

    @thread_it
    def _monitor_levers(self, **kwargs):

        
        self.monitor = True
        lever_ID = kwargs['lever_ID']
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
                    self.click_on()
                    while not GPIO.input(pins["lever_%s"%lever_ID]) and self.monitor:
                        print('hanging till lever not pressed')
                        time.sleep(0.05)
                    self.click_off()
                    lever = 0
                    self.lever_press_queue.put(lever_ID)

                    self.timestamp_queue.put('%i, %s lever pressed productive, %f'%(self.round, lever_ID, time.time()-self.start_time))
                    self.serial_sender.send_data('lever_press_' + lever_ID)

                else:
                    #we can still record from the lever until monitoring is turned
                    #off. note that this wont place anything in the lever_press queue,
                    #as that is just to tell the main thread the vole did something
                    self.timestamp_queue.put('%i, %s lever pressed, %f'%(self.round, lever_ID, time.time()-self.start_time))
                    while not GPIO.input(pins["lever_%s"%lever_ID]) and self.monitor:
                        'hanging till lever not pressed'
                        time.sleep(0.05)
                    lever = 0

            time.sleep(0.01)
        print('halting monitoring of %s lever'%lever_ID)
    
    def wait(self, worker, func_name):
        start = time.time()
        if isinstance(worker, list):
            print(f'waiting for one of the workers assigned to function "{func_name}"')
            while not any([w.done() for w in worker]):
                '''waiting for threads to finish'''
                time.sleep(0.025)

        else:
            print(f'waiting for function "{func_name}"')
            while not worker.done():
                time.sleep(0.025)
        done = time.time()
        print(f'"{func_name}" complete at {done - self.start_time} in {done - start}')
        

    def test_threading(self, message, wait = False):
        
        worker = self._test_decoration(self, message = message)
        
        if wait:
            name = inspect.currentframe().f_code.co_name
            self.wait(worker, name)


    @thread_it
    def _test_decoration(self, **kwargs):
        print(kwargs['message'])
        time.sleep(1)

    def test_threading(self, message, wait = False):
        
        worker = self._test_decoration(self, message = message)
        
        if wait:
            name = inspect.currentframe().f_code.co_name
            self.wait(worker, name)

    def extend_lever(self, lever_ID, wait = False):
        '''extend a lever. lever_IDs can be "food", "door_1", "door_2", or a list containing a combination (ie ["food", "door_1"]'''


        workers = []
        if isinstance(lever_ID, list):
            for arg in lever_ID:
                workers+= [self._extend_lever(self, lever_ID = arg)]
        else:
            workers+= [self._extend_lever(self, lever_ID = lever_ID)]
        
        if wait:
            name = inspect.currentframe().f_code.co_name
            self.wait(workers, name)

    @thread_it
    def _extend_lever(self, **kwargs):
        
        lever_ID = kwargs['lever_ID']
        

        #get extention and retraction angles from the operant_cage_settings
        extend = lever_angles[lever_ID][0]
        retract = lever_angles[lever_ID][1]
        
        wiggle = 5
        extend_start = max(0, extend-wiggle)
 
        print(f'\n\n**** extending lever {lever_ID}: extend[ {extend} ], retract[ {retract} ]**** ')
        self.timestamp_queue.put('%i, Levers out, %f'%(self.round, time.time()-self.start_time))
        self.serial_sender.send_data('lever_out_' + lever_ID)
        
        servo_dict[f'lever_{lever_ID}'].angle = extend_start
        time.sleep(0.05)
        servo_dict[f'lever_{lever_ID}'].angle = extend

    def retract_levers(self, lever_ID = ['food', 'door_1', 'door_2'], wait = False):
        '''retract lever. defaults to retracting all levers. lever_IDs can be "food", "door_1", "door_2", or a list containing a combination (ie ["food", "door_1"]'''

        workers = []
        if isinstance(lever_ID, list):
            for arg in lever_ID:
                workers+= [self._retract_lever(self, lever_ID = arg)]
        else:
            workers+= [self._retract_lever(self, lever_ID = lever_ID)]
        
        if wait:
            name = inspect.currentframe().f_code.co_name
            self.wait(workers, name)

    @thread_it
    def _retract_lever(self, *args, **kwargs):

        lever_ID = kwargs['lever_ID']
        timeout = 2


        #get extention and retraction angles from the operant_cage_settings
        extend = lever_angles[lever_ID][0]
        retract = lever_angles[lever_ID][1]
        
        #slightly wiggle the servo to try and relieve any binding
        wiggle = 10
        retract_start = max(180, retract + wiggle)
        
        start = time.time()
        while not GPIO.input(pins[f'lever_{lever_ID}']) and time.time()-start < timeout:
            'hanging till lever not pressed'
            time.sleep(0.05)
        servo_dict[f'lever_{lever_ID}'].angle = retract_start
        time.sleep(0.05)
        servo_dict[f'lever_{lever_ID}'].angle = retract
        self.timestamp_queue.put(f'{self.round}, Lever retracted|{lever_ID}, {time.time()-self.start_time}')
        

    def buzz(self, buzz_length, hz, name, wait = False):
        print('time to buzz')
        worker = self._buzz(self, buzz_length = buzz_length, hz = hz, name = name)
        if wait:
            name = inspect.currentframe().f_code.co_name
            self.wait(worker, name)
        return worker

    @thread_it
    def _buzz(self, **kwargs):
        '''take time (s), hz, and name as inputs'''
        
        buzz_len = kwargs['buzz_length']
        hz = kwargs['hz']
        name = kwargs['name']

        print(f'starting {name} tone {hz} hz')

        #set a 50% duty cycle, pass desired hz
        self.pi.set_PWM_dutycycle(pins['speaker_tone'], 255/2)
        self.pi.set_PWM_frequency(pins['speaker_tone'], int(hz))

        self.timestamp_queue.put(f'{self.round}, {name} tone start {hz}:hz {buzz_len}:seconds, {time.time()-self.start_time}')

        time.sleep(buzz_len)

        #sound off
        self.pi.set_PWM_dutycycle(pins['speaker_tone'], 0)

        self.timestamp_queue.put(f'{self.round}, {name} tone complete {hz}:hz {buzz_len}:seconds, {time.time()-self.start_time}')


    def dispense_pellet(self, wait = False):
        worker = self._dispense_pellet(self)
        if wait:
            name = inspect.currentframe().f_code.co_name
            self.wait(worker, name)
        return worker

    @thread_it
    def _dispense_pellet(self):
        timeout = time.time()

        read = 0

        #only dispense if there is no pellet, otherwise skip
        if not self.pellet_state:
            
            if not GPIO.input(pins['read_pellet']):
                print('attempting to dispense pellet, but sensor already reading blocked.')

            print('%i, starting pellet dispensing %f'%(self.round, time.time()-self.start_time))

            #we're just gonna turn the servo on and keep monitoring. probably
            #want this to be a little slow

            servo_dict['dispense_pellet'].throttle = continuous_servo_speeds['dispense_pellet']['fwd']

            #set a timeout on dispensing. with this, that will be a bit less than
            #6 attempts to disp, but does give the vole 2 sec in which they could nose
            #poke and trigger this as "dispensed"
            while time.time()-timeout < 3:

                if not GPIO.input(pins['read_pellet']):
                    read +=1

                if read > 2:
                    servo_dict['dispense_pellet'].throttle = continuous_servo_speeds['dispense_pellet']['stop']
                    self.timestamp_queue.put('%i, Pellet dispensed, %f'%(self.round, time.time()-self.start_time))
                    print('Pellet dispensed, %f'%(time.time()-self.start_time))

                    #now there is a pellet!
                    self.pellet_state = True

                    #offload monitoring to a new thread
                    self._read_pellet(self)
                    return None

                else:
                    #wait to give other threads time to do stuff, but fast enough
                    #that we check pretty quick if there's a pellet
                    time.sleep(0.025)
            servo_dict['dispense_pellet'].throttle = continuous_servo_speeds['dispense_pellet']['stop']
            self.timestamp_queue.put(f'{self.round}, Pellet dispense failure, {time.time()-self.start_time}')
            return None
        else:
            print("skipping pellet dispense due to pellet not retrieved")
            self.timestamp_queue.put(f'{self.round}, skip pellet dispense, {time.time()-self.start_time}')
            return None

    def pulse_sync_line(self, length, event_name, wait = False):
        worker = self._pulse_sync_line(self, length, event_name)
        if wait:
            name = inspect.currentframe().f_code.co_name
            self.wait(worker, name)

    @thread_it
    def _pulse_sync_line(self, length, event_name):
        '''not terribly accurate, but good enough. For now, this is called on every
        lever press or pellet retrieval. Takes length in seconds'''
        self.timestamp_queue.put(f'{self.round}, pulse sync line|{length}|{event_name}, {time.time()-self.start_time}')
        GPIO.output(pins['gpio_sync'], 1)
        time.sleep(length)
        GPIO.output(pins['gpio_sync'], 0)
    
    def clean_up(self, wait = True):
        '''cleanup all servos etc'''
        worker = self._clean_up(self)

        if wait:
            name = inspect.currentframe().f_code.co_name
            self.wait(worker, name)
    

    @thread_it  
    def _clean_up(self):

        '''cleanup all servos etc'''
        servo_dict['lever_food'].angle = lever_angles['food'][1]
        servo_dict['lever_door_1'].angle = lever_angles['door_1'][1]
        servo_dict['lever_door_2'].angle = lever_angles['door_2'][1]
        servo_dict['door_1'].throttle = continuous_servo_speeds['door_1']['stop']
        servo_dict['door_2'].throttle = continuous_servo_speeds['door_2']['stop']
        servo_dict['dispense_pellet'].throttle = continuous_servo_speeds['dispense_pellet']['stop']
        self.monitor = False
        self.serial_sender.shutdown()
        time.sleep(2)
        self.done = True

    def analyze(self):
        try:
            ana.run_analysis_script(self.this_path)
            
        except:
            print('there was a problem running analysis for this script!')
            traceback.print_exc()
            
    def breakpoint_monitor_lever(self, lever_ID):
        '''this lever monitor function tracks presses and returns when breakpoint reached'''
        workers = []
        if isinstance(lever_ID, list):
            for arg in lever_ID:
                workers+= [self._breakpoint_monitor_lever(self, lever_ID = arg)]
        else:
            workers+= [self._breakpoint_monitor_lever(self, lever_ID = lever_ID)]
        


    @thread_it
    def _breakpoint_monitor_lever(self, *args, **kwargs):
        '''this lever monitor function tracks presses and returns when breakpoint reached'''
        
        self.monitor = True
        lever_ID= kwargs['lever_ID']
        "monitor a lever. If lever pressed, put lever_ID in queue. "
        lever=0


        while self.monitor:
            if not GPIO.input(pins["lever_%s"%lever_ID]):
                lever +=1

            #just guessing on this value, should probably check somehow empirically
            if lever > 2:

                #send the lever_ID to the lever_q to trigger a  do_stuff.put in
                #the main thread/loop
                
                self.timestamp_queue.put('%i, %s lever pressed, %f'%(self.round, lever_ID, time.time()-self.start_time))


                self._retract_lever(lever_ID = lever_ID)

                self.lever_press_queue.put(lever_ID)
                lever = 0
                self.monitor = False
                break

            time.sleep(25/1000.0)
        print(f'\nmonitor thread done for lever {lever_ID}')

    def read_pellet(self):
        worker = self._read_pellet(self)

    @thread_it
    def _read_pellet(self):

        disp_start = time.time()
        
        disp = False
        #retrieved, IE empty trough
        read_retr = 0

        #dispensed pellet there, IE full trough
        read_disp = 0
        timeout = 2000

        while time.time() - disp_start < timeout and not self.done:
            #note this is opposite of the dispense function
            if GPIO.input(pins['read_pellet']):
                read_retr += 1
            else:
                read_disp += 1

            if read_retr > 5 and self.pellet_state:
                self.pulse_sync_line(length = 0.05, event_name = 'pellet retrieved')
                self.timestamp_queue.put(f'{self.round}, pellet retrieved, {time.time()-self.start_time}')
                self.serial_sender.send_data('pellet_retrieved')
                print(f'\n\n\nPellet taken! {(time.time()-self.start_time)}\n\n\n')
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
                    print('\n\n')
                time.sleep(0.01)


    def countdown_timer(self, time_interval, next_event):
        worker = self._countdown_timer(self, 
                                    time_interval = time_interval, 
                                    next_event = next_event)

    @thread_it
    def _countdown_timer(self, **kwargs):

        timeinterval = kwargs['time_interval']
        next_event = kwargs['next_event']

        start = time.time()
        while time.time() - start < timeinterval:
            sys.stdout.write(f"\r{np.round(timeinterval - (time.time()-start))} seconds left before {next_event}")
            time.sleep(0.5)
            sys.stdout.flush()

    def stop_all_servos(self):
        self.servo_dict['door_1'].throttle = self.continuous_servo_speeds['door_1']['stop']
        self.servo_dict['door_2'].throttle = self.continuous_servo_speeds['door_2']['stop']
        self.servo_dict['food'].throttle = self.continuous_servo_speeds['food']['stop']


    def print_timestamp_queue(self):
        '''use if you arent using the csv fush function in order to debug'''
        #spin up a dedicated writer thread
        return self._print_timestamp_queue(self)
        
    @thread_it
    def _print_timestamp_queue(self):
        '''use if you arent using the csv fush function in order to debug'''
        print('ready to print timestamps')
        while not self.done or not self.timestamp_queue.empty():
            
            if not self.timestamp_queue.empty():
                
                line = self.timestamp_queue.get().split(',')
                print(f'writing ###### {line}')
            time.sleep(0.025)
        
    
    
    
    def monitor_workers(self, verbose = False):
        return self._monitor_workers(self, verbose = verbose)
        
    
    @thread_it
    def _monitor_workers(self, **kwargs):
        workers = []
        verbose = kwargs['verbose']
        
        while not self.done:
            if not self.worker_queue.empty():
                #receive worker, parent function, round of initiation
                worker_and_info = self.worker_queue.get()
                if verbose:
                    print(f'worker queue received worker {worker_and_info}')
                #if we have an identically named worker, we will need to modify this tuple
                if worker_and_info[1] == '_monitor_workers':
                   #ignore this functions own worker object
                   #i dont like running this test every time when we really only need it 
                   #once, but not sure how to elegantly fix without altering
                   #thread_it
                   pass
                else:
                    workers += [worker_and_info]
                    print(f'currently {len(workers)} threads running via pool executor')

            for element in workers:
                worker, name, init_round = element
                '''print(f'checking {element}')'''
                
                if not worker.running():
                    if worker.exception():
                        print('oh snap! one of your threads had a problem.\n\n\n')
                        
                        print('******-----ERROR------******')
                        print(f"function: {name} round: {init_round}")
                        print(worker.exception())
                        print('******-----ERROR------******\n\n\n')
                        workers.remove(element)
                    elif worker.done():
                        if verbose:
                            print(f'worker done {element}')
                        workers.remove(element)
                    else:
                        pass
                    #print(f'$$$$$$$$$$$$ currently {len(workers)} threads running via pool executor $$$$$$$$$$$$')
                
            time.sleep(0.025)
        
        time.sleep(1)
        print('done and exiting')
        while len(workers) > 0:
            for element in workers:
                worker, _, _ = element
                if not worker.done():
                    print(f'{element} still not done... you may need to force exit')
                else:
                    workers.remove(element)
            time.sleep(0.25)
