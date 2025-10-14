import os
import signal
import typing as t
from time import sleep

from lk_utils import new_thread

from . import const
from .slave import Slave
from .socket_wrapper import Socket
from .util import get_local_ip_address


class Server:
    connections: t.Dict[int, Socket]
    host: str
    port: int
    verbose: bool
    _default_user_namespace: dict
    _socket: Socket
    
    # @property
    # def url(self) -> str:
    #     return 'tcp://{}:{}'.format(self.host, self.port)
    
    def __init__(
        self,
        host: str = const.DEFAULT_HOST,
        port: int = const.DEFAULT_PORT,
    ) -> None:
        self.connections = {}
        self.host = host
        self.port = port
        self.verbose = False
        self._default_user_namespace = {}
        self._socket = Socket()
    
    def run(
        self,
        user_namespace: dict = None,
        /,
        host: str = None,
        port: int = None,
        verbose: t.Union[bool, int] = 0,
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
        
        # fix ctrl + c
        if os.name == 'nt':
            signal.signal(signal.SIGINT, signal.SIG_DFL)
        
        while True:
            s = self._socket.accept()  # blocking
            self.connections[s.port] = s
            self._handle_connection(s)
            sleep(0.1)
    
    @new_thread()
    def _handle_connection(self, socket: Socket) -> None:
        Slave(socket, self._default_user_namespace).mainloop()


def run_server(
    user_namespace: dict = None,
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
