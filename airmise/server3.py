import json
from textwrap import dedent
from traceback import format_exception

import aiohttp
import aiohttp.web
from lk_utils import timestamp

from . import const
from .serdes import dump
from .serdes import load


class Server:
    def __init__(self) -> None:
        self._app = aiohttp.web.Application()
        self._app.add_routes((aiohttp.web.get('/', self._ws_handler),))
        self._default_user_namespace = {}
    
    def run(
        self,
        host: str = '0.0.0.0',
        port: int = const.DEFAULT_PORT,
        debug: bool = False,  # TODO  # noqa
        user_namespace: dict = None,
    ) -> None:
        if user_namespace:
            self._default_user_namespace.update(user_namespace)
        aiohttp.web.run_app(self._app, host=host, port=port)
    
    async def _ws_handler(self, req: aiohttp.web.Request):
        print(':r', '[green dim]server set up websocket[/]')
        ctx = {
            **self._default_user_namespace,
            '__ref__': {'__result__': None},
        }
        
        ws = aiohttp.web.WebSocketResponse()
        await ws.prepare(req)
        
        msg: aiohttp.WSMessage
        async for msg in ws:
            code, kwargs = load(msg.data)
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
                result = dump((1, ''.join(format_exception(e))))
            else:
                result = dump((0, ctx['__ref__']['__result__']))
            await ws.send_str(result)
        
        print(':r', '[red dim]server closed websocket[/]')
        del ctx
        return ws
