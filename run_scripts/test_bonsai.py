import sys
sys.path.append('/home/pi/')
import time
from RPI_operant.home_base.bonsai_serial_sender import sender

coms = sender()
coms.start()

if __name__ == '__main__':
    coms.send_data('leverOutFood')
    coms.finish()
    while coms.running():
        print('holding for coms')
        time.sleep(0.25)