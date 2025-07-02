import socket
import typing as t


class Socket:
    # address: t.Tuple[str, int]
    url: str
    _socket: socket.socket
    
    def __init__(self, **kwargs) -> None:
        if '_socket' in kwargs:
            self._socket = kwargs['_socket']
            self.url = kwargs['_url']
            # del self.accept
            # del self.bind
            # del self.connect
        else:
            self._socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    
    def accept(self) -> 'Socket':
        conn, addr = self._socket.accept()
        new_socket = Socket(_socket=conn, _url='tcp://{}:{}'.format(*addr))
        print(
            'new connection accepted',
            '{} <- {}'.format(self.url, new_socket.url),
            ':v'
        )
        return new_socket
    
    def bind(self, host: str, port: int) -> None:
        self._socket.bind((host, port))
        self.url = 'tcp://{}:{}'.format(host, port)
    
    def close(self) -> None:
        self._socket.close()
    
    def connect(self, host: str, port: int) -> None:
        try:
            self._socket.connect((host, port))
        except Exception as e:
            print(
                ':v8p',
                'cannot connect to server via "{}"! '
                'please check if server online.'.format(self.url)
            )
            raise e
        else:
            self.url = 'tcp://{}:{}'.format(host, port)
            print(':pv4', 'connected to server: {}'.format(self.url))
    
    def listen(self, backlog: int = 1) -> None:
        self._socket.listen(backlog)
        print(':pv2', 'server is listening at {}'.format(self.url))
    
    def recvall(self) -> bytes:
        size_width = int(self._socket.recv(1))
        '''
            digits      max_hex     max_size
            ----------- ----------  --------
            0           .           CLOSED
            1           F           16B
            2           FF          256B
            3           FFF         4KB
            4           FFFF        64KB
            5           FFFFF       1MB
            6           FFFFFF      16MB
            7           FFFFFFF     256MB
            8           FFFFFFFF    4GB
            9           FFFFFFFFF   64GB
        '''
        if size_width == 0:
            print(':pv7', 'connection closed by client', self.url)
            self._socket.close()
            raise SocketClosed
        
        exact_size = int(self._socket.recv(size_width), 16)
        # notice: https://stackoverflow.com/a/17668009/9695911
        # trick: https://poe.com/s/2HbNCYsmKHIqZqoQ6Md3
        data_bytes = bytearray()
        while exact_size:
            fact_bytes = self._socket.recv(exact_size)
            data_bytes.extend(fact_bytes)
            exact_size -= len(fact_bytes)
        print(
            ':vi3',
            'recv',
            size_width,
            '{:X}'.format(exact_size),
            _shortify_message(data_bytes)
        )
        return data_bytes
    
    def send_close_event(self) -> None:
        self._socket.sendall(b'0')
    
    def sendall(self, msg: str) -> None:
        for datum in self._encode_message(msg):
            self._socket.sendall(datum)
    
    @staticmethod
    def _encode_message(msg: str) -> t.Iterator[bytes]:
        data_bytes = msg.encode()
        exact_size = '{:X}'.format(len(data_bytes))
        size_width = len(exact_size)
        assert 0 < size_width <= 9
        print(
            ':vi3',
            'send',
            size_width,
            exact_size,
            _shortify_message(data_bytes)
        )
        yield str(size_width).encode()
        yield exact_size.encode()
        yield data_bytes


# TEST
def _shortify_message(msg_in_bytes: bytes) -> str:
    if len(msg_in_bytes) < 40:
        return msg_in_bytes.decode()
    else:
        return '{}...{}'.format(
            msg_in_bytes[:40].decode(), msg_in_bytes[-40:].decode()
        )


class SocketClosed(Exception):
    pass
