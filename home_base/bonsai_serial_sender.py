# Imports
import serial as ser
import time
#import RPi.GPIO as gpio 
import pandas as pd
import queue
import atexit
import threading
# Sender class
class sender():
    # SENDER is the object that sends information to Bonsai which includes timestamps and information on what event has occured. The arduino will take the serial commands and turn them into the correct signals for Bonsai.
    # INPUTS: port (str) - path of the serial port to connect to, defaults to GPIO serial of the pi
    #         baud (int) - Baud rate that the serial port runs on (default 9600 to match arduino)
    #         commandFile (str) - path of the commands.csv file where the commands are located

    def __init__(self, port = '/dev/serial0', baud = 9600, commandFile = '~/RPI_operant/home_base/bonsai_commands.csv'):
        # Set the initial properties
        print('initializing sender')
        self.finished = False
        self.sending = False
        
        self.port        = port
        self.baudRate    = baud
        self.history     = queue.Queue()
        self.commandFile = commandFile
        self.command_stack = queue.Queue()
        self.timeout = 2
        # Initialize the port
        try:
            self.ser = ser.Serial(self.port, self.baudRate)
            self.command_dict = self.get_commands() # Assign the commands property

            start = time.time() 
            self.send_data('startup_test')
            
            while self.sending and time.time() - start < self.timeout:
                time.sleep(0.05)
            finished = time.time()
            if finished - start > self.timeout:
                print('serial sender failed to send test message ')
        except:
            print('serial sender failed setup. If not sending serial data for Bonsai integration, ignore this warning.')
        
        self.active = True

    def start(self):
        wrt = threading.Thread(target = self.run, daemon = True)
        wrt.start()

    def busy(self):
        return self.sending

    def shutdown(self):
        self.finished = True

    def running(self):
        return self.active

    def run(self):
        while not self.finished:
            
            if not self.command_stack.empty():
                command = self.command_stack.get()
                
                self._send_data(command)
                
            time.sleep(0.05)

        while not self.command_stack.empty():
            
            command = self.command_stack.get()
            self._send_data(command)
            self.sleep(0.05)
        self.active = False

    def send_data(self, command):
        self.command_stack.put(command)
     


    def _send_data(self, command):
        # SEND_DATA sends the data through the associated serial port, and then logs all the commands that have been send to the self.history queue object.
        self.sending = True
        if not command in self.command_dict.keys():
            print(f'WARNING: "{command}" is not a valid command being sent, will not be read by the Arduino and Bonsai')
            print(self.command_dict.keys())
            return 
        elif not self.command_dict[command]['send to bonsai']:
            print(f'WARNING: command {command} was passed to the serial encoder, but attribute "send to bonsai" is FALSE. This will not be sent off the pi.') 
            return
        else:
            formatted = command + '\r'
            formatted = formatted.encode('ascii')
            
            self.ser.write(formatted)
        print(f'\n\nserial message sent: {command}\n\n')
        self.sending = False
    
    def get_commands(self):
        # GET_COMMANDS gets the list of possible command names from a previously defined file in csv format. 

        commDict = pd.read_csv(self.commandFile, index_col=0).to_dict('index')
        return commDict

#---------------------------------------------------------------------------------------------------
# FOR TESTING THE SCRIPT:
""" 
This test simply runs this file on a raspberry pi computer using the /dev/serial0 serial port as a
default. The pi is then connected to the arduino through the GPIO serial pins TX and RX, so that 
the arduino reads commands through the serial port of the pi. The arduino is set up to process the
commands listed in the commands.csv file ONLY so any commands issued other than those will not do
anything. 
"""
#---------------------------------------------------------------------------------------------------
if __name__ == "__main__":

    # Initialize the object
    obj = sender()
    obj.start()

    # Print info to terminal
    print('Starting Flash...')
    print('Port: ' + obj.port)

    # Endlessly send the same command to test
    while True:
        data = "lever_out_door_1"
        obj.send_data(data)
        print('Sent Command: ' + data)
        time.sleep(3) # Pause for ease of reading and to test the log

