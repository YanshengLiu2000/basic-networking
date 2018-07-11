import sys
import socket
import os
import time
import threading
import re


class subserver(threading.Thread):#  when a user logs in, main program will create a subserver class.
    def __init__(self, private_socket, private_addr, user_name, sub_block_list):
        threading.Thread.__init__(self)
        self.private_socket = private_socket
        self.private_addr = private_addr
        self.user_name = user_name
        self.sub_block_list = sub_block_list[:]

    def run(self):
        global lock
        insight = shout(self.user_name + ' log in')#use class shout to tell people im coming.
        insight.start()
        find_msg = checkmailbox(self.private_socket, self.user_name)
        find_msg.start()#check offline mailbox and find if there is message
        while 1:
            sentence = bytes.decode(self.private_socket.recv(2048))
            lock.acquire()#handle the threading lock
            try:
                if sentence == 'logout':  # logout function
                    sentence = 'Already logout Long may the sunshine!'
                    break
                elif sentence == 'whoelse':  # whoelse function
                    sentence = ''
                    active_label[self.user_name] = time.time()#if user actives, renew the active label.
                    for key in online_list:
                        if key==self.user_name:
                            continue
                        sentence = sentence + str(key) + ', '#get online list at current time.
                    reply = str.encode(sentence)
                    self.private_socket.send(reply)
                elif re.match('whoelse<(.*)>', sentence):  # whoelse<time> function
                    active_label[self.user_name] = time.time()#if user actives, renew the active label.
                    matchobj = re.match('whoelse<(.*)>', sentence)#get how long ago
                    timing = time.time() - float(matchobj.group(1))#get real point-in-time
                    sentence = ''
                    for key in history_user:
                        if key==self.user_name:#deletle user himself/herself
                            continue
                        for keytime in history_user[key]:
                            if keytime >= timing:#if history label is less than the input point in time, push the username into the string.
                                sentence = sentence + ', ' + key
                                break
                    if sentence == '':
                        sentence = 'There is none here before this time peroid.'#if there is none in the string, print the following sentence.
                    reply = str.encode(sentence)
                    self.private_socket.send(reply)
                elif re.match('block<(.*)>', sentence):  # block<someone> function
                    active_label[self.user_name] = time.time()#if user actives, renew the active label.
                    matchobj = re.match('block<(.*)>', sentence)
                    sentence = matchobj.group(1)
                    if sentence not in box or sentence == self.user_name:
                        sentence = 'ERROR: invalid behaviour, may caused by invalid user name or block yourself.'#if someone wanna block themselves or an unreal user
                    else:
                        if sentence in self.sub_block_list:
                            sentence = 'ERROR: Already blocked.'#if someone wanna block a person who has already in their block lists.
                        else:
                            block_list[self.user_name].append(sentence)
                            self.sub_block_list.append(sentence)
                            sentence = 'Block successful.'#else, block succeed.
                    reply = str.encode(sentence)
                    self.private_socket.send(reply)#send message
                elif re.match('unblock<(.*)>', sentence):  # unblock<someone> function
                    active_label[self.user_name] = time.time()#renew the active label
                    matchobj = re.match('unblock<(.*)>', sentence)
                    sentence = matchobj.group(1)
                    if sentence not in box:
                        sentence = 'ERROR: Invalid user name.'
                    elif sentence not in self.sub_block_list:
                        sentence = 'ERROR: This user is not in your block list.'#someone try to unblock a person who hasnt in their block lists.
                    else:
                        block_list[self.user_name].remove(sentence)
                        self.sub_block_list.remove(sentence)
                        sentence = 'This user is removed out of your block list.'#unblock succeed.
                    reply = str.encode(sentence)
                    self.private_socket.send(reply)
                elif re.match('broadcast<(.*)>', sentence):
                    active_label[self.user_name] = time.time()#renew active label
                    matchobj = re.match('broadcast<(.*)>', sentence)#catch the radio sentence
                    sentence = '<Big Foot World Channel> < ' + self.user_name + ' >' + matchobj.group(1)
                    reply = str.encode(sentence)
                    for key in online_list:
                        if self.user_name not in block_list[key]:
                            online_list[key][0].send(reply)#send the message to whoever online.
                elif re.match('message<(.*)><(.*)>', sentence):# send message to particular person no matter if he/she online or not.
                    active_label[self.user_name] = time.time()#renew active label
                    matchobj = re.match('message<(.*)><(.*)>', sentence)
                    aim = matchobj.group(1)#get who need the message.
                    sentence = 'From '+'<'+aim+'>'+' : '+ matchobj.group(2)# construct the message.
                    if aim not in box:
                        sentence = 'ERROR: user not exists.'#someone try to send message to a no-exist user.
                        reply = str.encode(sentence)
                        self.private_socket.send(reply)
                    elif aim in self.sub_block_list:
                        sentence = 'ALERT: you have blocked this user. Can not send message. '#someone try to send message to a user who he/she has already blocked.
                        reply = str.encode(sentence)
                        self.private_socket.send(reply)
                    else:
                        if self.user_name not in block_list[aim]:
                            if aim in online_list:
                                reply = str.encode(sentence)
                                online_list[aim][0].send(reply)#send message to particular user if he/she is online.
                            else:
                                offline_mail_box[aim].append(matchobj.group())#send message to particular user if he/she is offline.
                elif sentence == 'The world dont need hero. This world need professionals.YOU DIED.':#dont do anything for a long time, prepare to log out.
                    break
                else:
                    sentence='ALERT: Wrong command, try again.'# if receive wrong command, reply this one.
                    reply = str.encode(sentence)
                    self.private_socket.send(reply)
            finally:
                lock.release()#release the threading lock

                print(self.user_name+' exit.')
        del online_list[self.user_name]
        insight = shout(self.user_name + ' log out')
        insight.start()#tell all online users i wanna logout.
        reply = str.encode(sentence)
        self.private_socket.send(reply)#send the message to client and prepare to exit.
        self.private_socket.close()


