from asyncio import sleep
from textwrap import dedent

from lk_utils import timestamp
from sanic import Sanic
from sanic import Websocket as SanicWebSocket

from . import const
from .serdes import dump
from .serdes import load
from .util import get_local_ip_address


class Server:
    def __init__(
        self,
        name: str = 'aircontrol-server',
    ) -> None:
        self._runner = Sanic.get_app(name, force_create=True)
        # noinspection PyCallingNonCallable
        self._runner.websocket('/')(self._on_message)
        self._context = {'__result__': None}
    
    def run(
        self,
        host: str = get_local_ip_address(),
        port: int = const.SERVER_DEFAULT_PORT,
        debug: bool = False,
        user_namespace: dict = None,
    ) -> None:
        if user_namespace:
            self._context.update(user_namespace)
        self._runner.run(
            host=host,
            port=port,
            auto_reload=debug,
            access_log=False,
            single_process=True,
            #   FIXME: why multi-process does not work?
        )
    
    async def _on_message(self, _, ws: SanicWebSocket) -> None:
        print(':r', '[green dim]server side setups websocket[/]')
        context = self._context.copy()
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


server = Server()
run_server = server.run
