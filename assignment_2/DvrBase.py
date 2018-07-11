
import sys
from socket import *
import os
import time
import threading
import copy


def dict_to_list(dv):  # transfer msg to string. The format is element+' '+element. And the head of this string is the node_name of the router.
    telegram = node_name
    for i in dv:
        telegram = telegram + ' ' + str(i)
        for j in range(1, len(dv[i])):
            telegram = telegram + ' ' + str(dv[i][j])
    return telegram


def list_to_dict(msg):# transfer the received msg from string to dictionary.
    temp = msg
    input_dv = dict()
    while len(temp):
        destination = temp.pop(0)
        cost = temp.pop(0)
        port=temp.pop(0)
        input_dv[destination] = int(cost)
    return input_dv# input_dv={ destination: distance;  }


def compare_dv(previous_dv, incoming_dv, incoming_name):#use to compare input_dv and the dv owned by the router itself.
    global node_name
    switch = 0# use switch to detect if its dv is changed or not after the compare.
    for des in incoming_dv:
        if des == node_name:
            continue
        if des not in previous_dv:#if this destination is not in this router's dv, add this destination and the distance into its dv dictionary
            previous_dv[des] = [incoming_name, incoming_dv[des] + previous_dv[incoming_name][1], neighbour[incoming_name][1]]
            switch = 1# and turn on the switch.
        elif previous_dv[des][1] > incoming_dv[des] + previous_dv[incoming_name][1]:#if the distance is smaller than its original distance victor, replace it.
            previous_dv[des] = [incoming_name, incoming_dv[des] + previous_dv[incoming_name][1], neighbour[incoming_name][1]]
            switch = 1## and turn on the switch.
    if switch:
        return previous_dv#if dv has been changed, return new dv,
    else:
        return 0# else return 0


class calculate(threading.Thread):#use to decide how to deal with the incoming msg.
    def __init__(self, msg):
        threading.Thread.__init__(self)
        self.msg = msg

    def run(self):
        global dv
        result=0
        self.msg=str(self.msg, encoding='utf8').split(' ')# transfer to list.
        incoming_name = self.msg.pop(0)# record who sends this msg
        lock.acquire()
        previous_dv = copy.deepcopy(dv)
        lock.release()
        # if node_name in history_msg and history_msg[node_name][0]==self.msg:
        # exit this threading
        if node_name not in history_msg:# renew the active count down if this router has received msgs from this specific router.
            history_msg[incoming_name] = [self.msg, 3]
            incoming_dv = list_to_dict(self.msg)
            print('***TEST***',incoming_dv)
            lock.acquire()
            result = compare_dv(previous_dv, incoming_dv, incoming_name)# use compare to know get the result.
            lock.release()
        elif history_msg[incoming_name][0] != self.msg:# if this is the first time this router received the msg from that router. create a history record.
            history_msg[node_name] = [self.msg, 3]  # this '3' is use for countdown
            incoming_dv = list_to_dict(self.msg)
            lock.acquire()
            result = compare_dv(previous_dv, incoming_dv, incoming_name)# compare the incoming dv with the dv itself.
            lock.release()
        if result:
            lock.acquire()
            dv = result
            lock.release()


class speak(threading.Thread):#use to send msg to all record neighbours.It runs automatically every seconds.
    def __init__(self):
        threading.Thread.__init__(self)

    def run(self):
        i=0
        while 1:
            time.sleep(1)
            i+=1
            lock.acquire()
            leaving_msg = dict_to_list(dv)
            temp_socket = socket(AF_INET, SOCK_DGRAM)
            for node in neighbour:
                temp_socket.sendto(bytes(leaving_msg, encoding='utf8'), ('127.0.0.1', neighbour[node][1]))#the sending msg is srting which contains its node name and distance vector.
            #print('MSG has been sent.')  # test!!!##############################################
            lock.release()
            temp_socket.close()
            if i==5:
                i=0
                lock.acquire()
                #print('Here is {}.'.format(node_name))# test!!!##############################################
                print()
                for node in dv:
                    print('Shortest path to {}: next hop is {} and the cost is {}.'.format(node,dv[node][0],dv[node][1]))#every 5 sec, print its distance vector on the terminal.
                lock.release()


class listen(threading.Thread):#use to receive msg, always open.
    def __init__(self, my_port):
        threading.Thread.__init__(self)
        self.my_port = my_port

    def run(self):
        listen_socket = socket(AF_INET, SOCK_DGRAM)
        listen_socket.bind(('', self.my_port))
        while (1):
            msg, address = listen_socket.recvfrom(2048)
            lock.acquire()
            entering_queue.append(msg)# after it receives msgs, send the msg directly to calculate.
            lock.release()


class destroy(threading.Thread):#use to detect if any nieghbour is missing. this is a timer. BUT IT IS NOT BE USED IN THIS PROGRAM.
    def __init__(self):
        threading.Thread.__init__(self)

    def run(self):
        print('destroy is running!')
        while 1:
            time.sleep(1)
            lock.acquire()
            if len(history_msg):
                print(len(history_msg))
                for node in history_msg:
                    history_msg[node][1] -= 1
                    print('{} : {} times left'.format(node, history_msg[node][1]))
                    print(len(history_msg))
                    if history_msg[node][1] <= 0:
                        print('{} leaves the system'.format(node))
                        nuke(node)
                    break
            lock.release()


def nuke(node): #when detect node missing, prepare to reboot the router. IT IS NOT BE USED IN THIS PROGRAM.
    global emergency
    global neighbour
    global history_msg
    global entering_queue
    lock.acquire()
    history_msg.clear()
    entering_queue.clear()
    if node in neighbour:
        del neighbour[node]
    dv.clear()
    for element in neighbour:
        dv[element] = [element, neighbour[element][0], neighbour[element][1]]
    emergency = 'Prepare to reboot.'
    lock.release()



# starting program with parameters
entering_queue = []  # use to store msg which is going to compare and calculate
neighbour = dict()  # store neighbour nodes information
# neighbour={A:[distance_1,port]}
dv = dict()  # use to store all nodes path
# dv={A:[via_node(neighbours), distance, port#]}
history_msg = dict()  # this is used to record if the neighbour exist or not.
# history_msg={'A' : ['received msg', count_down]}

emergency=''
line = sys.argv
node_name = line[1]
node_port = int(line[2])
file_name = line[3]

with open(file_name) as file:#read neighbours from txt file and transfer information to dictionary
    i = 1
    for line in file:
        if i == 1:
            i+=1
            continue
        else:
            temp = line.strip('\n').split(' ')
            dv[temp[0]] = [temp[0],int(temp[1]), int(temp[2].strip('\r'))]
            neighbour[temp[0]]=[int(temp[1]),int(temp[2].strip('\r'))]
# reading complete

lock = threading.RLock()
my_handsome_ear = listen(node_port)
my_handsome_ear.setDaemon(True)
my_handsome_ear.start()
my_sexy_lip = speak()
my_sexy_lip.start()
print('start working!')#start listen and speak threadings
while 1:
    if len(entering_queue):# if msg coming in, run calculate.
        lock.acquire()
        incoming_msg = entering_queue.pop(0)
        lock.release()
        my_amazing_brain = calculate(incoming_msg)
        my_amazing_brain.start()
