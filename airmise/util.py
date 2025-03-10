import socket
from functools import cache
from random import choices
from string import ascii_lowercase


@cache
def get_local_ip_address() -> str:
    """
    from:
        streamlit : /net_util.py : get_internal_ip()
            https://stackoverflow.com/a/28950776
    """
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
        try:
            # doesn't even have to be reachable
            s.connect(('8.8.8.8', 1))
            return s.getsockname()[0]
        except Exception:
            return '127.0.0.1'


def random_name() -> str:
    return '_' + ''.join(choices(ascii_lowercase, k=12))
