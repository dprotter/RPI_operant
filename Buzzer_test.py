import pigpio
from operant_cage_settings import pins, servo_dict, continuous_servo_speeds, lever_angles
import time
import os

os.system('sudo pigpiod')

pi = pigpio.pi()





print('software pwm')
print('2k')
pi.set_PWM_dutycycle(12, 255/2)
pi.set_PWM_frequency(12, 2000)

time.sleep(2)
pi.hardware_PWM(12, 3000, 0)
time.sleep(1)

print('4k')

pi.set_PWM_dutycycle(12, 255/2)
pi.set_PWM_frequency(12, 4000)

time.sleep(1)
pi.hardware_PWM(12, 4000, 0)
print('all done')
GPIO.cleanup()
