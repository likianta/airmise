from time import sleep

from ..socket_wrapper import Socket
from ..socket_wrapper import SocketClosed


class Repeater:
    upstream: Socket
    dnstream: Socket

    def __init__(self, upstream: Socket, dnstream: Socket) -> None:
        self.upstream = upstream
        self.dnstream = dnstream

    def mainloop(self, interval: float = 0.1) -> None:
        while True:
            try:
                raw_msg = self.upstream.recvall()  # blocking
            except SocketClosed:
                self.dnstream.send_close_event()
                self.dnstream.close()
                break
            else:
                self.dnstream.sendall(raw_msg)
                rsp = self.dnstream.recvall()  # blocking
                self.upstream.sendall(rsp)
                sleep(interval)
