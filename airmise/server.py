import typing as tp
from time import sleep

from . import const
from .codec import decode
from .slave import Slave
from .socket_wrapper import Socket
from .util import fix_ctrl_c_keystroke
from .util import get_local_ip_address


class Server:
    connections: tp.Dict[int, Slave]
    host: str
    port: int
    verbose: bool
    _default_user_namespace: dict
    _socket: Socket
    
    def __init__(
        self,
        host: str = const.DEFAULT_HOST,
        port: int = const.DEFAULT_PORT,
        # _assignment: tp.Type[Slave] = Slave,
    ) -> None:
        self.connections = {}
        self.host = host
        self.port = port
        self.verbose = False
        self._default_user_namespace = {}
        self._socket = Socket()
        # self._assignment = _assignment
    
    def run(
        self,
        user_namespace: tp.Optional[dict] = None,
        /,
        host: tp.Optional[str] = None,
        port: tp.Optional[int] = None,
        verbose: tp.Union[bool, int] = 0,
    ) -> None:
        """
        verbose:
            0 (also False): disabled
            1 (also True): enable socket verbose
                see also `./socket_wrapper.py : Socket`
            2: enable both socket and server verbose
                see also `self._mainloop : [code] if self.verbose...`
            usually we use 0/1, i.e. the False/True.
        """
        if user_namespace:
            self._default_user_namespace.update(user_namespace)
        self.verbose = bool(verbose == 2)
        self._socket.verbose = bool(verbose)
        self._socket.bind(host or self.host, port or self.port)
        self._socket.listen(20)
        
        fix_ctrl_c_keystroke()
        
        while True:
            conn = self._socket.accept()  # blocking
            self._handle_connection(conn)
            sleep(0.1)
    
    def _handle_connection(self, conn: Socket) -> None:
        assert decode(conn.recvall()) == (const.INTERNAL, 'hi', None)
        #   why does connector say hi?
        #   it helps server to distinguish the connector type. see practical 
        #   usage in `./fast_reverse_proxy/proxy_roles.py:Router
        #   :_handle_connection`.
        endpoint = self.connections[conn.port] = Slave(
            conn, self._default_user_namespace
        )
        endpoint.mainloop(blocking=False)


def run_server(
    user_namespace: tp.Optional[dict] = None,
    /,
    host: str = const.DEFAULT_HOST,
    port: int = const.DEFAULT_PORT,
    verbose: bool = False,
) -> None:
    if host == '0.0.0.0':
        print('server is working on: \n- {}\n- {}'.format(
            'http://localhost:{}'.format(port),
            'http://{}:{}'.format(get_local_ip_address(), port)
        ))
    server = Server(host, port)
    server.run(user_namespace, verbose=verbose)
