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
        flag: int
        event: tp.Literal['register', 'request', 'response']
        data: dict

        while True:
            yield

            try:
                data_bytes = self._source.recvall()
            except (SocketClosed, ConnectionResetError):
                return

            flag, event, data = decode(data_bytes)
            assert flag == const.INTERNAL
            assert event in ('request', 'response')
            assert 'uid' in data and 'raw' in data

            self._target.sendall(data['raw'])
            rsp = self._target.recvall()
            self._source.sendall(rsp)


class Router(Server):
    def __init__(
        self, host: str = const.DEFAULT_HOST, port: int = const.SERVER_PORT
    ) -> None:
        super().__init__(host, port, _assignment=Broker)
        self._channels = {}

    def _handle_connection(self, conn: Socket) -> None:
        data_bytes = conn.recvall()
        flag, event, data = decode(data_bytes)
        assert flag == const.INTERNAL
        assert event == 'register'

        if data is None:  # register callee
            uid = uuid()
            self._channels[uid] = (None, conn)
            conn.sendall(encode((const.NORMAL, uid)))

        else:  # register caller
            uid = data['uid']
            assert (
                uid in self._channels
                and self._channels[uid][0] is None
                and self._channels[uid][1] is not None
            )
            self._channels[uid] = (conn, self._channels[uid][1])
            conn.sendall(encode((const.NORMAL, 'ok')))

            slave = self.connections[conn.port] = self._assignment(
                *self._channels[uid]
            )
            slave.mainloop(blocking=False)


class Callee(Slave):
    def __init__(self, user_namespace: tp.Optional[T.Namespace] = None) -> None:
        super().__init__(None, user_namespace)  # type: ignore
        self.uid = ''
        self._mainloop_running = False
        self._user_namespace = user_namespace or {}

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
            self._send(const.INTERNAL, 'register', None)
            self.uid = self._recv()
            print(self.uid, ':nv2p')
        return self


class Caller(Slave):
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
            self._send(const.INTERNAL, 'register', {'uid': self._uid})
            assert self._recv() == 'ok'
        return self

    def call(self, func_name: str, *args, **kwargs) -> tp.Any:
        self._send(
            const.INTERNAL,
            'request',
            {
                'uid': self._uid,
                'raw': encode(
                    (
                        const.CALL_FUNCTION,
                        func_name,
                        {'args': args, 'kwargs': kwargs},
                    )
                ),
            },
        )
        return self._recv()

    def exec(self, source: tp.Union[str, FunctionType], **kwargs) -> tp.Any:
        if isinstance(source, str):
            code = interpret_code(source)
        else:
            code = interpret_func(source)
        self._send(
            const.INTERNAL,
            'request',
            {'uid': self._uid, 'raw': encode((const.NORMAL, code, kwargs))},
        )
        return self._recv()
