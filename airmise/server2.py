import json
import os
import sys
import typing as t
from functools import cache
from textwrap import dedent
from traceback import format_exception

from lk_utils import fs
from lk_utils import timestamp

from . import const
from .serdes import dump
from .serdes import load

if 1:  # before importing robyn
    os.environ['ROBYN_CLI'] = 'true'
    if 'ROBYN_DEV_MODE' not in os.environ:
        os.environ['ROBYN_DEV_MODE'] = 'true'

if 2:  # import robyn
    from robyn import Config
    from robyn import Robyn
    from robyn import WebSocket
    # from robyn import config as robyn_config
    # from robyn.env_populator import load_vars
    # from robyn.reloader import setup_reloader


class _RobynConfig(Config):
    """
    ref:
        - robyn.argument_parser.Config
        - robyn.cli.run
    """
    
    # noinspection PyMissingConstructor
    def __init__(self) -> None:
        self.compile_rust_path = None
        self.create = False
        self.create_rust_file = None
        self.dev = os.getenv('ROBYN_DEV_MODE', 'true').lower() == 'true'
        #   if true, processes and workers must be 1.
        self.disable_openapi = True
        self.docs = False
        self.fast = False  # cannot be used together with `dev`.
        self.file_path = self.find_entrance()
        self.log_level = 'INFO'
        # self.log_level = 'WARN'
        self.open_browser = False
        self.processes = 1
        self.version = False
        self.workers = 1
        
        # load_vars(project_root=fs.parent(self.file_path))
        # setup_reloader(fs.parent(self.file_path), self.file_path)
    
    @staticmethod
    @cache
    def find_entrance() -> str:
        # print(sys.argv, sys.orig_argv)
        # sys.argv.clear()
        # sys.argv.extend(sys.orig_argv)
        if hasattr(sys.modules['__main__'], '__path__'):
            out = fs.abspath(sys.modules['__main__'].__path__[0])
        elif sys.orig_argv[1] == '-m':
            # out = fs.normpath('{}/{}/__main__.py'.format(
            #     os.getcwd(), sys.orig_argv[2])
            # )
            # out = '{}/{}'.format(os.getcwd(), '__main__')
            # #   it doesn't matter if '__main__' invalid, robyn just cares about
            # #   the entrance directory.
            out = __file__
        else:
            out = fs.abspath(sys.orig_argv[1])
        print(out, ':pv')
        return out


_robyn_app = Robyn(_RobynConfig.find_entrance(), _RobynConfig())


