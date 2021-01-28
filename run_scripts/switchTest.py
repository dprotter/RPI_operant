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

def run_script():
    print(pins)
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
    print(pins)
    try:
        while True:
            print(GPIO.input(pins['read_pellet']))
    except KeyboardInterrupt:
        pass
run_script()