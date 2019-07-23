#!/usr/bin/python3
import smtplib
import netifaces as ni
from string import Template
import socket
import time
import os
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders

MY_ADDRESS = 'protter.raspberry.pi.shop@gmail.com'
PASSWORD = 'vole!love'

def email_push(user):
    os.chdir('/home/pi/Operant_Output/')
    user = user.lower()

    #names, emails = get_contacts('mycontacts.txt') # read contacts
    users = {'dave':'david.protter@gmail.com', 'maya':'mapa2020@colorado.edu'}

    if user not in users:
        print('the user %s doesnt exist, sending to Dave instead'%user)

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
        print('successfully opened email connection')


    s.starttls()
    s.login(MY_ADDRESS, PASSWORD)

    # For each contact, send the email:
    msg = MIMEMultipart() #create a message

    # setup the parameters of the message
    msg['From']=MY_ADDRESS
    msg['To']=users[user]
    msg['Subject']= 'vole operant data! from %s'%socket.gethostname()


    for filename in os.listdir(os.getcwd()):
        path = os.path.join(os.getcwd(), filename)
        if not os.path.isfile(path) or not 'fresh' in filename:

            continue
        with open(path, 'r') as fp:
            print('attaching: ')
            print(path)
            part = MIMEBase('application', "octet-stream")
            part.set_payload(open(path, "r").read())
            encoders.encode_base64(part)
            part.add_header('Content-Disposition', 'attachment', filename=filename)  # or
            # part.add_header('Content-Disposition', 'attachment; filename="attachthisfile.csv"')
            msg.attach(part)
        new_name = filename.replace('_fresh','')
        os.rename(filename, new_name)
    # send the message via the server set up earlier.
    s.send_message(msg)
    del msg

    # Terminate the SMTP session and close the connection
    s.quit()

if __name__ == '__main__':
    email_push(user = 'dave')
