"""
https://chatgpt.com/share/6a965430-dab0-83ee-aac8-916c0bd374be
"""

import os
import platform
import typing as tp
from types import FunctionType

from lk_utils import now
from lk_utils import uuid

from .. import const
from ..codec import decode
from ..codec import encode
from ..requester import interpret_code
from ..requester import interpret_func
from ..server import Server
from ..responder import Responder
from ..responder import T as T0
from ..socket_wrapper import Socket
from ..socket_wrapper import SocketClosed
from ..util import get_local_ip_address


class T:
    Namespace = T0.Namespace
    UserInfo = tp.TypedDict(
        'UserInfo',
        {
            'client_id': str,
            'comp_name': str,
            'user_name': str,
            'user_host': str,
            'user_port': int,
            'conn_host': str,
            'conn_port': int,
            'timestamp': str,
        },
    )


class Broker(Responder):
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
                self._source.close()
                print('close broker', ':v7')
                break

            event, data = decode(data_bytes)
            # assert flag == const.INTERNAL
            # assert event in ('close', 'request', 'response')
            assert event in ('close', 'request'), (event, data)

            if event == 'close':
                # self._target.send_close_event()
                # self._target.close()
                # self._source.sendall(b'ok')
                self._source.close()
                print('close broker', ':v7')
                break
            else:
                self._target.sendall(data)  # -> Callee:_mainloop:socket.recvall
                rsp = self._target.recvall()
                # print(str(decode(data))[:500], str(decode(rsp))[:500], ':ilnv')
                self._source.sendall(rsp)


class Router(Server):
    def __init__(
        self, host: str = const.DEFAULT_HOST, port: int = const.SERVER_PORT
    ) -> None:
        super().__init__(host, port)
        self.routes: tp.Dict[str, tp.Tuple[Socket, T.UserInfo]] = {}
        #   {uid: (connection, user_info), ...}

    def _handle_connection(self, conn: Socket) -> None:
        data_bytes = conn.recvall()
        flag, event, data = decode(data_bytes)
        assert flag == const.INTERNAL
        if event == 'register_proxy_caller':
            uid = data['uid']
            assert uid in self.routes, uid
            broker = self.connections[conn.port] = Broker(
                source=conn, target=self.routes[uid][0]
            )
            broker.mainloop(blocking=False)
            conn.sendall(encode((const.NORMAL, 'ok')))
        elif event == 'register_proxy_callee':
            client_id = uuid()
            user_info: T.UserInfo = {
                'client_id': client_id,
                'comp_name': data['computer_name'],
                'user_name': data['user_name'],
                'user_host': data['ip'],
                #   i don't name it "user_ip" because i want all key names'
                #   lengths equal, feels a little good in code formatting.
                'user_port': data['port'],
                'conn_host': conn.host,
                'conn_port': conn.port,
                'timestamp': now(),
            }
            print(user_info, ':nv2li')
            self.routes[client_id] = (conn, user_info)
            conn.sendall(encode((const.NORMAL, client_id)))
        else:
            # maybe regular client, see `../client.py:Client:_say_hi` and
            # `../server.py:Server:_handle_connection`
            endpoint = self.connections[conn.port] = Responder(
                conn, self._default_user_namespace
            )
            endpoint.mainloop(blocking=False)


class Callee(Responder):
    def __init__(self, user_namespace: tp.Optional[T.Namespace] = None) -> None:
        super().__init__(None, user_namespace)  # type: ignore
        self.computer_name = platform.node()
        self.user_name = os.getlogin()
        self.user_ip = get_local_ip_address()
        self.user_id = ''

    @property
    def uid(self) -> str:
        assert self.user_id
        return self.user_id

    @property
    def user_info(self) -> str:
        assert self.socket
        return '{}@{}:{}'.format(self.user_name, self.user_ip, self.socket.port)

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
        # self.user_info = '{}@{}:{}'.format(
        #     os.getlogin(), get_local_ip_address(), self.socket.port
        # )
        self._send(
            const.INTERNAL,
            'register_proxy_callee',
            {
                'user_name': self.user_name,
                'computer_name': self.computer_name,
                'ip': self.user_ip,
                'port': self.socket.port,
            },
        )
        self.user_id = self._recv()
        print(self.user_id, ':nv2')


class Caller(Responder):
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
