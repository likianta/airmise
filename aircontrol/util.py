import socket
import sys
from functools import cache
from random import choices
from string import ascii_lowercase


@cache
def get_local_ip_address() -> str:
    # https://stackoverflow.com/a/166520/9695911
    if sys.platform == 'linux':
        return socket.gethostbyname(socket.getfqdn())
    else:
        return socket.gethostbyname(socket.gethostname())


def random_name() -> str:
    return '_' + ''.join(choices(ascii_lowercase, k=12))
