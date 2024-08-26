"""
guide: docs/server-webapp-client-structure.zh.md
"""
import typing as t
from asyncio import sleep
from collections import defaultdict
from textwrap import dedent
from uuid import uuid1

from sanic import Sanic
from sanic import Websocket as SanicWebSocket

from . import const
from .client import Client
from .server import Server
from .util import get_local_ip_address


class LocalServer(Server):
    def __init__(self) -> None:
        super().__init__(
            'aircontrol-local-server',
            'localhost',
            const.WEBAPP_DEFAULT_PORT,
        )


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


class WebClient:
    def __init__(
        self,
        host: str = get_local_ip_address(),
        port: int = const.WEBAPP_DEFAULT_PORT
    ) -> None:
        id = uuid1().hex
        self.front_script = dedent(
            '''
            const web_host = window.location.hostname;
            // console.log(web_host);
            
            const web_client = new WebSocket(
                `ws://${{web_host}}:{port}/frontend/{id}`);
            const user_client = new WebSocket('ws://localhost:{port}/{id}');
            
            web_client.onmessage = (e) => {{ user_client.send(e.data); }}
            user_client.onmessage = (e) => {{ web_client.send(e.data); }}
            '''.format(port=port, id=id)
        )
        self.front_tag = '<script>\n{}\n</script>'.format(self.front_script)
        self.back_client = Client()
        self.back_client.url = 'ws://{}:{}/backend/{}'.format(host, port, id)
        self.back_client.open(lazy=True)
        self.run = self.back_client.run
        self.open = self.back_client.open
        self.reopen = self.back_client.reopen
        self.close = self.back_client.close
    
    # @property
    # def SCRIPT(self) -> str:
    #     return self.front_script
    
    # @property
    # def TAG(self) -> str:
    #     return self.front_tag
    
    @property
    def is_opened(self) -> bool:
        return self.back_client.is_opened
