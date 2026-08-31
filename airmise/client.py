import atexit
import typing as tp
from types import FunctionType

from . import const
from .master import Master
from .socket_wrapper import Socket


class Client:
    # FIXME: should we distinguish server_host, server_port from host and port?
    host: str
    master: tp.Optional[Master]
    port: int
    _socket: tp.Optional[Socket]

    def __init__(self) -> None:
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

    def config(
        self, host: str, port: int, verbose: tp.Optional[bool] = None
    ) -> tp.Self:
        if (self.host, self.port) != (host, port):
            self.host, self.port = host, port
            if self.is_opened:
                print('restart client to apply new config', ':pv')
                self.reopen()
                if verbose is not None:
                    assert self._socket
                    self._socket.verbose = verbose
        return self

    def open(
        self,
        host: str = const.DEFAULT_HOST,
        port: int = const.DEFAULT_PORT,
        timeout: int = 0,
    ) -> tp.Self:
        assert host and port
        if self.is_opened:
            # print(
            #     ':v6p',
            #     'client already connected. if you want to reconnect, please '
            #     'use `reopen` method'
            # )
            if self.host == host and self.port == port:
                return self
            else:
                self.close()
        self._socket = Socket()
        try:
            self._socket.connect(host, port, timeout)
        except Exception:
            self._socket.close()
            self._socket = None
            raise
        else:
            self.host, self.port = host, port
        self.master = Master(self._socket)
        return self

    connect = open

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

    def exec(self, source: tp.Union[str, FunctionType], **kwargs) -> tp.Any:
        if not self.is_opened:
            self.open()
        return self.master.exec(source, **kwargs)

    def call(self, func_name: str, *args, **kwargs) -> tp.Any:
        if not self.is_opened:
            self.open()
        return self.master.call(func_name, *args, **kwargs)

    def set_passive(self) -> None:  # blocking
        self.master.set_passive()


default_client = Client()
exec = default_client.exec
call = default_client.call
config = default_client.config
# connect = _default_client.open


def connect(
    host: str = '', port: int = 0, path: str = '', timeout: int = 0
) -> None:
    # fmt: off
    # if host: default_client.host = host  # noqa
    # if port: default_client.port = port  # noqa
    # if path: default_client.path = path  # noqa
    # fmt: on
    default_client.open(
        host or default_client.host, port or default_client.port, timeout
    )
