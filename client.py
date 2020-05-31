import socket
import select
import traceback
import sys
from library import receive_message, send_message

def shut_down_client(client_socket):
    client_socket.close()
    print("Chat program has been shut down")
    sys.exit(0)


def handle_server_msg(client_socket, msg):
    if msg == 'exit':
        shut_down_client(client_socket)

addr = ('127.0.0.1', 3000)
client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

try:
    client_socket.connect(addr)

except:
    traceback.print_exc()
    print("An error occurred while opening the server.")

rlist = [client_socket, sys.stdin]

while True:
    R,W,X = select.select(rlist, [], [], 500)

    if not R:
        shut_down_client(client_socket)

    r = R[0]

    for r in R:
        if r==sys.stdin:
            msg = sys.stdin.readline()
            send_message(client_socket, msg)
            print("Message sent")

        elif r==client_socket:
            msg = receive_message(r)
            if not msg:
                continue

            handle_server_msg(client_socket, msg)
            print("Message arrived:", msg)