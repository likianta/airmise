import typing as tp
from .codec import decode
from .codec import encode
from .responder import Responder
from .socket_wrapper import Socket
# from lk_utils import run_new_thread
# from .server import Server


class Worker:
    def __init__(self, port: int, context: tp.Optional[dict] = None) -> None:
        self.port = port
        self.context = context

    # def start(self, context: dict, blocking: bool = True):
    #     svr = Server(port=self.port)
    #     if blocking:
    #         svr.run(context)
    #     else:
    #         run_new_thread(svr.run, context)

    def expose_to_public_via_proxy_server(
        self,
        proxy_server_host: str,
        proxy_server_port: int,
        callback: tp.Optional[tp.Callable] = None,
    ) -> None:
        """
        illustration:
                +-------1-> tunnel_port_manager (public) --+
                |                                          |
            local_port (private) <-3-> tunnel_port <-2-----+
        """
        sock = Socket()
        sock.bind('0.0.0.0', self.port)
        sock.connect(proxy_server_host, proxy_server_port)

        sock.sendall(encode(('register', self.port)))
        type, data = decode(sock.recvall())
        assert type == 'connection_established'

        tunnel_port = data
        print(
            'local_port: [magenta]{}[/] <---> tunnel_port: [green]{}[/]'.format(
                self.port, tunnel_port
            ),
            ':r',
        )
        res = Responder(sock, self.context or {})
        if callback:
            callback(tunnel_port, res)
        res.mainloop()  # blocking
