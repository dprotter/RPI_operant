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