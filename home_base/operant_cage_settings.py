from adafruit_servokit import ServoKit
kit = ServoKit(channels=16)
pins = {'lever_food':4,'lever_door_1':17,'led_food':18, 'read_pellet':24,
    'pellet_tone':21, 'start_tone':20, 'door_close_tone':22, 'led_social':19,
    'door_1_override_open_switch':13, 'door_1_override_close_switch':16,
    'door_1_state_switch':0, 'door_state_2_switch':0, 'door_2_override_open_switch':0,
    'door_2_override_close_switch':0,'gpio_sync':23, }


#values Levers [extended, retracted]
lever_angles = {'food':[40, 115], 'door_1':[43,100], 'door_2':[43,100]}


continuous_servo_speeds = {
                        'dispense_pellet':{'stop':0.04, 'fwd':0.09},
                        'door_1':{'stop':0.07, 'open':0.8, 'close':-0.1,
                        'open time':1.25*1.4,
                        },
                        'door_2':{'stop':0.07, 'open':0.8, 'close':-0.1,
                        'open time':1.25*1.4,
                        }
                                                                            }


servo_dict = {'food':kit.servo[1], 'dispense_pellet':kit.continuous_servo[2],
                'social':kit.servo[0], 'door_1':kit.continuous_servo[3], 'door_2':kit. continuous_servo[4]}
