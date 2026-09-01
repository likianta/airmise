"""
https://chatgpt.com/share/6a965430-dab0-83ee-aac8-916c0bd374be
"""

import typing as tp
from types import FunctionType

from lk_utils import uuid

from .. import const
from ..codec import decode
from ..codec import encode
from ..master import interpret_code
from ..master import interpret_func
from ..server import Server
from ..slave import Slave
from ..slave import T
from ..socket_wrapper import Socket
from ..socket_wrapper import SocketClosed


class Broker(Slave):
    def __init__(self, source: Socket, target: Socket) -> None:
        super().__init__(source)
        self._source = source
        self._target = target

    def _mainloop(self, *_, **__) -> tp.Iterator:
        event: tp.Literal['close', 'request', 'response']
        data: bytes

        while True:
            yield

            try:
                data_bytes = self._source.recvall()
            except (SocketClosed, ConnectionResetError):
                return

            event, data = decode(data_bytes)
            # assert flag == const.INTERNAL
            assert event in ('close', 'request', 'response')

            if event == 'close':
                # self._target.send_close_event()
                # self._target.close()
                # self._source.sendall(b'ok')
                self._source.close()
                print('close broker', ':v7')
                return
            else:
                self._target.sendall(data)  # -> Callee:_mainloop:socket.recvall
                rsp = self._target.recvall()
                self._source.sendall(rsp)


class Router(Server):
    def __init__(
        self, host: str = const.DEFAULT_HOST, port: int = const.SERVER_PORT
    ) -> None:
        super().__init__(host, port)
        self._routes: tp.Dict[str, Socket] = {}

    def _handle_connection(self, conn: Socket) -> None:
        data_bytes = conn.recvall()
        flag, event, data = decode(data_bytes)
        assert flag == const.INTERNAL
        if event == 'register_proxy_caller':
            uid = data['uid']
            assert uid in self._routes, uid
            broker = self.connections[conn.port] = Broker(
                source=conn, target=self._routes[uid]
            )
            broker.mainloop(blocking=False)
            conn.sendall(encode((const.NORMAL, 'ok')))
        elif event == 'register_proxy_callee':
            uid = uuid()
            self._routes[uid] = conn
            conn.sendall(encode((const.NORMAL, uid)))
        else:
            # maybe regular client, see `../client.py:Client:_say_hi` and
            # `../server.py:Server:_handle_connection`
            endpoint = self.connections[conn.port] = Slave(conn)
            endpoint.mainloop(blocking=False)


class Callee(Slave):
    def __init__(self, user_namespace: tp.Optional[T.Namespace] = None) -> None:
        super().__init__(None, user_namespace)  # type: ignore
        self.uid = ''

    def connect(
        self,
        host: str = const.DEFAULT_HOST,
        port: int = const.SERVER_PORT,
        timeout: int = 0,
    ) -> tp.Self:
        self.socket = Socket()
        try:
            self.socket.connect(host, port, timeout)
        except Exception:
            self.socket.close()
            raise
        else:
            self._say_hi()
        return self

    def _say_hi(self) -> None:
        self._send(const.INTERNAL, 'register_proxy_callee')
        self.uid = self._recv()
        print(self.uid, ':nv2')


class Caller(Slave):
    """
    Message flow:
        `Caller.connect:_send` -> `Router._handle_connection:register caller`.
        `Caller:_request` -> `Broker._mainloop:self._source.recvall`.
        `Caller.call/exec:_recv` <- `Broker._mainloop:self._source.sendall`.
    """

    def __init__(self, uid: str) -> None:
        self._uid = uid

    def connect(
        self,
        host: str = const.DEFAULT_HOST,
        port: int = const.SERVER_PORT,
        timeout: int = 0,
    ) -> tp.Self:
        self.socket = Socket()
        try:
            self.socket.connect(host, port, timeout)
        except Exception:
            self.socket.close()
            raise
        else:
            self._say_hi()
        return self

    def _say_hi(self) -> None:
        self._send(const.INTERNAL, 'register_proxy_caller', {'uid': self._uid})
        assert self._recv() == 'ok'

    def close(self) -> None:
        self.socket.sendall(encode(('close', b'')))
        # assert self._recv() == 'ok'
        # self.socket.send_close_event()
        self.socket.close()

    def call(self, func_name: str, *args, **kwargs) -> tp.Any:
        self._request(
            encode(
                (
                    const.CALL_FUNCTION,
                    func_name,
                    {'args': args, 'kwargs': kwargs},
                )
            )
        )
        return self._recv()

    def exec(self, source: tp.Union[str, FunctionType], **kwargs) -> tp.Any:
        if isinstance(source, str):
            code = interpret_code(source)
        else:
            code = interpret_func(source)
        self._request(encode((const.NORMAL, code, kwargs)))
        return self._recv()

    def _request(self, raw_data: bytes) -> None:
        self.socket.sendall(encode(('request', raw_data)))
