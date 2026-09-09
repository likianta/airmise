import socket
import typing as tp


class SocketClosed(Exception):
    pass


class Socket:
    # host: str
    # port: int
    # peer_host: str
    # peer_port: int
    verbose: bool
    _host: str
    _peer_host: str
    _peer_port: int
    _port: int
    _socket: socket.socket

    def __init__(self, verbose: bool = False) -> None:
        self._socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        # `self._host`, `self._port` are not initialized until 
        # `self.connect/bind/accept`.
        self.verbose = verbose

    # @property
    # def host(self) -> str:
    #     return self._host

    # @property
    # def port(self) -> int:
    #     return self._port

    @property  # DELETE
    def plain_addr(self) -> str:
        return '{}:{}'.format(self._host, self._port)

    # @property  # DELETE
    # def url(self) -> str:
    #     return 'tcp://{}:{}'.format(self._host, self._port)

    # --------------------------------------------------------------------------
    # client side

    @property
    def local_host(self) -> str:
        return self._host

    @property
    def local_port(self) -> int:
        return self._port

    def connect(
        self, server_host: str, server_port: int, timeout: int = 0
    ) -> None:
        if server_host == '0.0.0.0':
            # '0.0.0.0' is not a routable address, we convert it to 'localhost'.
            server_host = 'localhost'
        try:
            if timeout:
                self._socket.settimeout(timeout)
            self._socket.connect((server_host, server_port))
            if timeout:
                self._socket.settimeout(None)
        except Exception:
            print(
                ':pr',
                '[red]cannot connect to server [dim]({}:[u dim]{}[/])[/]! '
                'please check if server online.[/]'.format(
                    server_host, server_port
                ),
            )
            raise
        # notice: the port from `getsockname` may be wrong if server is bridged
        # via frp service.
        # see a workaround in `build/build_standalone/airclient_standalone
        # /src/client.py`.
        self._host, self._port = self._socket.getsockname()
        self._peer_host = server_host
        self._peer_port = server_port
        print(
            ':pr',
            '[green]connected to server: '
            '[default dim]local ({}:[u dim]{}[/])[/] '
            '-> server [dim]({}:[u dim]{}[/])[/][/]'.format(
                self.local_host, self.local_port, self.peer_host, self.peer_port
            ),
        )

    def close(self) -> None:
        self._socket.close()

    # --------------------------------------------------------------------------
    # server side

    @property
    def peer_host(self) -> str:
        return self._peer_host

    @property
    def peer_port(self) -> int:
        return self._peer_port

    def bind(self, host: str, port: int) -> None:
        self._host = host
        self._port = port
        self._socket.bind((host, port))

    def listen(self, backlog: int = 1) -> None:
        self._socket.listen(backlog)
        print(':pv2', 'server is listening at "{}"'.format(self.plain_addr))

    def accept(self) -> 'PeerSocket':
        conn, addr = self._socket.accept()
        self._peer_host = addr[0]
        self._peer_port = addr[1]

        peer_sock = PeerSocket(conn, addr[0], addr[1], self.verbose)
        print(
            '[green]new connection accepted: '
            '[default dim]server ({}:[u dim]{}[/])[/] '
            '<- client [dim]({}:[u dim]{}[/])[/][/]'.format(
                self.local_host, self.local_port, peer_sock.host, peer_sock.port
            ),
            ':rp',
        )
        return peer_sock

    def recvall(self) -> bytes:
        if x := self._socket.recv(1):
            size_width = int(x)
            """
                digits  max_hex     max_size
                ------  ----------  --------
                0       .           CLOSED
                1       F           16B
                2       FF          256B
                3       FFF         4KB
                4       FFFF        64KB
                5       FFFFF       1MB
                6       FFFFFF      16MB
                7       FFFFFFF     256MB
                8       FFFFFFFF    4GB
                9       FFFFFFFFF   64GB
            """
        else:  # https://chatgpt.com/share/6a980167-78a0-83ee-9897-47fc08baa7fd
            print(':v7p', 'peer disconnected')
            raise SocketClosed

        if size_width == 0:
            print(
                ':pv7',
                'remote request closing this connection',
                self.plain_addr,
            )
            self.sendall(b'ok')
            self._socket.close()
            print(':pv3', 'port released', self.port)
            raise SocketClosed

        exact_size = int(self._socket.recv(size_width), 16)
        # notice: https://stackoverflow.com/a/17668009/9695911
        # trick: https://poe.com/s/2HbNCYsmKHIqZqoQ6Md3
        data_bytes = bytearray()
        requested_size = exact_size
        while requested_size:
            fact_bytes = self._socket.recv(requested_size)
            data_bytes.extend(fact_bytes)
            requested_size -= len(fact_bytes)
        if self.verbose:
            print(
                ':vi3',
                'recv',
                size_width,
                '{:X} ({})'.format(exact_size, _pretty_size(exact_size)),
                _shortify_message(data_bytes),
            )
        return bytes(data_bytes)

    def send_close_event(self) -> None:
        self._socket.sendall(b'0')
        assert self.recvall() == b'ok'

    def sendall(self, msg: bytes) -> None:
        for datum in self._encode_message(msg):
            self._socket.sendall(datum)

    def _encode_message(self, data_bytes: bytes) -> tp.Iterator[bytes]:
        exact_size = '{:X}'.format(len(data_bytes))
        size_width = len(exact_size)
        assert 0 < size_width <= 9
        if self.verbose:
            print(
                ':vi3',
                'send',
                size_width,
                '{} ({})'.format(exact_size, _pretty_size(int(exact_size, 16))),
                _shortify_message(data_bytes),
            )
        yield str(size_width).encode()
        yield exact_size.encode()
        yield data_bytes


class PeerSocket(Socket):
    host: str
    port: int
    # this_host: str
    # this_port: int
    # peer_host: str
    # peer_port: int

    def __init__(
        self,
        # peer_connection: socket.socket,
        # this_address,
        # peer_address,
        connection: socket.socket,
        host: str,
        port: int,
        verbose: bool = False,
    ) -> None:
        self._socket = connection
        self.host = host
        self.port = port
        self.verbose = verbose


def get_any_vaild_socket(
    try_hosts: tp.Iterable[str], port: int, timeout: int = 0
) -> tp.Tuple[Socket, str]:
    for host in try_hosts:
        s = Socket()
        try:
            s.connect(host, port, timeout)
        except Exception:
            s.close()
            continue
        else:
            return s, host
    else:
        raise Exception('connection failed', try_hosts)


def _pretty_size(size: tp.Union[int, float]) -> str:
    for unit in ('B', 'KB', 'MB', 'GB'):
        if size < 1024:
            return f'{size:.2f}{unit}'
        size /= 1024
    else:
        return f'{size:.2f}TB'


def _shortify_message(
    msg_in_bytes: tp.Union[bytes, bytearray], chunk_size: int = 10
) -> str:
    if len(msg_in_bytes) < chunk_size * 2:
        return msg_in_bytes.decode()
    else:
        return '{}...{}'.format(
            msg_in_bytes[:chunk_size].decode(),
            msg_in_bytes[-chunk_size:].decode(),
        )
