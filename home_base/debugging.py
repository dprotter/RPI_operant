import sys
sys.path.append('/home/pi/')

import RPI_operant.home_base.functions as FN
fn = FN.runtime_functions()


import threading
import time

fn.test_threading(message = 'this is a test', wait = True)
fn.extend_lever(lever_ID = 'food', wait = True)