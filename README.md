# RPI_operant
Raspberry Pi and python based operant

1. Use etcher to flash an SD card with the OS.
2. use setup wizard as normal. Set a new password. Enable SSH, enable I2C, and so forth
3. change the hostname to something informative. This name will be in the header of the email you receive (IE operant_pi_1, operant_pi_2, etc)
    1. edit /etc/hostname
        1. sudo nano /etc/hostname
    2. edit /etc/hosts
        1. sudo nano /etc/hosts
4. clone the RPI_operant repository
    1. git clone “https://github.com/dprotter/RPI_operant"
5. install dependencies by running setup.py
    1. sudo python3 setup.py install
6. duplicate the operant cage settings default file to a secure location on the pi
    1. sudo cp RPI_operant/home_base/operant_cage_settings_defaults.py /etc/RPI_operant/operant_cage_settings_local.py

## Setting up Bonsai
To set up Bonsai on the PC there are a few things that should be noted. 

1. First, the necessary packages that need to be installed through Bonsai can be found in the package manager in the PC app. They are:
    * Arduino Library
2. In the Arduino Analog Input node, make sure the port is set to whatever port the Arduino is connected to through a USB B cable. This can be found by opening the Device Manager on the PC and checking the Ports options. One of them should be listed as an Arduino Uno.
3. In the CSV Writer node, there should be a specified file path that it writes to. This should be set to wherever you want to file to be saved on the PC Bonsai is installed in. 
    * After each run of the Bonsai script, make sure that you run the *csv_parser.py* file found in *Operant-Cage/Software/Bonsai-Out*. This replaces the numbered values that Bonsai reads with the correct event labels found in the *bonsai_commands.csv* file. 
    * Once you run the file through, copy that data file into a new directory and then delete the original file. The Bonsai script will not run if there is a file of the same name as specified in the CSV Writer node in the Bonsai script.
4. When starting the Bonsai script, it will automatically re-initialize the Arduino. So, you should wait 5-10 seconds until the Arduino script is initialized and running before you start whatever Python file to run on the Pi (*Door_shape*, *Magazine*, *Autoshape*, etc...).