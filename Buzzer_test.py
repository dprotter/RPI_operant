import RPi.GPIO as GPIO
from operant_cage_settings import pins, servo_dict, continuous_servo_speeds, lever_angles
import time

k = 'pellet_tone'

GPIO.setup(pins[k], GPIO.OUT)
GPIO.output(pins[k], 0)
pwm_tone = GPIO.PWM(pins[k], 600)

print('pellet tone')
pwm_tone.ChangeFrequency(3000)
pwm_tone.start(50)
time.sleep(2)
pwm_tone.stop()
time.sleep(1)

print('experiment start tone')

pwm_tone.ChangeFrequency(1200)

for i in range(10):
    time.sleep(0.05)
    pwm_tone.start(50)
    time.sleep(0.1)
    pwm_tone.stop()

print('all done')
GPIO.cleanup()
