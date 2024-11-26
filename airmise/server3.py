import json
import typing as t
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
        print(':v3', 'server set up websocket')
        ctx = {
            **self._default_user_namespace,
            '__ref__': {'__result__': None},
        }
        session_data_holder = {}
        
        ws = aiohttp.web.WebSocketResponse()
        await ws.prepare(req)
        
        def exec_() -> t.Any:
            ctx['__ref__']['__result__'] = None
            exec(code, ctx)
            return ctx['__ref__']['__result__']
        
        msg: aiohttp.WSMessage
        async for msg in ws:
            
            code, kwargs, options = load(msg.data)
            
            if code:
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
            
            if options:
                if options.get('is_iterator'):
                    iter_id = options['id']
                    if iter_id not in session_data_holder:
                        try:
                            session_data_holder[iter_id] = exec_()
                        except Exception as e:
                            response = dump(
                                (const.ERROR, ''.join(format_exception(e)))
                            )
                        else:
                            response = dump((const.RETURN, 'ready'))
                        await ws.send_str(response)
                    else:
                        try:
                            datum = next(session_data_holder[iter_id])
                            result = dump((const.YIELD, datum))
                        except StopIteration:
                            result = dump((const.YIELD_END, None))
                            session_data_holder.pop(iter_id)
                        except Exception as e:
                            result = dump(
                                (const.ERROR, ''.join(format_exception(e)))
                            )
                        await ws.send_str(result)
                else:
                    raise Exception(options)
            else:
                try:
                    result = exec_()
                except Exception as e:
                    result = dump((const.ERROR, ''.join(format_exception(e))))
                else:
                    result = dump((const.RETURN, result))
                await ws.send_str(result)
        
        print(':v7', 'server closed websocket')
        return ws
