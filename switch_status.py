import home_base.functions as FN
fn = FN.runtime_functions()
from home_base.functions import pins, GPIO
from tabulate import tabulate
import time
import threading

fn.setup_pins()
fn.start_time = time.time()
fn.round = 0


or1 = threading.Thread(target = fn.override_door_1, daemon = True)
or2 = threading.Thread(target = fn.override_door_2, daemon = True)
or1.start()
or2.start()


fn.setup_pins()
num_pins = len(pins)


fn.extend_lever(lever_ID = ['food', 'door_1', 'door_2'])

def print_pin_status():

    print("\033c", end="")
    pin_keys = sorted(pins.keys())
    status = []
    for i in range(0,num_pins,2):
        
        if i+1<num_pins:
            status += [[pin_keys[i], GPIO.input(pins[pin_keys[i]]),
                        pin_keys[i+1], GPIO.input(pins[pin_keys[i+1]])]]
        else:
            status += [[pin_keys[i], GPIO.input(pins[pin_keys[i]]),
                        '', '']]
    print(tabulate(status, headers = ['pin', 'status', 'pin', 'status']))
    time.sleep(0.05)

try:
    while True:
        print_pin_status()
        time.sleep(0.05)

except KeyboardInterrupt:
    print('\n\ncleaning up')
    fn.clean_up()