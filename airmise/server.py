import os
import signal
import threading
import typing as t
from time import sleep

from lk_utils import run_new_thread
from lk_utils.subproc import ThreadBroker

from . import const
from .slave import Slave
from .socket_wrapper import Socket
from .util import get_local_ip_address


class NonblockingSlave(Slave):
    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self._mainloop_thread: t.Optional[ThreadBroker] = None
    
    def mainloop(self) -> None:
        assert not self._mainloop_thread
        self._mainloop_thread = run_new_thread(
            self._mainloop,
            self.socket,
            self._user_namespace,
            interruptible=True,
        )
    
    def set_active(self) -> None:
        if self._mainloop_thread:
            self._mainloop_thread.stop()
        self.active = True


class Server:
    connections: t.Dict[int, NonblockingSlave]
    host: str
    port: int
    verbose: bool
    _default_user_namespace: dict
    _socket: Socket
    
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
        if (
            os.name == 'nt' and
            threading.current_thread() is threading.main_thread()
        ):
            signal.signal(signal.SIGINT, signal.SIG_DFL)
        
        while True:
            socket = self._socket.accept()  # blocking
            slave = self.connections[socket.port] = NonblockingSlave(
                socket, self._default_user_namespace
            )
            slave.mainloop()  # nonblocking
            sleep(0.1)


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
