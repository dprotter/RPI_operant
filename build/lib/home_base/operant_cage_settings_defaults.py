from adafruit_servokit import ServoKit
import os

kit = ServoKit(channels=16)

'''dont change these default values! if you need to make changes to the operant cage settings,
like changing lever angle values or servo speeds, copy '''

pins = {'lever_food':24,
    'lever_door_1':27,
    'lever_door_2':22,
    'led_food':0,
    'read_pellet':13,
    'speaker_tone':21,
    'led_social':19,
    'door_1_override_open_switch':4,
    'door_2_override_open_switch':16,
    'door_1_override_close_switch':23,
    'door_2_override_close_switch':25,
    'door_1_state_switch':17,
    'door_2_state_switch':18,

    'gpio_sync':6, }


#values Levers [extended, retracted]
lever_angles = {'food':[100, 50], 'door_1':[70,120], 'door_2':[85,35]}


continuous_servo_speeds = {
                        'dispense_pellet':{'stop':0.15, 'fwd':0.12},
                        'door_1':{'stop':0.16, 'close':0.8, 'open':-0.1,
                        'open time':1.6,
                        },
                        'door_2':{'stop':0.1, 'open':0.8, 'close':-0.1,
                        'open time':1.6,
                        }
                                                                            }


servo_dict = {'lever_food':kit.servo[14], 'dispense_pellet':kit.continuous_servo[1],
                'lever_door_1':kit.servo[2], 'door_1':kit.continuous_servo[0],
                'lever_door_2':kit.servo[12],'door_2':kit. continuous_servo[13]}