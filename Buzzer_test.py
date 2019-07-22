import pigpio
from operant_cage_settings import pins, servo_dict, continuous_servo_speeds, lever_angles
import time
import os
import RPi.GPIO as GPIO
#activates the pigpio daemon that runs PWM, unless its already running
if os.system('sudo lsof -i TCP:8888'):
    os.system('sudo pigpio')

pi = pigpio.pi()


print('2k')
pi.set_PWM_dutycycle(pins['pellet_tone'], 255/2)
pi.set_PWM_frequency(pins['pellet_tone'], 2000)



print('4k')

pi.set_PWM_dutycycle(pins['pellet_tone'], 255/2)
pi.set_PWM_frequency(pins['pellet_tone'], 4000)


time.sleep(2)
pi.set_PWM_dutycycle(pins['pellet_tone'], 0)


print('all done')
