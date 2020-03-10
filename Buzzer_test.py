import pigpio
import time as time
import os
import RPi.GPIO as GPIO
from home_base.operant_cage_settings import pins

#activates the pigpio daemon that runs PWM, unless its already running
if os.system('sudo lsof -i TCP:8888'):
    os.system('sudo pigpiod')

pi = pigpio.pi()
pin = pins['speaker_tone']

print('1k')
pi.set_PWM_dutycycle(pin, 255/2)
pi.set_PWM_frequency(pin, 1000)

time.sleep(2)

pi.set_PWM_dutycycle(pin, 0)

time.sleep(1)
print('3k')

pi.set_PWM_dutycycle(pin, 255/2)
pi.set_PWM_frequency(pin, 3000)


time.sleep(2)
pi.set_PWM_dutycycle(pin, 0)


print('all done')
