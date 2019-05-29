#!/usr/bin/python3
import smtplib
import netifaces as ni
from string import Template
import socket
import time
addresses = []

from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

'''cribbed from https://medium.freecodecamp.org/send-emails-using-code-4fcea9df63f '''

MY_ADDRESS = 'protter.raspberry.pi.shop@gmail.com'
PASSWORD = 'vole!love'

def get_contacts(filename):
    """
    Return two lists names, emails containing names and email addresses
    read from a file specified by filename.
    """

    names = []
    emails = []
    with open(filename, mode='r', encoding='utf-8') as contacts_file:
        for a_contact in contacts_file:
            names.append(a_contact.split()[0])
            emails.append(a_contact.split()[1])
    return names, emails


def main():
    #names, emails = get_contacts('mycontacts.txt') # read contacts
    names = ['Dave']
    emails = ['david.protter@Gmail.com', 'mapa2020@colorado.edu']

    success = False
    start = time.time()
    # set up the SMTP server
    while not success and time.time()-start <20:
        try:
            s = smtplib.SMTP(host= 'smtp.gmail.com', port=587)
            success = True
        except:
            success = False

    if not success:
        print('couldnt establish a connection')
        raise
    else:
        print('success')

    for inter in ni.interfaces():
        print(inter)
        if ni.AF_INET in ni.ifaddresses(inter):
            addresses.append([inter, ni.ifaddresses(inter)[ni.AF_INET]])
        else:
            addresses.append([inter, 'not connected'])

    s.starttls()
    s.login(MY_ADDRESS, PASSWORD)

    # For each contact, send the email:
    for name, email in zip(names, emails):
        msg = MIMEMultipart()       # create a message

        message = ''
        for line in addresses:
            message += str(line) +'\n'

        # setup the parameters of the message
        msg['From']=MY_ADDRESS
        msg['To']=email
        msg['Subject']="%s IP"%socket.gethostname()

        # add in the message body
        msg.attach(MIMEText(message, 'plain'))

        # send the message via the server set up earlier.
        s.send_message(msg)
        del msg

    # Terminate the SMTP session and close the connection
    s.quit()

if __name__ == '__main__':
    main()
