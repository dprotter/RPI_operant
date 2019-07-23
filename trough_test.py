import RPi.GPIO as GPIO
import time
from operant_cage_settings import pins

GPIO.setmode(GPIO.BCM)

GPIO.setup(pins['read_pellet'], GPIO.IN, pull_up_down=GPIO.PUD_UP)

start = time.time()
i = 0
while(time.time() - start < 10):
    print('%i     %i'%(pins['read_pellet'], i))
    i+= 1
    time.sleep(0.05)
print('done')
