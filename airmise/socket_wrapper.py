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
        print(conn, addr, ':v')
        new_socket = Socket(_socket=conn, _url='tcp://{}:{}'.format(*addr))
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
        digits = int(self._socket.recv(1))
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
        if digits == 0:
            print(':pv7', 'connection closed by client', self.url)
            self._socket.close()
            raise SocketClosed
        
        exact_size = int(self._socket.recv(digits), 16)
        data_bytes = self._socket.recv(exact_size)
        return data_bytes
    
    def send_close_event(self) -> None:
        self._socket.send(b'0')
    
    def sendall(self, msg: str) -> None:
        for datum in self._encode_message(msg):
            self._socket.send(datum)
            
    @staticmethod
    def _encode_message(msg: str) -> t.Iterator[bytes]:
        msg_in_bytes = msg.encode()
        exact_size = '{:X}'.format(len(msg_in_bytes))
        size_in_digits = len(exact_size)
        yield str(size_in_digits).encode()
        yield exact_size.encode()
        yield msg_in_bytes


class SocketClosed(Exception):
    pass
