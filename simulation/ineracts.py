""" 
Date Created : 8/5/2021
Date Modified: 8/5/2021
Author: Ryan Cameron, David Protter, Sarah ???
Description: This is the script that has all of the interactable objects for the vole
Property of Donaldson Lab, University of Colorado Boulder, PI Zoe Donaldson
http://www.zdonaldsonlab.com/
Code located at - https://github.com/donaldsonlab/Operant-Cage 
"""

# Imports
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

import RPI_operant.home_base.functions as FN
fn = FN.runtime_functions()

# Switch
class switch:
    # SWITCH is the class that controls a switch object
    def __init__(self, pin = None, parent = None):
        self.pin = pin
        self.parent = self.set_parent(self, parent)
        self.presses = queue.Queue()

# Servo
class servo:
    # SERVO controls the properties of a servo that can be added to any other object
    def __init__(self, pin = None, parent = None):
        self.pin = pin
        self.parent = parent
        self.angle = None

    def move(self, angle):
        # MOVE moves the servo to the specified angle
        self.pin.angle = angle
        self.angle = angle

    def set_parent(self, parent):
        # SET_PARENT sets the parent object of this servo and connects the two objects to automatically update when something changes with the other.
        return parent

# IR
class irbeam:
    # IRBEAM is the object that houses the IR beams that can be put into the dispenser as well as the other places on the floor of the cage
    def __init__(self, pin = None, command = None, parent = None):
        self.pin = pin
        self.command = command
        self.parent = self.set_parent(self, parent)

    def set_parent(self, parent):
        # SET_PARENT sets and connets the parent object to this object in order to have the references in place.
        return parent 

# Levers
class lever:
    # LEVER is a class that contains all the info that the levers need to operate in the simulation. This includes the options that the levers have, the extend and retract methods, and signals about whether the vole pressed the lever or not. 
    def __init__(self, lever_ID = None, command = None, sender = None):
        self.lever_ID = lever_ID
        self.pressed = False # if true, the lever was just pressed
        self.extended = False
        self.commandTag = command # Tag for the command to send when events occur
        self.pin = pins["lever_%s"%lever_ID]
        self.sender = sender
        self.children = {'switch': switch(pin=self.pin,parent=self), 'servo': servo(pin=servo_dict[f'lever_{lever_ID}'],parent=self)}
        # 

    def extend(self):
        # EXTEND extends the lever to the angle specified in the settings file
        extended = lever_angles[self.lever_ID][0]
        # Extend the lever
        self.children['servo'].move(extended)
        self.send()

    def retract(self):
        # RETRACT retracts the lever to the angle specified in the settings file
        retracted = lever_angles[self.lever_ID][1]
        # Retract the lever
        self.children['servo'].move(retracted)

    def send(self):
        # SEND is a backend function that sends the command to the arduino whenever a specified event is processed. 
        self.sender.data = self.commandTag
        self.sender.send_data()

# Food Dispenser
class dispenser:
    # DISPENSER is the object that dispenses the food pellets. It includes an IR sensor that says when the pellet has been dispensed and then taken as well. This also controls the servo for the food dispenser.

    def __init__(self, command = None, sender = None):
        self.command = command
        self.children = {'servo': servo(pin=servo_dict['dispense_pellet'],parent=self), 'ir': }
        self.sender = sender

# Doors

# IR's

# Vole (Test and Tethered)