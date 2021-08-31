import sys
sys.path.append('/home/pi/')
import time
from RPI_operant.home_base.bonsai_serial_sender import sender

coms = sender()
coms.start()

if __name__ == '__main__':
    coms.send_data('lever_out_food')
    
    while coms.busy():
        print('holding for coms')
        time.sleep(0.25)
    coms.send_data('lever_press_door_1')
    
    while coms.busy():
        print('holding for coms')
        time.sleep(0.25)
    coms.finish()