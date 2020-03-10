from home_base.operant_cage_settings import (kit, pins,
    lever_angles, continuous_servo_speeds, servo_dict)



servo_dict['door_1'].throttle = continuous_servo_speeds['door_1']['stop']
servo_dict['door_2'].throttle = continuous_servo_speeds['door_2']['stop']
servo_dict['dispense_pellet'].throttle = continuous_servo_speeds['dispense_pellet']['stop']
