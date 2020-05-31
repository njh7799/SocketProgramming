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


def propagate_client_details_for_server_end(client_details):
    for client in client_details:
        send_message(client, "exit")


def end_chat_service(server_socket, client_details):
    propagate_client_details_for_server_end(client_details)
    close_server(server_socket)


def kill_room(msg, rooms, client_details):
    room_name = re.findall("\/kill ([\w]+)", msg)[0]
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


def find_client_with_user(user_name, room, client_details):
    members = room["members"]
    for member in members:
        if client_details[member]["user_name"] == user_name:
            return member
    return False


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
    if user_name and does_user_name_exists(user_name, room, client_details):
        send_message(client, "MASTER: redundant user name! try different one")
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


def propagate_message(msg, rooms, client, client_detail):
    room_name = client_detail["room_name"]
    members = rooms[room_name]["members"]
    for member in members:
        if member == client:
            continue
        send_message(member, msg)


def run_exit(rooms, client, client_details):
    client_detail = client_details[client]
    if client_detail["state"] == "wait":
        print("Client", str(client.getpeername()), "has left")
        del client_details[client]
        send_message(client, "exit")

    elif client_detail["state"] == "chat":
        msg = "Client " + client_detail["user_name"] + " has left the room."
        send_message(client, "Left the room")
        propagate_message(msg, rooms, client, client_detail)
        client_details[client] = {
            "state": "wait",
            "room_name": '',
            "user_name": ''
        }


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
        send_message(client, "MASTER: There is no user named "+user_name+"!!")
        return
    send_message(target_client, "(whisper from) "+client_detail["user_name"] + ": " + chat_msg)


def propagate_chat_message(msg, rooms, client, client_detail):
    if client_detail["state"] == "wait":
        send_message(client, "MASTER: You must go into the room first!!")
        return

    propagate_message(client_detail["user_name"]+":"+msg, rooms, client, client_detail)


def operate_server_command(msg, rooms, server_socket, client_details):
    if msg == '/ls':
        show_room_list(rooms)
    elif msg == '/exit':
        end_chat_service(server_socket, client_details)
    elif re.search("\/kill ([\w]+)", msg):
        kill_room(msg, rooms, client_details)
    elif msg == '/show clients':
        show_client_details(client_details)
    else:
        print("Invalid Input!!")


def handle_client_message(msg, rooms, client, client_details):
    client_detail = client_details[client]
    if re.search("\/join ([\w]+)( ([\w]+))?", msg):
        join_room(msg, rooms, client, client_details)
    elif re.search("\/create ([\w]+)( ([\w]+))?", msg):
        create_room(msg, rooms, client, client_details)
    elif re.search("\/whisper ([\w]+) ([\w| ]+)", msg):
        whisper(msg, rooms, client, client_detail)
    elif msg == "/exit":
        run_exit(rooms, client, client_details)
    elif re.search("^\/", msg):
        send_message("MASTER: Invalid operation!")
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