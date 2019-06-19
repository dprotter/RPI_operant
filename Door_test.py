from adafruit_servokit import ServoKit
import time
kit = ServoKit(channels = 16)
ser = kit.continuous_servo[3]
open_throttle = 0.7
stop = 0.065
close_throttle = 0-open_throttle+stop

open_time = 1
close_time = 1
for i in range(3):
    ser.throttle = open_throttle
    time.sleep(open_time)
    ser.throttle = stop
    time.sleep(1)
    ser.throttle = close_throttle
    time.sleep(close_time)
ser.throttle = stop
