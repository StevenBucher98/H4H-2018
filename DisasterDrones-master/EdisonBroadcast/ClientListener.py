import socket, threading

mutex = threading.Lock()

f = open("message.txt", "r")
static_reply = ''.join(f.readlines())
f.close()

def listen_clients():
    global mutex
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.bind(('',242*106))
    while True:
        data = s.recvfrom(1024)
        msg = data[0].decode('ascii')
        if msg == "Ping":
            print("hit")
            reply = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            reply.sendto(
                str.encode("~" + static_reply),
                (data[1][0],242*106)
            )
            reply.close()
        else:
            mutex.acquire()
            recv_data = open('data_file.dat','a+')
            recv_data.write(msg + "\n")
            recv_data.close()
            mutex.release()

def listen_drones():
    global mutex
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.bind(('',(242*106)^(1337)))
    while True:
        data = s.recvfrom(1024)
        msg = data[0].decode('ascii')
        if msg == "Req Dump":
            print("Data request")
            reply = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            recv_data = open('data_file.dat','r')
            reply.sendto(
                str.encode("~" + ''.join(recv_data.readlines())),
                (data[1][0],(242*106)^(1337))
            )
            recv_data.close()
            reply.close()
        elif msg[0] == '~':
            print("Got dump:", msg)
            mutex.acquire()
            # here we assume that the data will not be requested again so
            # we can commit it to file
            recv_data = open('data_file.dat','a+')
            recv_data.write(msg + "\n")
            recv_data.close()
            mutex.release()


thr = threading.Thread(target=listen_drones, args=(), kwargs={})
thr.daemon = True
thr.start()
print("listening!")
listen_clients()