pins = {'lever_food':4,'lever_social':17,'led_food':18, 'read_pellet':24,
    'pellet_tone':21, 'start_tone':20}


#values Levers [extended, retracted]
lever_angles = {'food':[40, 115], 'social':[40,100]}


continuous_servo_speeds = {
                        'dispense_pellet':{'stop':0.04, 'fwd':0.09},
                        'door':{'stop':0.04, 'open':0.9, 'close':0-0.9+0.04}
                                                                            }


servo_dict = {'food':kit.servo[1], 'dispense_pellet':kit.continuous_servo[2],
                'social':kit.servo[0], 'door':kit.continuous_servo[3]}
