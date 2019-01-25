#!/usr/bin/env python

# this file should not be used it is an example of a phone client

import socket, time, threading

broadcast = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
broadcast.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)

com = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
com.bind(('',242*106))

def listen_for_resp():
    global com
    while True:
        msg = com.recvfrom(1024)
        if msg[0] != b"~Hello Ping": # check this is not us
            print(str(msg[1][0]) + ": " + str(msg[0]))

thr = threading.Thread(target=listen_for_resp, args=(), kwargs={})

def send_broadcast():
    global thr
    global broadcast
    while True:
        broadcast.sendto(
            b"~Hello Ping",
            ('255.255.255.255',242*106)
        )
        time.sleep(2)
        print("sent!")

thr.daemon = True
thr.start()
send_broadcast()
