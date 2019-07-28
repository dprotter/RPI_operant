# RPI_operant
Raspberry Pi and python based operant

Setting up a new pi!
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
6. tell git to ignore the local settings file
    1. git update-index --assume-unchanged operant_cage_settings.py
7. get pi to email you it's IP! edit the /etc/profile
    1.  sudo nano /etc/profile
    2.  add line the following line at the bottom of the doc
        1. sudo python3 /home/pi/RPI_operant/Send_IP.py
