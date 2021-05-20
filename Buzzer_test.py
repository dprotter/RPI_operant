import pigpio
import os
#activates the pigpio daemon that runs PWM, unless its already running
if os.system('sudo lsof -i TCP:8888'):
    os.system('sudo pigpiod')

import time as time

import RPi.GPIO as GPIO
from home_base.operant_cage_settings import pins


pi = pigpio.pi()
pin = pins['speaker_tone']


try:
    print('3k')

    pi.set_PWM_dutycycle(pin, 255/2)
    pi.set_PWM_frequency(pin, 3000)



   
    while True:
        
        time.sleep(0.05)

except KeyboardInterrupt:
    pi.set_PWM_dutycycle(pin, 0)





print('all done')
