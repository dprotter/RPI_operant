from home_base.functions import runtime_functions as FN
from home_base.functions import pins, GPIO
from tabulate import tabulate
import time

fn = FN()

fn.setup_pins()
num_pins = len(pins)

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

while True:
    print_pin_status()