def send_message(target, msg):
    en_msg = msg.encode()
    target.send(en_msg)


def receive_message(target):
    msg = target.recv(1024)
    de_msg = msg.decode()
    if msg == b'':
        return ''
    return de_msg