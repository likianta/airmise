import json
from asyncio import sleep
from textwrap import dedent
from traceback import format_exception

from lk_utils import timestamp
from sanic import Sanic
from sanic import Websocket as SanicWebSocket

from . import const
from .serdes import dump
from .serdes import load


class Server:
    def __init__(self, name: str = 'aircontrol-server') -> None:
        self._runner = Sanic.get_app(name, force_create=True)
        self._runner.websocket('/')(self._on_message)  # noqa
        self._default_user_namespace = {}
    
    def run(
        self,
        host: str = '0.0.0.0',
        port: int = const.SERVER_DEFAULT_PORT,
        debug: bool = False,
        user_namespace: dict = None,
    ) -> None:
        if user_namespace:
            self._default_user_namespace.update(user_namespace)
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
        ctx = {
            **self._default_user_namespace,
            '__ref__': {'__result__': None},
        }
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
                await ws.send(dump((1, ''.join(format_exception(e)))))
            else:
                await ws.send(dump((0, ctx['__ref__']['__result__'])))
