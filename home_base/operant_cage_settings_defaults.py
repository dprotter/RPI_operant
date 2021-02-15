from adafruit_servokit import ServoKit
import os

kit = ServoKit(channels=16)

'''dont change these default values! if you need to make changes to the operant cage settings,
like changing lever angle values or servo speeds, copy '''

pins = {'lever_food':27,
    'lever_door_1':18,
    'lever_door_2':22,
    'led_food':19,
    'read_pellet':16,
    'speaker_tone':21,
    'led_social':20,
    'door_1_override_open_switch':24,
    'door_2_override_open_switch':6,
    'door_1_override_close_switch':25,
    'door_2_override_close_switch':5,
    'door_1_state_switch':4,
    'door_2_state_switch':17,
    'read_ir_1':12,
    'read_ir_2':13,

    'gpio_sync':23, }


#values Levers [extended, retracted]
lever_angles = {'food':[100, 70], 'door_1':[100,55], 'door_2':[90,35]}


continuous_servo_speeds = {
                        'dispense_pellet':{'stop':0.15, 'fwd':0.12},
                        'door_1':{'stop':0.1, 'close':-0.1, 'open':0.8,
                        'open time':1.6,
                        },
                        'door_2':{'stop':0.1, 'open':-0.1, 'close':0.8,
                        'open time':1.6,
                        }
                                                                            }


servo_dict = {'lever_food':kit.servo[14], 'dispense_pellet':kit.continuous_servo[1],
                'lever_door_1':kit.servo[2], 'door_1':kit.continuous_servo[0],
                'lever_door_2':kit.servo[12],'door_2':kit. continuous_servo[13]}
