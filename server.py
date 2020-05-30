import socket
import select
import traceback
import sys

addr = ('127.0.0.1', 3000)
serverSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

try:
    serverSocket.bind(addr)

except:
    traceback.print_exc()
    print("An error occurred while opening the server.")

print("The Server has been opened")
serverSocket.listen(10)

rlist = [serverSocket]

while True:
    R,W,X = select.select(rlist, [],[], 50)

    for r in R:
        print(r)
        if r==serverSocket:
            client, clientAddr = serverSocket.accept()
            print("New Client Connected", clientAddr)
            msg = 'hello new client'
            en_msg = msg.encode()
            client.send(en_msg)
            rlist.append(client)

        else:
            msg = r.recv(1024)
            de_msg = msg.decode()
            if msg == b'':
                continue
            print("New msg arrived -- ", de_msg)