from lk_utils import run_new_thread
from time import sleep
from ...slave import Slave
from ...socket_wrapper import Socket
from ...const import DEFAULT_PORT
from ...const import FRP_TRANSCEIVER_PORT
from ...codec import decode
from ...codec import encode

def connect_to_public_transport(
    namespace: dict,
    source_port: int = DEFAULT_PORT,
    target_host: str = '',
    target_port: int = FRP_TRANSCEIVER_PORT,
) -> None:
    assert target_host
    
    sock = Socket()
    sock.bind('0.0.0.0', source_port)
    sock.connect(target_host, target_port)
    # run_new_thread(_discard_incoming_connection, sock)
    
    sock.sendall(encode(('register', source_port)))
    
    type, data = decode(sock.recvall())
    if type == 'connection_established':
        public_port = data
        print(
            'connection established ({} -> {}). you can use '
            '`air.connect("{}", {})` to reach public transport.'.format(
                source_port, public_port,
                target_host, public_port,
            ),
            ':v4'
        )
    elif type == 'connection_refused':
        raise NotImplementedError
    else:
        raise Exception(type, data)
    
    slave = Slave(sock, namespace)
    slave.mainloop()

def _discard_incoming_connection(sock: Socket):
    # sock._socket.listen(1)
    while True:
        conn = sock.accept()
        r = conn.recvall()
        assert r == b''
        print('discard incoming connection')
        conn.close()
        sleep(1)
