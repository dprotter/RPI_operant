import pigpio
from operant_cage_settings import pins, servo_dict, continuous_servo_speeds, lever_angles
import time
import os

os.system('sudo pigpiod')

GPIO = pigpio.pi()



GPIO.set_mode(12, GPIO.OUT)



print('software pwm')
pi.set_PWM_dutycycle(12, 255/2)
pi.set_PWM_frequency(12, 3000)

time.sleep(2)
pi.hardware_PWM(12, 3000, 0)
time.sleep(1)

print('experiment start tone')

pi.hardware_PWM(12, 3000, 1e6*0.5)

time.sleep(1)
pi.hardware_PWM(12, 3000, 0)
print('all done')
GPIO.cleanup()
