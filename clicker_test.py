import sys
sys.path.append('/home/pi/')
import RPI_operant.home_base.functions as FN
fn = FN.runtime_functions()
from home_base.functions import pins, GPIO
from tabulate import tabulate
import time
import threading

fn.setup_pins()


fn.setup_pins()

try:
    while True:
        input()
        fn.click_on()
        input()
        fn.click_off()

except KeyboardInterrupt:
    print('\n\ncleaning up')
    

