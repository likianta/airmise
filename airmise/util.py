import socket
from functools import cache
from random import choices
from string import ascii_lowercase


@cache
def get_local_ip_address() -> str:
    """
    ref:
        streamlit : /net_util.py : get_internal_ip()
            https://stackoverflow.com/a/28950776
    
    by the way, if you are using this method in android termux console, the -
    result is incorrect, and there is no way to get local ip address since we -
    don't have permission to use commands like `ifconfig` `ip addr` etc.
    see also: https://github.com/termux/termux-packages/issues/12758 \
    #issuecomment-1516423305
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
