import socket
import typing as t


class Socket:
    host: str
    port: int
    verbose: bool
    _socket: socket.socket
    
    def __init__(self, verbose: bool = False, **kwargs) -> None:
        self.verbose = verbose
        if '_socket' in kwargs:
            self._socket = kwargs['_socket']
            self.host = kwargs['host']
            self.port = kwargs['port']
            # del self.accept
            # del self.bind
            # del self.connect
        else:
            self._socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    
    @property
    def url(self) -> str:
        return 'tcp://{}:{}'.format(self.host, self.port)
    
    def accept(self) -> 'Socket':
        conn, addr = self._socket.accept()
        new_socket = Socket(_socket=conn, host=addr[0], port=addr[1])
        print(
            'new connection accepted',
            '{} <- {}'.format(self.url, new_socket.url),
            ':v'
        )
        return new_socket
    
    def bind(self, host: str, port: int) -> None:
        self.host = host
        self.port = port
        self._socket.bind((host, port))
    
    def close(self) -> None:
        self._socket.close()
    
    def connect(self, host: str, port: int) -> None:
        try:
            self._socket.connect(
                ('localhost' if host == '0.0.0.0' else host, port)
                #   '0.0.0.0' is not a routable address, we use 'localhost' -
                #   instead.
            )
        except Exception as e:
            print(
                ':v8p',
                'cannot connect to server via "{}"! '
                'please check if server online.'
                .format('tcp://{}:{}'.format(host, port))
            )
            raise e
        else:
            self.host, self.port = self._socket.getsockname()
            print(':pv4', 'connected to server: {} <- {}'.format(
                'tcp://{}:{}'.format(host, port), self.url
            ))
    
    def listen(self, backlog: int = 1) -> None:
        self._socket.listen(backlog)
        print(':pv2', 'server is listening at {}'.format(self.url))
    
    def recvall(self) -> bytes:
        size_width = int(self._socket.recv(1))
        '''
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
        '''
        if size_width == 0:
            print(':pv7', 'connection closed by client', self.url)
            self._socket.close()
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
                _shortify_message(data_bytes)
            )
        return data_bytes
    
    def send_close_event(self) -> None:
        self._socket.sendall(b'0')
    
    def sendall(self, msg: bytes) -> None:
        for datum in self._encode_message(msg):
            self._socket.sendall(datum)
    
    def _encode_message(self, data_bytes: bytes) -> t.Iterator[bytes]:
        exact_size = '{:X}'.format(len(data_bytes))
        size_width = len(exact_size)
        assert 0 < size_width <= 9
        if self.verbose:
            print(
                ':vi3',
                'send',
                size_width,
                '{} ({})'.format(exact_size, _pretty_size(int(exact_size, 16))),
                _shortify_message(data_bytes)
            )
        yield str(size_width).encode()
        yield exact_size.encode()
        yield data_bytes


def _pretty_size(size: int) -> str:
    for unit in ('B', 'KB', 'MB', 'GB'):
        if size < 1024:
            return f'{size:.2f}{unit}'
        size /= 1024
    else:
        return f'{size:.2f}TB'


def _shortify_message(msg_in_bytes: bytes, chunk_size: int = 10) -> str:
    if len(msg_in_bytes) < chunk_size * 2:
        return msg_in_bytes.decode()
    else:
        return '{}...{}'.format(
            msg_in_bytes[:chunk_size].decode(),
            msg_in_bytes[-chunk_size:].decode(),
        )


class SocketClosed(Exception):
    pass
