import sys
sys.path.append('/home/pi/')
import time
import RPI_operant.home_base.functions as FN



fn = FN.runtime_functions()
fn.setup_pins(verbose = False)

mw_fut = fn.monitor_workers()
fn.print_timestamp_queue()
time.sleep(1)
time.sleep(0.5)
fn.start_timing()
fn.buzz(buzz_length = 0.25, hz = 2000, name = 'test', wait = True)
print(f'timestamp is empty {fn.timestamp_queue.empty()}')


fn.extend_lever(lever_ID = 'food')
fn.dispense_pellet()
print(f'timestamp is empty {fn.timestamp_queue.empty()}')

fn.clean_up()
