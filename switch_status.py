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

for x in range(5):

        #spin up threads for the thread distributor
        t = threading.Thread(target = fn.thread_distributor)

        #when main thread finishes, kill these threads
        t.daemon = True
        t.start()

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

try:
    while True:
        print_pin_status()
        time.sleep(0.05)

except KeyboardInterrupt:
    print('\n\ncleaning up')
    fn.do_stuff_queue.put(('clean up', ))
    fn.do_stuff_queue.join()