class shout(threading.Thread):#use to tell all online users im logging in or logging out.
    def __init__(self, sentence):
        threading.Thread.__init__(self)
        self.sentence = sentence

    def run(self):
        global lock
        lock.acquire()
        try:
            for key in online_list:
                reply = str.encode(self.sentence)
                online_list[key][0].send(reply)
        finally:
            lock.release()

    def stop(self):
        self.thread_stop = True


class checkmailbox(threading.Thread):#use to keep message if someone is not online at that time and send all offline message when he/ she login immediately.
    def __init__(self, private_socket, user_name):
        threading.Thread.__init__(self)
        self.private_socket = private_socket
        self.user_name = user_name

    def run(self):
        global lock
        lock.acquire()
        try:
            if len(offline_mail_box[self.user_name]):
                offline_mail_box[self.user_name].reverse()
                while len(offline_mail_box[self.user_name]):
                    msg = offline_mail_box[self.user_name].pop()
                    matchobj = re.match('message<(.*)><(.*)>', msg)
                    sentence = matchobj.group(1) + ' : ' + matchobj.group(2)
                    reply = str.encode(sentence)
                    self.private_socket.send(reply)
        finally:
            lock.release()

    def stop(self):
        self.thread_stop = True

class timerdown(threading.Thread):#timer, uses to monitor and remove long unactive online user. check once every timeout/10.0 seconds.
    def __init__(self, timeout):#start when server is running.
        threading.Thread.__init__(self)
        self.timerdown = timeout

    def run(self):
        global lock
        print('Crusader start processing.')
        self.timerdown = float(self.timerdown)
        number_ten=10.0
        check_period = self.timerdown/number_ten
        #lock.acquire()#dont know why, but if i add this, error occured.
        try:
            while 1:
                time.sleep(check_period)
                for key in active_label:
                    if time.time() - active_label[key] > self.timerdown:
                        print('Crusader is coming!!!!!!!!!!!!!!!!!.')
                        del active_label[key]
                        online_list[key][0].send(
                            str.encode('The world dont need hero. This world need professionals.YOU DIED.'))
                        break
        finally:
            print()
            #lock.release()


line = sys.argv
port = int(line[1])
block_duration = int(line[2])
timeout = int(line[3])

