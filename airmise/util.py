import os
import signal
import socket
import threading
from functools import cache
from random import choices
from string import ascii_lowercase

def is_port_occupied(port: int) -> bool:
    """
    returns true if port is occupied, else free to use.
    time consumption: if port is occupied, it takes <10ms to get the result;
    else takes ~50ms to return.
    """
    # with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
    #     s.settimeout(0.05)
    #     if s.connect_ex(('localhost', port)) == 0:
    #         return True
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        try:
            s.bind(('0.0.0.0', port))
        except OSError as e:
            # OSError: [WinError 10048] Only one usage of each socket
            # address (protocol/network address/port) is normally permitted
            if e.winerror == 10048:
                return True
            else:
                raise e
        else:
            return False

def fix_ctrl_c_keystroke() -> None:
    if (
        os.name == 'nt' and
        threading.current_thread() is threading.main_thread()
    ):
        signal.signal(signal.SIGINT, signal.SIG_DFL)

def get_free_port(*prefers: int) -> int:
    sock = socket.socket()
    for p in prefers:
        if not is_port_occupied(p):
            return p
    sock.bind(('', 0))
    port = sock.getsockname()[1]
    sock.close()
    return port

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
