import socket
import select
import traceback
import sys
import re
from library import receive_message, send_message


def close_server(server_socket):
    server_socket.close()
    print("Close chat server")
    sys.exit(0)


def show_room_list(rooms):
    if not rooms:
        print("MASTER: no room created")
        return
    print("--[Room list]--")
    for room_name in rooms:
        print(room_name)
        print("\n")


def propagate_client_details_for_server_end(client_details):
    for client in client_details:
        send_message(client, "exit")


def end_chat_service(server_socket, client_details):
    propagate_client_details_for_server_end(client_details)
    close_server(server_socket)


def kill_room(msg, rooms, client_details):
    room_name = re.findall("\/kill ([\w]+)\n", msg)[0]
    target_room = rooms[room_name]
    for member in target_room["members"]:
        send_message(member, "kill")
        client_details[client] = {
            "state": "wait",
            "room_name": '',
            "user_name": ''
        }
    del rooms[room_name]
    print(room_name,"is killed")


def show_client_details(client_details):
    if not client_details:
        print("MASTER: no client_details connected")
        return
    print("--[Client list]--")
    for client in client_details:
        print(client)
        print('\n')


def does_user_name_exists(user_name, room, client_details):
    members = room["members"]
    for member in members:
        if client_details[member]["user_name"] == user_name:
            return False
    return True


def create_room(msg, rooms, client, client_details):
    (room_name, null, user_name) = re.findall("\/create ([\w]+)( ([\w]+))?", msg)[0]
    if room_name in rooms:
        send_message(client, "MASTER: same room name already exists!!!")
        return
    if client_details[client]["state"] == "chat":
        send_message(client, "MASTER: you are already in the room!!!")
        return

    if not user_name:
        user_name = "Unknown"

    room = {
        "members": [client]
    }
    rooms[room_name] = room
    client_details[client] = {
        "state": "chat",
        "room_name": room_name,
        "user_name": user_name
    }
    send_message(client, "Room "+room_name+" created")
    print("New room "+room_name+" created")
    return


def join_room(msg, rooms, client, client_details):
    (room_name,null,user_name) = re.findall("\/join ([\w]+)( ([\w]+))?", msg)[0]
    if room_name not in rooms:
        send_message(client, "MASTER: no room named "+room_name+"!!!")
        return
    if client_details[client]["state"] == "chat":
        send_message(client, "MASTER: you are already in the room!!!")
        return
    room = rooms[room_name]
    if user_name and not does_user_name_exists(user_name, room, client_details):
        send_message(client, "MASTER: redundant user name! try different one")
        return
    if not user_name:
        user_name="Unknown"

    client_details[client] = {
        "state": "chat",
        "room_name": room_name,
        "user_name": user_name
    }
    room["members"].append(client)
    send_message(client, "Room "+room_name+" joined")
    return


def operate_server_command(msg, rooms, server_socket, client_details):
    if msg == '/ls\n':
        show_room_list(rooms)
    elif msg == '/exit\n':
        end_chat_service(server_socket, client_details)
    elif re.search("\/kill ([\w]+)\n", msg):
        kill_room(msg, rooms, client_details)
    elif msg == '/show clients\n':
        show_client_details(client_details)
    else:
        print("Invalid Input!!")


def handle_client_message(msg, client):
    if re.search("\/join ([\w]+)( ([\w]+))?\n", msg):
        join_room(msg, rooms, client, client_details)
    elif re.search("\/create ([\w]+)( ([\w]+))?\n", msg):
        create_room(msg, rooms, client, client_details)
    else:
        print("MASTER: Invalid message received:", msg)


addr = ('127.0.0.1', 3000)
server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

try:
    server_socket.bind(addr)

except:
    traceback.print_exc()
    print("An error occurred while opening the server.")
    sys.exit(0)

print("The Server has been opened")

rooms = {}  #
# {
#     room_name:{
#         members = [
#           client
#        ]
#     }
# }
client_details = {}
# {
#     <client>:{
#         "state":"wait",
#         "room_name": "",
#         "user_name": "",
#     }
# }


server_socket.listen(10)

rlist = [server_socket, sys.stdin]

print('>', sep=' ', end='', flush=True)
while True:

    R, W, X = select.select(rlist, [], [], 500)

    if not R:
        end_chat_service(server_socket, client_details)

    r = R[0]

    if r == sys.stdin:
        msg = sys.stdin.readline()
        operate_server_command(msg, rooms, server_socket, client_details)

    elif r == server_socket:
        client, clientAddr = server_socket.accept()
        print("New Client has been Connected", clientAddr)
        rlist.append(client)
        client_details[client] = {"state": "wait", "room_name": '', "user_name":''}

    else:
        msg = receive_message(r)
        if not msg:
            continue
        handle_client_message(msg, r)

    print('>', sep=' ', end='', flush=True)