import pigpio
from operant_cage_settings import pins, servo_dict, continuous_servo_speeds, lever_angles
import time
import os
import RPi.GPIO as GPIO
os.system('sudo pigpiod')
GPIO.setmode(GPIO.BCM)
pi = pigpio.pi()


GPIO.setup(6, GPIO.OUT)


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

print("LED")
GPIO.output(6, 1)
time.sleep(2)
pi.hardware_PWM(12, 4000, 0)

GPIO.output(6,0)
print('all done')
GPIO.cleanup()
