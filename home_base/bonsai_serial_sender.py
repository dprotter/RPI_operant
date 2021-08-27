# Imports
import serial as ser
import time
#import RPi.GPIO as gpio 
import pandas as pd
import queue
import atexit
import threading
# Sender class
class sender(threading.Thread):
    # SENDER is the object that sends information to Bonsai which includes timestamps and information on what event has occured. The arduino will take the serial commands and turn them into the correct signals for Bonsai.
    # INPUTS: port (str) - path of the serial port to connect to, defaults to GPIO serial of the pi
    #         baud (int) - Baud rate that the serial port runs on (default 9600 to match arduino)
    #         commandFile (str) - path of the commands.csv file where the commands are located

    def __init__(self, port = '/dev/serial0', baud = 9600, commandFile = '~/RPI_operant/home_base/bonsai_commands.csv'):
        # Set the initial properties
        print('initializing sender')
        super().__init__()
        self.finished = False
        self.sending = False
        self.active = True
        self.port        = port
        self.baudRate    = baud
        self.history     = queue.Queue()
        self.commandFile = commandFile
        self.command_stack = queue.Queue()
        # Initialize the port
        self.ser = ser.Serial(self.port, self.baudRate)
        self.command_dict = self.get_commands() # Assign the commands property
    
    def busy(self):
        return self.sending

    def finish(self):
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
            
        self.sending = False
    
    def get_commands(self):
        # GET_COMMANDS gets the list of possible command names from a previously defined file in csv format. 

        commDict = pd.read_csv(self.commandFile, index_col=0).to_dict('index')
        return commDict

