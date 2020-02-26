import pigpio
import time as time
import os
import RPi.GPIO as GPIO
#activates the pigpio daemon that runs PWM, unless its already running
if os.system('sudo lsof -i TCP:8888'):
    os.system('sudo pigpiod')

pi = pigpio.pi()


print('1k')
pi.set_PWM_dutycycle(14, 255/2)
pi.set_PWM_frequency(14, 1000)

time.sleep(2)

pi.set_PWM_dutycycle(14, 0)

time.sleep(1)
print('3k')

pi.set_PWM_dutycycle(14, 255/2)
pi.set_PWM_frequency(14, 3000)


time.sleep(2)
pi.set_PWM_dutycycle(14, 0)


print('all done')
