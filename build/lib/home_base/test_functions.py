import RPi.GPIO as GPIO
import os
if os.system('sudo lsof -i TCP:8888'):
    os.system('sudo pigpiod')
import socket
import time
from operant_cage_settings import (kit, pins,
    lever_angles, continuous_servo_speeds,servo_dict)
import datetime
import csv

import numpy as np
import queue
import random
import pigpio
pi = pigpio.pi()

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

setup_pins()
#is there a pellet currently in the trough?
pellet_state = False

#are we overriding the door activity?
door_override = {'door_1':False, 'door_2':False}

#true = closed, false = open
door_states = {'door_1':False, 'door_2':False}


def extend_lever(lever_ID):

    #get extention and retraction angles from the operant_cage_settings
    extend = lever_angles[lever_ID][0]
    retract = lever_angles[lever_ID][1]

    modifier = 15
    
    if extend > retract:
        retract_start = retract - modifier
        extend_start = extend + modifier
    else:
        retract_start = retract + modifier
        extend_start = extend - modifier
    
    
    print(f'extending lever {lever_ID}: extend[ {extend} ], retract[ {retract} ]')
    servo_dict[f'lever_{lever_ID}'].angle = extend_start
    time.sleep(0.1)
    servo_dict[f'lever_{lever_ID}'].angle = extend
    
def retract_lever(lever_ID):
    #get extention and retraction angles from the operant_cage_settings
    extend = lever_angles[lever_ID][0]
    retract = lever_angles[lever_ID][1]

    modifier = 10
    
    if extend > retract:
        retract_start = retract - modifier
        extend_start = extend + modifier
    else:
        retract_start = retract + modifier
        extend_start = extend - modifier
    
    print(f'extending lever {lever_ID}: extend[ {extend} ], retract[ {retract} ]')
    servo_dict[f'lever_{lever_ID}'].angle = retract_start
    time.sleep(0.1)
    servo_dict[f'lever_{lever_ID}'].angle = retract
    


def test_lever_switch(lever_ID):
    extend_lever(lever_ID)
    print(f'lets test {lever_ID} lever')
    time.sleep(3)
    start = time.time()
    while time.time() - start < 10:
        print(GPIO.input(pins[f'lever_{lever_ID}']))
        time.sleep(0.2)
    retract_lever(lever_ID)