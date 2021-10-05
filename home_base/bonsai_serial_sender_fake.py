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
        self.finished = False
        self.active = False
        print('initializing fake sender')


    def start(self):
        pass

    def busy(self):
        return self.sending

    def shutdown(self):
        self.finished = True

    def running(self):
        return self.active

    def run(self):
        pass

    def send_data(self, command):
        print(f'{command} ---> outbound')
     

    
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

    print('this is a fake sender')