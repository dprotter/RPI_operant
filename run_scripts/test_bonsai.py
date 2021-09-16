import sys
sys.path.append('/home/pi/')
import time
from RPI_operant.home_base.bonsai_serial_sender import sender

coms = sender()
coms.start()
while not coms.active:
    print('waiting for coms startup')
    time.sleep(0.1)
print('succesful startup')
time.sleep(1)

if __name__ == '__main__':
    print('Sending...')
    messData = 'lever_out_food'
    coms.send_data(messData)
    print('Sent: ' + messData)
    
    for i in range(10):
        while coms.busy():
            print('holding for coms')
            time.sleep(0.25)
        time.sleep(2.5)
        messData = 'lever_press_door_2'
        coms.send_data(messData)
        print('Sent: ' + messData)
    
    # while coms.busy():
    #     print('holding for coms')
    #     time.sleep(0.25)
    time.sleep(2.5)
    messData = 'lever_press_food'
    coms.send_data(messData)
    print('Sent: ' + messData)

    time.sleep(2.5)
    messData = 'lever_out_door_1'
    coms.send_data(messData)
    print('Sent: ' + messData)

    time.sleep(2.5)
    coms.finish()