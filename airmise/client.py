import atexit
import typing as t
from types import FunctionType

from . import const
from .master import Master
from .socket_wrapper import Socket


class Client:
    # FIXME: should we distinguish server_host, server_port from host and port?
    host: str
    master: t.Optional[Master]
    port: int
    _socket: t.Optional[Socket]
    
    def __init__(
        self,
        host: str = const.DEFAULT_HOST,
        port: int = const.DEFAULT_PORT,
    ) -> None:
        self.host = host
        self.port = port
        self.master = None
        self._socket = None
        atexit.register(self.close)
    
    @property
    def id(self) -> int:
        return self._socket.port
    
    @property
    def is_opened(self) -> bool:
        return bool(self._socket)
    
    @property
    def url(self) -> str:  # DELETE?
        return 'tcp://{}:{}'.format(self.host, self.port)
    
    def config(self, host: str, port: int, verbose: bool = None) -> t.Self:
        if (self.host, self.port) != (host, port):
            self.host, self.port = host, port
            if self.is_opened:
                print('restart client to apply new config', ':pv')
                self.reopen()
                if verbose is not None:
                    self._socket.verbose = verbose
        return self
    
    def open(self) -> None:
        if self.is_opened:
            # print(
            #     ':v6p',
            #     'client already connected. if you want to reconnect, please '
            #     'use `reopen` method'
            # )
            return
        self._socket = Socket()
        self._socket.connect(self.host, self.port)
        self.master = Master(self._socket)
    
    def close(self) -> None:
        if self.is_opened:
            print('close connection', ':v')
            try:
                self._socket.send_close_event()
            except OSError:
                pass
            self._socket.close()
            self._socket = None
    
    def reopen(self) -> None:
        self.close()
        self.open()
    
    def exec(self, source: t.Union[str, FunctionType], **kwargs) -> t.Any:
        if not self.is_opened: self.open()
        return self.master.exec(source, **kwargs)
    
    def call(self, func_name: str, *args, **kwargs) -> t.Any:
        if not self.is_opened: self.open()
        return self.master.call(func_name, *args, **kwargs)


default_client = Client()
exec = default_client.exec
call = default_client.call
config = default_client.config
# connect = _default_client.open


def connect(host: str = None, port: int = None, path: str = None) -> None:
    if host: default_client.host = host
    if port: default_client.port = port
    if path: default_client.path = path
    default_client.open()
