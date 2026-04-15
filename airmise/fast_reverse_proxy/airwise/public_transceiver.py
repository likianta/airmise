from lk_utils import run_new_thread
from time import sleep
from ...codec2 import decode
from ...codec2 import encode
from ...const import DEFAULT_HOST
from ...const import FRP_TRANSCEIVER_PORT
from ...socket_wrapper import Socket
from ...util import fix_ctrl_c_keystroke
from ...util import get_free_port

def run_transceiver(host: str = DEFAULT_HOST, port: int = FRP_TRANSCEIVER_PORT):
    sock = Socket()
    sock.bind(host, port)
    sock.listen(100)
    
    fix_ctrl_c_keystroke()
    
    while True:
        conn = sock.accept()  # blocking
        type, data = decode(conn.recvall())
        assert type == 'register'
        src_port = data
        proxy_port = get_free_port(src_port, 20000 + src_port)
        print('connection setup: {} <- {}'.format(proxy_port, src_port))
        
        run_new_thread(_allocate_sub_runner, conn, proxy_port)
        conn.sendall(encode(('connection_established', proxy_port)))
        sleep(0.1)

def _allocate_sub_runner(main_connection: Socket, sub_port: int):
    sock = Socket()
    sock.bind('0.0.0.0', sub_port)
    sock.listen(100)

    while True:
        conn = sock.accept()
        run_new_thread(_handle_io, conn, main_connection)
        sleep(0.1)

def _handle_io(public_channel: Socket, private_channel: Socket):
    while True:
        raw_data = public_channel.recvall()  # blocking
        private_channel.sendall(raw_data)
        response = private_channel.recvall()  # blocking
        public_channel.sendall(response)
        sleep(0.1)
