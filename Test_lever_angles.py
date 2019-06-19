from adafruit_servokit import ServoKit
import time

kit = ServoKit(channels=16)

servo_dict = {'food':kit.servo[0], 'dispense_pellet':kit.continuous_servo[2],
                'social':kit.servo[1], 'door':kit.continuous_servo[3]}
