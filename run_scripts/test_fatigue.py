""" 
Date Created : 9/7/2021
Date Modified: 9/7/2021
Author: Ryan Cameron, David Protter, Sarah ???
Description: This script runs fatigue tests on the operant cage to make sure that it can run over and over again without complications. Specifically, this script test the capability of the doors to extend and retract without fail, and for the levers to extend and retract without fail. As a measure of this, the script outputs a log file detailing how long it took the doors to fully close.
Property of Donaldson Lab, University of Colorado Boulder, PI Zoe Donaldson
http://www.zdonaldsonlab.com/
Code located at - https://github.com/donaldsonlab/Operant-Cage 
"""

# Imports
import time
import numpy as np
import sys
sys.path.append('/home/pi/')

import RPI_operant.home_base.functions as FN
fn = FN.runtime_functions()

# Classes
class fatigue:
    # FATIGUE is the overall class that contains everything needed to run a fatigue test on a certain object. It takes in an object that is representative of a physical component and runs that object through test n number of times to ensure that it can hold up over time. 
    def __init__(self, log = False, object = None, n = 500, runnable = None, args = None):
        self.extractLog = log
        self.component = object
        self.runnable = runnable # This is the function that will be run over and over
        self.args = args # List of arguments that the function needs
        self.N = n

    def begin(self):
        # BEGIN is the main function of this class that begins the fatigue test organizes all of the results.
        print('Beginning Fatigue Test...')

        # Run the loop
        for iN in range(self.N): 
            # Loops through N times
            # Run the function that needs to be run
            print('hmmmmmm')

# Test run
if __name__ == "__main__":
    # If this is the file that is being run directly, run the test code
    run = True
    # While loop to make sure the user enters the correct info
    while run:
        testType = input("What is the type of test to run (1. Doors, 2. Levers: ")
        testType.lower()
        # Run the correct test
        if testType == "doors":
            print('Starting Doors Fatigue Test...')
            # Make sure doors are closed
            print('Closing Doors...')
            fn.reset_chamber()
            print('Chamber ready to test')

            # Fatigue Test
            n = 100
            for iRun in range(n): # Loop through n times
                # Open Door 1
                fn.open_door(door_ID='door_1')
                time.sleep(1)
                # Close Door
                fn.close_doors(door_ID='door_1')

                # Open Door 2
                fn.open_door(door_ID='door_2')
                time.sleep(1)
                # Close Door
                fn.close_door(door_ID='door_2')
            
            # Stop the script
            print('Test Complete')
            run = False

        elif testType == "levers":
            print('Starting Levers Fatigue Test...')

             # Stop the script
            print('Test Complete')
            run = False

        else:
            # No match on the user input
            print('WARNING: INVALID TEST TYPE, PLEASE RE-ENTER OR EXIT')
            userChoice = input('Would you like to retry (y/n): ')
            if userChoice == 'y':
                run = True
            elif userChoice == 'n':
                run = False
            else:
                print('ERROR: INVALID CHOICE, STOPPING SCRIPT')