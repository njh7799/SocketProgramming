import socket
import select
import traceback
import sys
import re
from library import receive_message, send_message


def propagate_message(msg, rooms, client, client_detail):
    room_name = client_detail["room_name"]
    members = rooms[room_name]["members"]
    for member in members:
        if member == client:
            continue
        send_message(member, msg)


def close_server(server_socket):
    server_socket.close()
    print("Close chat server")
    sys.exit(0)


def get_room_list(rooms):
    if not rooms:
        return "MASTER: no room created"
    room_list = "--[Room list]--"
    for room_name in rooms:
        room_detail = rooms[room_name]
        room_list += '\r\n' + room_name
        room_list += '\r\n  creator: ' + room_detail["creator_name"]
        room_list += '\r\n  n of members: ' + str(len(room_detail["members"]))
    return room_list


def propagate_client_details_for_server_end(client_details):
    for client in client_details:
        send_message(client, "exit")


def end_chat_service(server_socket, client_details):
    propagate_client_details_for_server_end(client_details)
    close_server(server_socket)


def kill_room(msg, rooms, client_details):
    room_name = re.findall("\/kill ([\w]+)", msg)[0]
    room = rooms[room_name]
    for member in room["members"]:
        send_message(member, "Room has been killed")
        client_details[member] = {
            "state": "wait",
            "room_name": '',
            "user_name": ''
        }
    del rooms[room_name]
    print(room_name,"is killed")


def show_clients(client_details):
    if not client_details:
        print("MASTER: no clients connected")
        return
    print("--[Client list]--")
    for client in client_details:
        print("address:", client.getpeername())
        print("state:", client_details[client]["state"])
        print("room name:", client_details[client]["room_name"])
        print("user name:", client_details[client]["user_name"])


def does_user_name_exists(user_name, room, client_details):
    members = room["members"]
    for member in members:
        if client_details[member]["user_name"] == user_name:
            return True
    return False


def join_room(msg, rooms, client, client_details):
    (room_name,null,user_name) = re.findall("\/join ([\w]+)( ([\w]+))?", msg)[0]
    if room_name not in rooms:
        send_message(client, "MASTER: no room named "+room_name+"!!!")
        return
    if client_details[client]["state"] == "chat":
        send_message(client, "Cannot join: client is already in a chat room")
        return
    room = rooms[room_name]
    if user_name and does_user_name_exists(user_name, room, client_details):
        send_message(client, "Cannot join: Nickname already exists")
        return
    if not user_name:
        user_name = "Unknown"
    client_details[client] = {
        "state": "chat",
        "room_name": room_name,
        "user_name": user_name
    }
    msg = "Client " + client_details[client]["user_name"] + " joined in the room.\r\n"
    msg += "name: " + client_details[client]["user_name"] + "\r\n"
    msg += "addr: " + str(client.getpeername()) + "\r\n"
    propagate_message(msg, rooms, client, client_details[client])
    room["members"].append(client)
    send_message(client, "Room "+room_name+" joined")
    return


def create_room(msg, rooms, client, client_details):
    (room_name, null, user_name) = re.findall("\/create ([\w]+)( ([\w]+))?", msg)[0]
    if room_name in rooms:
        send_message(client, "MASTER: same room name already exists!!!")
        return
    if client_details[client]["state"] == "chat":
        send_message(client, "Cannot create: client is already in a chat room")
        return

    if not user_name:
        user_name = "Unknown"

    room = {
        "creator": client,
        "creator_name": user_name,
        "room_name":room_name,
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


def handle_creator_left_event(room, client):
    send_message(client, "Left the room")
    for member in room["members"]:
        if member == client:
            continue
        send_message(member, "Creator left the room and has been abandoned")
        client_details[member] = {
            "state": "wait",
            "room_name": '',
            "user_name": ''
        }
    client_details[client] = {
        "state": "wait",
        "room_name": '',
        "user_name": ''
    }
    del rooms[room["room_name"]]
    return


def handle_participant_left_event(room, rooms, client, client_details):
    client_detail = client_details[client]
    msg = "Client " + client_detail["user_name"] + " has left the room."
    send_message(client, "Left the room")
    propagate_message(msg, rooms, client, client_detail)
    client_details[client] = {
        "state": "wait",
        "room_name": '',
        "user_name": ''
    }
    room["members"] = [member for member in room["members"] if member != client]


def handle_client_disconnect_event(client, client_details):
    print("Client", str(client.getpeername()), "has left")
    del client_details[client]
    send_message(client, "exit")
    return


def find_client_with_user(user_name, room, client_details):
    members = room["members"]
    for member in members:
        if client_details[member]["user_name"] == user_name:
            return member
    return False


def whisper(msg, rooms, client, client_detail):
    if client_detail["state"] == "wait":
        send_message(client, "MASTER: You must go into the room first!!")
        return
    (user_name, chat_msg) = re.findall("\/whisper ([\w]+) ([\w| ]+)", msg)[0]
    if user_name == "Unknown":
        send_message(client, "MASTER: You can not send message to Unknown users!!")
        return
    room_name = client_detail["room_name"]
    room = rooms[room_name]
    target_client = find_client_with_user(user_name, room, client_details)
    if not target_client:
        send_message(client, "No client with the name "+user_name+" exist in this room")
        return
    send_message(target_client, "(whisper from) "+client_detail["user_name"] + ": " + chat_msg)


def run_exit(rooms, client, client_details):
    client_detail = client_details[client]
    if client_detail["state"] == "wait":
        handle_client_disconnect_event(client, client_details)
        return
    room_name = client_detail["room_name"]
    room = rooms[room_name]
    creator = room["creator"]
    if creator == client:
        handle_creator_left_event(room, client)
        return

    handle_participant_left_event(room, rooms, client, client_details)


def propagate_chat_message(msg, rooms, client, client_detail):
    if client_detail["state"] == "wait":
        send_message(client, "MASTER: You must go into the room first!!")
        return

    propagate_message(client_detail["user_name"]+":"+msg, rooms, client, client_detail)


def operate_server_command(msg, rooms, server_socket, client_details):
    if msg == '/ls':
        print(get_room_list(rooms))
    elif msg == '/exit':
        end_chat_service(server_socket, client_details)
    elif re.search("\/kill ([\w]+)", msg):
        kill_room(msg, rooms, client_details)
    elif msg == '/show clients':
        show_clients(client_details)
    else:
        print("Inappropriate Command!!")


def handle_client_message(msg, rooms, client, client_details):
    client_detail = client_details[client]
    if msg == '/ls':
        send_message(client, get_room_list(rooms))
    elif re.search("\/join ([\w]+)( ([\w]+))?", msg):
        join_room(msg, rooms, client, client_details)
    elif re.search("\/create ([\w]+)( ([\w]+))?", msg):
        create_room(msg, rooms, client, client_details)
    elif re.search("\/whisper ([\w]+) ([\w| ]+)", msg):
        whisper(msg, rooms, client, client_detail)
    elif msg == "/exit":
        run_exit(rooms, client, client_details)
    elif re.search("^\/", msg):
        send_message(client, "Inappropriate Command!!")
    else:
        propagate_chat_message(msg, rooms, client, client_detail)


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
# example
# {
#     room_name:{
#         room_name: room11
#         creator: client
#         members = [
#           client
#        ]
#     }
# }
client_details = {}
# example
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
        msg = sys.stdin.readline().strip()
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
        handle_client_message(msg, rooms, r, client_details)

    print('>', sep=' ', end='', flush=True)