for x in range(8):
    t = threading.Thread(target = thread_distributor)
    t.daemon = True
    t.start()
    print("started %i"%x )


### master looper ###
for i in range(loops):
    round_start = time.time()
    round = i
    print("#-#-#-#-#-# new round #%i!!!-#-#-#-#-#"%i)
    timestamp_queue.put('%i, Starting new round, %f'%(round, time.time()-start_time))
    do_stuff_queue.put(('start tone',))

    #wait till tone is done
    do_stuff_queue.join()

    do_stuff_queue.put(('extend lever',
                        ('food',lever_angles['food'][0],lever_angles['food'][1])))

    #wait till levers are out before we do anything else. Depending on how
    #fast the voles react to the lever, we may start monitoring before it is
    #actually out.
    do_stuff_queue.join()

    #begin tracking the lever in a thread
    do_stuff_queue.put(('monitor lever', (lever_press_queue, 'food',)))

    timeII_start = time.time()

    #for the timeII interval, monitor lever and overide pellet timing if pressed
    while time.time() - timeII_start < timeII:
        #eventually, here we will call threads to monitor
        #vole position and the levers. here its just random
        if not interrupt and not lever_press_queue.empty():
            interrupt = True
            lever_ID = lever_press_queue.get()
            print('the %s lever was pressed! woweeeee'%lever_ID)
            timestamp_queue.put('%i, a lever was pressed! woweeeee, %f'%(round, time.time()-start_time))
            do_stuff_queue.put(('pellet tone',))
            do_stuff_queue.put(('dispence pellet',))
            do_stuff_queue.join()
        time.sleep(0.05)

    #waited the interval for timeII, nothing happened
    if not interrupt:
        print('the vole is dumb and didnt press a lever')
        timestamp_queue.put('%i, no lever press, %f'%(round, time.time()-start_time))
        do_stuff_queue.put(('pellet tone',))
        do_stuff_queue.put(('dispence pellet',))
        time.sleep(0.05)
        do_stuff_queue.join()

    time.sleep(0.05)

    do_stuff_queue.put(('retract lever',
                        ('food', lever_angles['food'][0],lever_angles['food'][1])))

    time.sleep(timeIV)
    print('entering ITI for #-#-# round #%i -#-#-# '%i )

    #wait for ITI to pass

    '''a good time to write some stuff to file'''
    with open(path, 'a') as csv_file:
        csv_writer = csv.writer(csv_file)
        while time.time() - round_start < round_time:
            if not timestamp_queue.empty():
                line = timestamp_queue.get().split(',')
                print('writing ###### %s'%line)
                csv_writer.writerow(line)
            time.sleep(0.01)
    #reset our global values interrupt and monitor. This will turn off the lever
    #if it is still being monitored. This resets the inerrupt value for the next
    #loop of the training.
    interrupt = False
    monitor = False

'''append current timestamp queue contents to csv file'''
with open(path, 'a') as file:
    writer = csv.writer(file, delimiter = ',')
    while not timestamp_queue.empty():
        line = timestamp_queue.get().split(',')
        writer.writerow(line)

if pellet_state:
    timestamp_queue.put('%i, final pellet not retrieved, %f'%(round, time.time()-start_time))
print("all Done")
#reset levers to retracted
servo_dict['food'].angle = lever_angles['food'][0]
servo_dict['social'].angle = lever_angles['social'][0]
servo_dict['door'].throttle = continuous_servo_speeds['door']['stop']
servo_dict['dispense_pellet'].throttle = continuous_servo_speeds['dispense_pellet']['stop']

if 'y' in push.lower():
    email_push.email_push(user = user)
