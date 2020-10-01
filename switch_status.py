from home_base.functions import runtime_functions as FN
from home_base.functions import pins, GPIO
from tabulate import tabulate
import time


fn.setup_pins()
fn.start_time = time.time()
fn.round = 0


or1 = threading.Thread(target = fn.override_door_1, daemon = True)
or2 = threading.Thread(target = fn.override_door_2, daemon = True)
or1.start()
or2.start()
fn = FN()

fn.setup_pins()
num_pins = len(pins)

fn.do_stuff_queue.put(('extend lever',
                            ('door_1')))

fn.do_stuff_queue.put(('extend lever',
                            ('door_2')))


fn.do_stuff_queue.put(('extend lever',
                            ('food')))

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