""" 
Date Created : 8/5/2021
Date Modified: 8/9/2021
Author: Ryan Cameron, David Protter, Sarah ???
Description: This is the script that has all of the interactable objects for the vole
Property of Donaldson Lab, University of Colorado Boulder, PI Zoe Donaldson
http://www.zdonaldsonlab.com/
Code located at - https://github.com/donaldsonlab/Operant-Cage 
"""
# Imports
import serial as ser
import time
#import RPi.GPIO as gpio 
import pandas as pd
import queue
import atexit

# Sender class
class sender:
    # SENDER is the object that sends information to Bonsai which includes timestamps and information on what event has occured. The arduino will take the serial commands and turn them into the correct signals for Bonsai.
    # INPUTS: port (str) - path of the serial port to connect to, defaults to GPIO serial of the pi
    #         baud (int) - Baud rate that the serial port runs on (default 9600 to match arduino)
    #         commandFile (str) - path of the commands.csv file where the commands are located

    def __init__(self, port = '/dev/serial0', baud = 9600, commandFile = 'simulation/commands.csv'):
        # Set the initial properties
        self.port        = port
        self.baudRate    = baud
        self.data        = None
        self.history     = queue.Queue()
        self.commandFile = commandFile

        # Initialize the port
        self.ser = ser.Serial(self.port, self.baudRate)
        self.get_commands() # Assign the commands property

    def send_data(self):
        # SEND_DATA sends the data through the associated serial port, and then logs all the commands that have been send to the self.history queue object.
        formatted = self.data + "\r"
        formatted = formatted.encode('ascii')
        self.ser.write(formatted)

        # Add a timestamp to the command
        nowTime = time.asctime(time.localtime())
        # Add the command to the queue
        queueData = self.data + ',' + nowTime
        self.history.put(queueData)
        self.history.task_done()

    def get_data(self, command):
        # GET_DATA gets the data needed from the associated software, in form of a command string. The command must match one of the possible command sequences outlined in the commands.csv file
        # INPUTS: command (str) - the command string that should be sent. 

        # Search for the command in the list of possible commands
        try:
            description = self.commands[command]
        except ValueError:
            print('WARNING: Not a valid command being sent, will not be read by the Arduino and Bonsai')
            return 
        
        # Set the data as the command to send
        self.data = command
    
    def get_commands(self):
        # GET_COMMANDS gets the list of possible command names from a previously defined file in csv format. 

        commDict = pd.read_csv(self.commandFile, index_col=0, header = None, squeeze=True).to_dict()
        self.commands = commDict

    def print_history(self):
        # PRINT_HISTORY prints all the items in the queue with their timestamps to a log file just for reference. The log file is located in whatever the main directory you are running is and is called commandLog.txt
        
        # Indicate the beginning of the log procees
        print('Beginning writing commands to log...')
        # Get amount of objects in the queue
        numObjs = self.history.qsize()
        # Open the file and write each command to it as its only line
        fileID = open("commandLog.txt","w") # Opens file as write only to override any previous data
        lines = []
        for iComm in range(numObjs): # Loop through the queue objects and write them to a text file
            lines = lines + [self.history.get() + '\r\n']

        # Finish
        fileID.writelines(lines)
        fileID.close()
        print('Commands Logged')

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
    atexit.register(obj.print_history)

    # Print info to terminal
    print('Starting Flash...')
    print('Port: ' + obj.port)

    # Endlessly send the same command to test
    while True:
        obj.data = "leverOutFood"
        obj.send_data()
        print('Sent Command: ' + obj.data)
        time.sleep(2) # Pause for ease of reading and to test the log


