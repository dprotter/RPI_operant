from adafruit_servokit import ServoKit
import time
kit = ServoKit(channels = 16)
ser = kit.continuous_servo[3]
open_throttle = 0.8
stop = 0.07

close_throttle = -0.1

open_time = 1.25
close_time = 2.7
for i in range(10):
    ser.throttle = open_throttle
    time.sleep(open_time)
    ser.throttle = stop
    time.sleep(0.5)
    ser.throttle = close_throttle
    time.sleep(close_time)
    ser.throttle = stop
    time.sleep(0.5)