class Server:
    def __init__(self) -> None:
        self._app = _robyn_app
        ws = WebSocket(self._app, '/')
        ws.on('connect')(self._on_connect)
        ws.on('message')(self._on_message)
        ws.on('close')(self._on_close)
        self._default_user_namespace = {}
        self._user_contexts = {}
    
    def run(
        self,
        host: str = '0.0.0.0',
        port: int = const.SERVER_DEFAULT_PORT,
        debug: bool = False,
        user_namespace: dict = None,
    ) -> None:
        if host == 'localhost':
            # localhost is an alias to '127.0.0.1'. we must resolve it otherwise
            # robyn will raise an error says 'localhost is an invalid ip address
            # syntax'.
            host = '127.0.0.1'
        os.environ['ROBYN_DEV_MODE'] = 'true' if debug else 'false'
        if debug:
            self._app.config.dev = True
        if user_namespace:
            self._default_user_namespace.update(user_namespace)
        print('server is running at http://{}:{}'.format(host, port))
        # self._app.start(host=host, port=port)
        
        # ---------------------------------------------------------------------
        # FIXME: need twice `ctrl-c` to stop the server.
        # self._add_shutdown_handler()
        
        # t = Thread(target=self._app.start, kwargs={'host': host, 'port': port})
        # t.daemon = True
        # t.start()
        # while t.is_alive():
        #     t.join(0.4)
        
        # import multiprocessing as mp
        # p = mp.Process(
        #     target=self._app.start,
        #     kwargs={'host': host, 'port': port},
        #     daemon=True,
        # )
        # p.start()
        # while p.is_alive():
        #     print('alive', ':v')
        #     p.join(0.4)
        
        # from robyn.processpool import init_processpool
        # from robyn.processpool import run_processes
        # from robyn.robyn import SocketHeld
        # pool = init_processpool(
        #     self._app.directories,
        #     self._app.request_headers,
        #     self._app.router.get_routes(),
        #     self._app.middleware_router.get_global_middlewares(),
        #     self._app.middleware_router.get_route_middlewares(),
        #     self._app.web_socket_router.get_routes(),
        #     self._app.event_handlers,
        #     SocketHeld(host, port),
        #     self._app.config.workers,
        #     self._app.config.processes,
        #     self._app.response_headers,
        # )
        # print(pool)
        # run_processes(
        #     host,
        #     port,
        #     self._app.directories,
        #     self._app.request_headers,
        #     self._app.router.get_routes(),
        #     self._app.middleware_router.get_global_middlewares(),
        #     self._app.middleware_router.get_route_middlewares(),
        #     self._app.web_socket_router.get_routes(),
        #     self._app.event_handlers,
        #     self._app.config.workers,
        #     self._app.config.processes,
        #     self._app.response_headers,
        #     False,
        # )
        
        from robyn.events import Events
        from robyn.robyn import Server, SocketHeld
        from threading import Thread
        server = Server()
        for directory in self._app.directories:
            server.add_directory(*directory.as_list())
        server.apply_request_headers(self._app.request_headers)
        server.apply_response_headers(self._app.response_headers)
        for route in self._app.router.get_routes():
            route_type, endpoint, function, is_const = route
            server.add_route(route_type, endpoint, function, is_const)
        for middleware_type, middleware_function in (
            self._app.middleware_router.get_global_middlewares()
        ):
            server.add_global_middleware(
                middleware_type, middleware_function
            )
        for route_type, endpoint, function in (
            self._app.middleware_router.get_route_middlewares()
        ):
            server.add_middleware_route(route_type, endpoint, function)
        if Events.STARTUP in self._app.event_handlers:
            server.add_startup_handler(
                self._app.event_handlers[Events.STARTUP]
            )
        if Events.SHUTDOWN in self._app.event_handlers:
            server.add_shutdown_handler(
                self._app.event_handlers[Events.SHUTDOWN]
            )
        for endpoint in self._app.web_socket_router.get_routes():
            web_socket = self._app.web_socket_router.get_routes()[endpoint]
            server.add_web_socket_route(
                endpoint,
                web_socket.methods["connect"],
                web_socket.methods["close"],
                web_socket.methods["message"],
            )
        th = Thread(
            target=server.start,
            args=(SocketHeld(host, port), self._app.config.workers),
            daemon=True,
        )
        th.start()
        self._add_shutdown_handler()
        while th.is_alive():
            print('alive', ':v')
            th.join(0.4)
    
    @staticmethod
    def _add_shutdown_handler() -> None:
        def _force_shutting_down(sig: int = 2, *_) -> None:
            print('force shutting down', sig)
            os.kill(os.getpid(), sig)
        
        import signal
        signal.signal(signal.SIGINT, _force_shutting_down)
        # import atexit
        # atexit.register(_force_shutting_down)
    
    async def _on_connect(self, ws: t.Any, *_) -> str:
        print(':r', '[dim][green]server set up websocket[/] '
                    '({})[/]'.format(ws.id))
        self._user_contexts[ws.id] = {
            **self._default_user_namespace,
            '__ref__': {'__result__': None},
        }
        return 'CONNECTED'
    
    async def _on_message(self, ws: t.Any, msg: str) -> str:
        ctx = self._user_contexts[ws.id]
        '''
        what is `ctx` and `ref`?
        `ctx` is an implicit "background" information for the code to run.
        `ref` is a hook to preserve the key variables.
        for example, when code is doing `import numpy`, the `numpy` module will
        be stored in `ctx` so that the next code can access it.
        when code is doing `memo data = [123]`, the `data` will be stored in
        `ref` so that the next code can access it by `memo data`.
        TODO: we may remove `ref` and use `ctx` only in the future.
        '''
        
        code, kwargs = load(msg)
        print(':vr2', dedent(
            '''
            > *message at {}*

            ```python
            {}
            ```
            
            {}
            '''
        ).format(
            timestamp(),
            code.strip(),
            '```json\n{}\n```'.format(json.dumps(
                kwargs, default=str, ensure_ascii=False, indent=4
            )) if kwargs else ''
        ).strip())
        if kwargs:
            ctx.update(kwargs)
        
        ctx['__ref__']['__result__'] = None
        try:
            exec(code, ctx)
        except Exception as e:
            return dump((1, ''.join(format_exception(e))))
        else:
            return dump((0, ctx['__ref__']['__result__']))
    
    async def _on_close(self, ws: t.Any, *_) -> str:
        # print(ws.id in self._user_contexts, ':v')
        if ws.id in self._user_contexts:
            print(':r', '[dim][red]server closed websocket[/] '
                        '({})[/]'.format(ws.id))
            del self._user_contexts[ws.id]
        # else already closed
        return 'CLOSED'
