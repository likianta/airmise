import os
import signal
import socket
import threading
import traceback
from functools import cache
from random import choices
from string import ascii_lowercase

import neoprint as np
from lk_utils import dedent


def fix_ctrl_c_keystroke() -> None:
    if (
        os.name == 'nt'
        and threading.current_thread() is threading.main_thread()
    ):
        signal.signal(signal.SIGINT, signal.SIG_DFL)


def format_exception(error: Exception, source: str = '') -> str:
    # https://chatgpt.com/share/6a9161d8-c738-83e8-a06c-04c44dfd896a
    if not source or '\n' not in source:
        return '\n'.join(traceback.format_exception(error))

    def dim(text: str) -> str:
        return np.format(text, markup=':sv')

    def red(text: str) -> str:
        return np.format(text, markup=':sv8')

    out_lines = []
    src_lines = source.splitlines()
    for line in traceback.format_exception(error):
        if line.lstrip().startswith('File "<string>"'):
            a, b, c = line.split(', ', 2)
            line_num = int(b.removeprefix('line '))
            src_index = line_num - 1
            out_lines.append(
                dedent(
                    """
                    File {}, line {}:
                        {}
                      > {}
                        {}
                    """
                )
                .format(
                    '"<string>"',
                    line_num,
                    dim(src_lines[src_index - 1]) if src_index > 0 else '',
                    red(src_lines[src_index]),
                    dim(src_lines[src_index + 1])
                    if (src_index + 1) < len(src_lines)
                    else '',
                )
                .rstrip()
            )
        else:
            out_lines.append(line)
    return '\n'.join(out_lines)


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


def random_name() -> str:
    return '_' + ''.join(choices(ascii_lowercase, k=12))
