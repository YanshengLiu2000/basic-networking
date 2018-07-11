import sys
import socket
import threading
import time

class listen(threading.Thread):#threading which uses to receive the message from server.
    def __init__(self, socket):
        threading.Thread.__init__(self)
        self.socket = socket

    def stop(self):
        self.thread_stop = True

    def run(self):
        while 1:
            reply = self.socket.recv(2048)
            print('From Server:', bytes.decode(reply))

class speak(threading.Thread):#useless, dont use this part
    def __init__(self, socket):
        threading.Thread.__init__(self)
        self.sokect = socket

    def stop(self):
        self.thread_stop = True

    def run(self):
        while 1:
            time.sleep(0.5)
            sentence = str.encode(input('>'))
            self.sokect.send(sentence)

########################main_part######################################
line = sys.argv
serverName=line[1]
serverPort=int(line[2])

while 1:#login function part.
    clientSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    clientSocket.connect((serverName, serverPort))
    print('Please input your user name and keyword: ')
    user_name = str(input('User name: '))
    pass_word = str(input('Keyword: '))#after collect both password and username, combine them to a string and send it to server.
    sentence = str.encode(user_name + ' ' + pass_word)
    clientSocket.send(sentence)
    reply = clientSocket.recv(2048)#try to get recieve msg from server.
    sentence = bytes.decode(reply)
    print('<PUBLIC CHANNEL> ', sentence)
    if sentence == 'Welcome back, ' + user_name:
        break
    print()
    time.sleep(1)
# my_handsome_ear = listen(clientSocket)
my_sexy_lip = speak(clientSocket)#create a threading to receive the message
# my_handsome_ear.start()
my_sexy_lip.setDaemon(True)#this threading will end when main program will be closed.
my_sexy_lip.start()
while 1:
    reply = clientSocket.recv(2048)
    sentence = bytes.decode(reply)
    print('<PUBLIC CHANNEL> ', sentence)
    if sentence == 'Already logout Long may the sunshine!':
        break
    elif sentence == 'The world dont need hero. This world need professionals.YOU DIED.':#use for long time unactive online
        clientSocket.send(str.encode(sentence))
        break
    elif sentence == 'But you are already online.Fail log in twice.':
        break