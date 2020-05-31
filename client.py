import socket
import select
import traceback
import sys
from library import receive_message, send_message


def close_client(client_socket):
    client_socket.close()
    print("Chat program has been closed")
    sys.exit(0)


def kill_room():
    print("Room has been killed")


def propagate_server_for_client_end(client_socket):
     send_message(client_socket, "exit")


def handle_server_msg(client_socket, msg):
    if msg == 'exit':
        close_client(client_socket)
    elif msg == 'kill':
        kill_room()
    else:
        print(msg)
addr = ('127.0.0.1', 3000)
client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

try:
    client_socket.connect(addr)

except:
    traceback.print_exc()
    print("An error occurred while opening the server.")

rlist = [client_socket, sys.stdin]

print('>', sep=' ', end='', flush=True)

while True:
    R,W,X = select.select(rlist, [], [], 500)

    if not R:
        close_client(client_socket)

    r = R[0]

    if r == sys.stdin:
        msg = sys.stdin.readline()
        send_message(client_socket, msg)

    elif r == client_socket:
        msg = receive_message(r)
        if not msg:
            continue

        handle_server_msg(client_socket, msg)

    print('>', sep=' ', end='', flush=True)
