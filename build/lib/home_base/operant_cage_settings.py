from adafruit_servokit import ServoKit
import os

kit = ServoKit(channels=16)

if not os.path.isfile('/etc/RPI_operant/operant_cage_settings_local.py'):
    print('no local operant cage settings, reverting to defaults')

    from home_base.operant_cage_settings_defaults import pins, lever_angles, continuous_servo_speeds, servo_dict

else:
    print('importing local operant cage settings')
    import importlib.util
    spec = importlib.util.spec_from_file_location("operant_cage_settings_local", 
                                                    "/etc/RPI_operant/operant_cage_settings_local.py")
    foo = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(foo)

    pins = foo.pins
    lever_angles = foo.lever_angles
    continuous_servo_speeds = foo.continuous_servo_speeds
    servo_dict = foo.servo_dict