black_user_box = dict()  # key: user_name value: current time
black_ip_box=dict()#key: IP value: current time
box = dict()  # key: user_name value: password
login_count = dict()  # key: user_name  value: times
online_list = dict()  # key:user_name value:[socket,IP]#
subserver_list = []  # element=[user name, subserving]
history_user = dict()  # key: user_name value: [time,time]
active_label = dict()  # key: user_name value: time
ip_count=dict() # key:IP addr value: times
with open('credentials.txt') as file:#read and record all username and password pairs into the dictionary(box)
    for line in file:
        user_name, pass_word = line.strip('\n').split(' ')
        box[user_name] = pass_word.strip('\r')

block_list = {key: [] for key in box}  # list of key[]=[blocked user]
offline_mail_box = {key: [] for key in box}  # key: user_name value:['msg1','msg2']
timer = timerdown(timeout)
timer.setDaemon(True)#end this threading when server ends.
timer.start()#timer start
lock = threading.RLock()#build a threading lock.
serverPort = port
serverSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
serverSocket.bind(('', serverPort))
serverSocket.listen(5) # maybe there is one time all 5 users wanna login at the same time.

while 1:#always open the welcome socket for someone who wanna login.
    connectionSocket, addr = serverSocket.accept()
    sentence = bytes.decode(connectionSocket.recv(2048))
    user_name, pass_word = sentence.split(' ')#transfer the sentence to username and passowrd
    if user_name in black_user_box :#if users are in block list, dont allow them to login and close the socket.
        if time.time() - black_user_box[user_name] < block_duration:
            sentence = 'you are blocked, plz wait.'
            reply = str.encode(sentence)
            connectionSocket.send(reply)
            connectionSocket.close()
            continue
        else:#check time and decide if remove this user from the black user box.
            del black_user_box[user_name]
            del login_count[user_name]
    if addr[0] in black_ip_box:#check if the IP is blocked or not.
        if time.time()-black_ip_box[addr[0]]< block_duration:
            sentence = 'you are blocked, plz wait.'
            reply = str.encode(sentence)
            connectionSocket.send(reply)
            connectionSocket.close()# if this IP is blocked, reject the connection
            continue
        else:
            del black_ip_box[addr[0]]
            del login_count[addr[0]]

    if user_name in box:
        if box[user_name] == pass_word:# if user name in box and password is correct, try to log in the system and start its own subserver
            if user_name in online_list:
                if addr[0] not in ip_count:
                    ip_count[addr[0]]=1
                    sentence = 'But you are already online.Fail logging in.'# if someone have already logged in, reject the login and close the socket.
                else:
                    ip_count[addr[0]]+=1
                    sentence = 'But you are already online.Fail logging in.'

                if ip_count[addr[0]]==3:
                    ip_count=0
                    black_ip_box[addr[0]]=time.time()
                    sentence='Your IP is blocked, please try again after '+str(block_duration)+' seconds.'# if someone still try to log in, block their IP addresses.
                reply = str.encode(sentence)
                connectionSocket.send(reply)
                connectionSocket.close()
            else:
                reply = str.encode('Welcome back, ' + str(user_name))# for someone who logs in successful.
                connectionSocket.send(reply)
                online_list[user_name] = [connectionSocket, addr]
                print(user_name+' online.')
                active_label[user_name] = time.time()
                if user_name in history_user:
                    history_user[user_name].append(time.time())
                else:
                    history_user[user_name] = [time.time()]#record login time for whoelse<>.
                subserver_list.append([user_name, subserver(connectionSocket, addr, user_name, block_list[user_name])])
                subserver_list[-1][-1].start()#create a sbuserver and launch it.

        else:
            if user_name in login_count:#for someone who input uncorrect password
                if login_count[user_name] == 2:
                    black_user_box[user_name] = time.time()
                    sentence = 'You have been blocked. Plz try again after ' + str(block_duration) + ' seconds.'
                    reply = str.encode(sentence)
                else:
                    login_count[user_name] += 1
                    sentence = 'not correct user_name or pass word, ' + str(
                        3 - login_count[user_name]) + ' times remain.'
                    reply = str.encode(sentence)
            else:
                login_count[user_name] = 1
                sentence = 'not correct user_name or pass word, 2 times remain.'
                reply = str.encode(sentence)
            connectionSocket.send(reply)
            connectionSocket.close()#for uncorrect username and password pairs close socket directly.
