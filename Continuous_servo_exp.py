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
kit.continuous_servo[1].throttle = 0

for i in range(10):
    throttle = 1.0 - 0.2*i
    print(throttle)
    kit.continuous_servo[1].throttle = throttle
    time.sleep(1.5)
