import pigpio

import os
import RPi.GPIO as GPIO
#activates the pigpio daemon that runs PWM, unless its already running
if os.system('sudo lsof -i TCP:8888'):
    os.system('sudo pigpio')

pi = pigpio.pi()


print('2k')
pi.set_PWM_dutycycle(8, 255/2)
pi.set_PWM_frequency(8, 2000)

time.sleep(2)

pi.set_PWM_dutycycle(8, 0)

time.sleep(1)
print('3k')

pi.set_PWM_dutycycle(8, 255/2)
pi.set_PWM_frequency(8, 3000)


time.sleep(2)
pi.set_PWM_dutycycle(8, 0)


print('all done')
