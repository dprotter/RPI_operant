import time
import RPi.GPIO as GPIO
from home_base.operant_cage_settings import pins, servo_dict, continuous_servo_speeds, lever_angles

pins_here =  {}
for k in pins.keys():
    print(k)
    if 'lever' in k or 'switch' in k:
        print(k + ": IN")
        GPIO.setup(pins[k], GPIO.IN, pull_up_down=GPIO.PUD_UP)
        pins_here[k] = pins[k]

for key in pins_here.keys():
    print('Press %s lever on pin %i'%(key, pins_here[key]))
    start = time.time()
    press = 0
    while(time.time() - start <20):
        if GPIO.input(pins_here[key]):
            print('the %s lever was pressed!'%key)
            press += 1
        if press > 3:
            print('ok, we get it, you can press a lever')
            break
        time.sleep(0.05)

raw = input('do you want to see the raw lever data? (10 sec)(y/n)')
if 'y' in raw:

    for key in pins_here.keys():
        print('Press %s lever on pin %i'%(key, pins_here[key]))
        start = time.time()
        press = 0
        while(time.time() - start <10):
            print(GPIO.input(pins_here[key]))
            time.sleep(0.05)
