import socket
import select
import traceback
import sys

addr = ('127.0.0.1', 3000)
clientSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

try:
    clientSocket.connect(addr)

except:
    traceback.print_exc()
    print("An error occurred while opening the server.")

rlist = [clientSocket, sys.stdin]

while True:
    R,W,X = select.select(rlist, [], [], 50)

    for r in R:
        if r==sys.stdin:
            msg = sys.stdin.readline()
            en_msg = msg.encode()
            clientSocket.send(en_msg)
            print("Message sent")

        elif r==clientSocket:
            msg = clientSocket.recv(1024)
            if msg == b'':
                continue
            de_msg = msg.decode()
            print("Message arrived:", de_msg)