"""
docs/webapp-work-model.zh.md
"""
import typing as t
from asyncio import sleep
from collections import defaultdict
from textwrap import dedent
from uuid import uuid1

from lk_utils import timestamp
from sanic import Sanic
from sanic import Websocket as SanicWebSocket

from . import const
from .client import Client
from .serdes import dump
from .serdes import load
from .util import get_local_ip_address


class UserLocalServer:
    def __init__(self, name: str = 'aircontrol-local-server') -> None:
        self._runner = Sanic.get_app(name, force_create=True)
        self._runner.websocket('/<client_id>')(self._on_message)  # noqa
        self._all_users_namespace = defaultdict(self._init_user_namespace)
        self._default_user_namespace = None
    
    def _init_user_namespace(self) -> dict:
        out = {'__result__': None}
        if self._default_user_namespace:
            out.update(self._default_user_namespace)
        return out
    
    def run(self, debug: bool = False, user_namespace: dict = None) -> None:
        self._default_user_namespace = user_namespace
        self._runner.run(
            host='localhost',
            port=const.WEBAPP_DEFAULT_PORT,
            auto_reload=debug,
            access_log=False,
            single_process=True,  # FIXME
        )
    
    async def _on_message(self, _, ws: SanicWebSocket, client_id: str) -> None:
        context = self._all_users_namespace[client_id]
        
        while True:
            await sleep(1e-3)
            data = await ws.recv()
            code, kwargs = load(data)
            
            print(':vr2', dedent(
                '''
                > *message at {}*

                ```python
                {}
                ```
                '''
            ).format(timestamp(), code.strip()))
            if kwargs:
                print(kwargs, ':vl')
                context.update(kwargs)
            
            exec(code, context, {'__ctx__': context})
            result = context['__result__']
            await ws.send(dump(result))


class WebServer:
    class _Undefined:
        pass
    
    def __init__(
        self,
        name: str = 'aircontrol-web-server',
        host: str = get_local_ip_address(),
        port: int = const.WEBAPP_DEFAULT_PORT,
    ) -> None:
        self.host = host
        self.port = port
        self.is_front_online = False
        # TODO: queue is not complete.
        self._requests = defaultdict(lambda: t.cast(str, self._Undefined))
        self._responses = defaultdict(lambda: t.cast(str, self._Undefined))
        # self._message_queue = defaultdict(lambda: (deque(), deque()))
        # #   {client_id: (requests, responses), ...}
        # #       requests: [(id, req), ...]
        # #       responses: [(id, rsp), ...]
        self._runner = Sanic.get_app(name, force_create=True)
        self._runner.websocket('/frontend/<client_id>')(self._frontend)  # noqa
        self._runner.websocket('/backend/<client_id>')(self._backend)  # noqa
    
    def run(self, debug: bool = False) -> None:
        self._runner.run(
            host=self.host,
            port=self.port,
            auto_reload=debug,
            access_log=False,
            single_process=True,
        )
    
    async def _frontend(self, _, ws: SanicWebSocket, client_id: str) -> None:
        self.is_front_online = True
        while True:
            while self._requests[client_id] is self._Undefined:
                await sleep(2e-3)
            req: str = self._requests.pop(client_id)
            await ws.send(req)
            rsp: str = await ws.recv()
            self._responses[client_id] = rsp
    
    async def _backend(self, _, ws: SanicWebSocket, client_id: str) -> None:
        while True:
            req = await ws.recv()  # blocking
            self._requests[client_id] = req
            while self._responses[client_id] is self._Undefined:
                await sleep(2e-3)
            else:
                rsp: str = self._responses.pop(client_id)
                await ws.send(rsp)
    
    '''
    async def _frontend(self, _, ws: SanicWebSocket, client_id: str) -> None:
        self.fontend_active = True
        requests, responses = self._message_queue[client_id]
        while True:
            await sleep(2e-3)
            if requests:
                id, data = requests.popleft()
                print(id, data, ':v')
                await ws.send(data)
                resp = await ws.recv()
                responses.append((id, resp))

    async def _backend(self, _, ws: SanicWebSocket, client_id: str) -> None:
        requests, responses = self._message_queue[client_id]
        while True:
            if data := await ws.recv(2e-3):
                requests.append(load(data))
            while responses:
                await ws.send(dump(responses.popleft()))
            await sleep(2e-3)
    '''


class WebClient(Client):
    front_func: str
    front_pyfunc: str
    front_pyscript: str
    front_pytag: str
    front_script: str
    front_tag: str
    session_id: str
    
    def __init__(self, session_id: str = None) -> None:
        super().__init__()
        self.session_id = session_id or uuid1().hex
    
    def connect(self, host: str, port: int, lazy: bool = True) -> None:
        self.front_func = dedent(
            '''
            function init_aircontrol_websockets() {
                const user_client = new WebSocket('ws://localhost:<port>/<id>');
                const host_client = new WebSocket(
                    `ws://${window.location.hostname}:<port>/frontend/<id>`);
                );
                host_client.onmessage = (e) => { user_client.send(e.data); }
                user_client.onmessage = (e) => { host_client.send(e.data); }
            }
            '''
            .replace('<port>', str(port))
            .replace('<id>', self.session_id)
        )
        self.front_script = '{}\n{}'.format(
            self.front_func,
            'init_aircontrol_websockets();',
        )
        self.front_tag = '<script>\n{}\n</script>'.format(self.front_script)
        
        self.front_pyfunc = dedent(
            '''
            # executed by brython.
            from browser import window
            
            def init_aircontrol_websockets() -> None:
                user_client = window.WebSocket.new(
                    f'ws://localhost:<port>/<id>'
                )
                host_client = window.WebSocket.new(
                    f'ws://{}:<port>/frontend/<id>'.format(
                        window.location.hostname
                    )
                )
                
                def _transfer_to_user(e) -> None:
                    user_client.send(e.data)
                    
                def _transfer_to_host(e) -> None:
                    host_client.send(e.data)
                    
                host_client.onmessage = _transfer_to_user
                user_client.onmessage = _transfer_to_host
            '''
            .replace('<port>', str(port))
            .replace('<id>', self.session_id)
        )
        self.front_pyscript = '{}\n{}'.format(
            self.front_pyfunc,
            'init_aircontrol_websockets()',
        )
        self.front_pytag = '<script type="text/python">\n{}\n</script>'.format(
            self.front_pyscript
        )
        
        self.url = 'ws://{}:{}/backend/{}'.format(host, port, self.session_id)
        if lazy:
            self._todo = self.open
        else:
            self.open()
