import socket
import select
import traceback
import sys
import re


def show_room_list(rooms):
    if not rooms:
        print("MASTER: no room created")
        return
    print("--[Room list]--")
    for room_name in rooms:
        print(room_name)
        print("\n")


def shut_down_server(server_socket, clients):
    for clientAddr in clients:
        en_msg = "exit".encode()
        client = clients[clientAddr]["entity"]
        client.send(en_msg)
    server_socket.close()
    print("Chat server has been shut down")
    sys.exit(0)


def kill_room(msg, rooms):
    room_name: object = re.findall("\/kill ([\w]+)\n", msg)[0]
    target_room = rooms[room_name]
    for member in target_room["members"]:
        en_msg = "kill".encode()
        member.send(en_msg)

    del rooms[room_name]


def show_clients(clients):
    if not clients:
        print("MASTER: no clients connected")
        return
    print("--[Client list]--")
    for clientAddr in clients:
        print(clientAddr)
        print("\n")


def operate_server_command(msg, rooms, server_socket, clients):
    if msg == '/ls\n':
        show_room_list(rooms)
    elif msg == '/exit\n':
        shut_down_server(server_socket, clients)
    elif msg == re.search("\/kill ([\w]+)\n", msg):
        kill_room(msg, rooms)
    elif msg == '/show clients\n':
        show_clients(clients)
    else:
        print("Invalid Input!!")


addr = ('127.0.0.1', 3000)
server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

try:
    server_socket.bind(addr)

except:
    traceback.print_exc()
    print("An error occurred while opening the server.")
    sys.exit(0)

print("The Server has been opened")

rooms = {}
clients = {}

server_socket.listen(10)

rlist = [server_socket, sys.stdin]

print('>', sep=' ', end='', flush=True)
while True:

    R, W, X = select.select(rlist, [], [], 500)

    if not R:
        shut_down_server(server_socket, clients)

    r = R[0]

    if r == sys.stdin:
        msg = sys.stdin.readline()
        operate_server_command(msg, rooms, server_socket, clients)

    elif r == server_socket:
        client, clientAddr = server_socket.accept()
        print("New Client has been Connected", clientAddr)
        rlist.append(client)
        clients[clientAddr] = {"entity": client, "state": 0}

    else:
        msg = r.recv(1024)
        de_msg = msg.decode()
        if msg == b'':
            continue
        print("New msg arrived -- ", de_msg)

    print('>', sep=' ', end='', flush=True)