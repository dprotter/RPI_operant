from home_base.operant_cage_settings import (kit, pins,
    lever_angles, continuous_servo_speeds, servo_dict)



servo_dict['door_1'].throttle = continuous_servo_speeds['door_1']['stop']
servo_dict['door_2'].throttle = continuous_servo_speeds['door_2']['stop']
servo_dict['dispense_pellet'].throttle = continuous_servo_speeds['dispense_pellet']['stop']

servo_dict['lever_food'].angle = lever_angles['food'][1]
servo_dict['lever_door_1'].angle = lever_angles['door_1'][1]
servo_dict['lever_door_2'].angle = lever_angles['door_2'][1]