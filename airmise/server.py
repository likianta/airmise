import typing as tp
from time import sleep

from lk_utils import run_cmd_args

from . import const
from .codec import decode
from .responder import Responder
from .socket_wrapper import Socket
from .util import fix_ctrl_c_keystroke
from .util import get_local_ip_address


class Server:
    connections: tp.Dict[int, Responder]
    host: str
    port: int
    verbose: bool
    _default_user_namespace: dict
    _socket: Socket

    def __init__(
        self,
        host: str = const.DEFAULT_HOST,
        port: int = const.DEFAULT_PORT,
        # _assignment: tp.Type[Responder] = Responder,
    ) -> None:
        self.connections = {}
        self.host = host
        self.port = port
        self.verbose = False
        self._default_user_namespace = {}
        self._socket = Socket()
        # self._assignment = _assignment

    def run(
        self,
        user_namespace: tp.Optional[dict] = None,
        # /,
        host: str = '',
        port: int = 0,
        verbose: tp.Union[bool, int] = 0,
        proxy_host: str = '',
        proxy_port: int = 0,
        proxy_secret: str = '',
    ) -> None:
        """
        Args:
            verbose:
                0 / False: Disabled.
                1 / True: Enable socket verbose.
                    See also `./socket_wrapper.py : Socket`.
                2: Enable both socket and server verbose.
                    See also `self._mainloop : [code] if self.verbose...`.
            proxy_host:
                We use bore (https://github.com/ekzhang/bore) to expose local
                server to remote (i.e. the public).
                Make sure the remote has run `bore server ...` and set proper
                whitelist.
            proxy_port:
                Used only if proxy_host is set.
                ~~The port 0 means random port on remote server.~~
            proxy_secret: Optional.
        """
        if user_namespace:
            self._default_user_namespace.update(user_namespace)

        self.verbose = bool(verbose == 2)
        self._socket.verbose = bool(verbose)
        self._socket.bind(host or self.host, port or self.port)
        self._socket.listen(20)

        fix_ctrl_c_keystroke()

        if proxy_host:
            if not proxy_port:
                proxy_port = port or self.port
            run_cmd_args(
                (
                    'bore',
                    'local',
                    ('-s', proxy_secret),
                    ('-t', proxy_host),
                    ('-p', str(proxy_port)),
                    str(proxy_port),
                ),
                verbose=True,
                blocking=False,
            )

        while True:
            conn = self._socket.accept()  # blocking
            self._handle_connection(conn)
            sleep(0.1)

    def _handle_connection(self, conn: Socket) -> None:
        assert decode(conn.recvall()) == (const.INTERNAL, 'hi', None)
        #   why does connector say hi?
        #   it helps server to distinguish the connector type. see practical
        #   usage in `./fast_reverse_proxy/proxy_roles.py:Router
        #   :_handle_connection`.
        endpoint = self.connections[conn.port] = Responder(
            conn, self._default_user_namespace
        )
        endpoint.mainloop(blocking=False)


def run_server(
    user_namespace: tp.Optional[dict] = None,
    # /,
    host: str = const.DEFAULT_HOST,
    port: int = const.DEFAULT_PORT,
    verbose: bool = False,
) -> None:
    if host == '0.0.0.0':
        print(
            '[green]server is working on: \n- {}\n- {}[/]'.format(
                'http://localhost:[u]{}[/]'.format(port),
                'http://{}:[u]{}[/]'.format(get_local_ip_address(), port),
            ),
            ':rp',
        )
    server = Server(host, port)
    server.run(user_namespace, verbose=verbose)
