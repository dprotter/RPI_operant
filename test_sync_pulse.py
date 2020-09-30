import home_base.functions as FN
fn = FN.runtime_functions()

import threading
import time

fn.setup_pins()
fn.start_time = time.time()
fn.round = 0


or1 = threading.Thread(target = fn.override_door_1, daemon = True)
or2 = threading.Thread(target = fn.override_door_2, daemon = True)
or1.start()
or2.start()

for x in range(5):

        #spin up threads for the thread distributor
        t = threading.Thread(target = fn.thread_distributor)

        #when main thread finishes, kill these threads
        t.daemon = True
        t.start()
for i in range(5):
    fn.pulse_sync_line(1)
    time.sleep(0.5)