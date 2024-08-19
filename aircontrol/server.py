import typing as t
from asyncio import sleep
from textwrap import dedent

from lk_utils import timestamp
from sanic import Sanic
from sanic import Websocket as SanicWebSocket
from tornado.web import decode_signed_value

from . import const
from .serdes import dump
from .serdes import load
from .util import get_local_ip_address

server_runner = Sanic.get_app('aircontrol-server', force_create=True)


def run_server(
    host: str = get_local_ip_address(),
    port: int = const.SERVER_DEFAULT_PORT,
    debug: bool = False,
    user_namespace: dict = None,
) -> None:
    if user_namespace:
        globals().update(user_namespace)
    server_runner.run(
        host=host,
        port=port,
        auto_reload=debug,
        access_log=False,
        single_process=True,
        #   FIXME: why multi-process does not work?
    )


# -----------------------------------------------------------------------------

@server_runner.websocket('/')  # noqa
async def _on_message(_, ws: SanicWebSocket) -> None:
    print(':r', '[green dim]server side setups websocket[/]')
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
        if kwargs: print(kwargs, ':vl')
        result = _execute2(code, kwargs)
        await ws.send(dump(result))


__ref__ = {}


def _execute1(code: str, kwargs: dict) -> t.Any:
    __ref__['__result__'] = None
    exec(code, {'__ref__': __ref__}, kwargs)
    return __ref__['__result__']


def _execute2(code: str, kwargs: t.Optional[dict]) -> t.Any:
    """
    FIXME: there is a weird bug that if we use `_execute1`, it may report name
        not defined error. it is likely related to <https://stackoverflow.com
        /questions/29979313/python-weird-nameerror-name-is-not-defined-in-an
        -exec-environment> but i don't know how to figure it out.
        so i use `exec(code, globals(), globals())` as a workaround. see below.
    """
    if kwargs:
        globals().update(kwargs)
    __ref__['__result__'] = None
    exec(code, globals(), globals())
    globals().update(__ref__)
    return __ref__['__result__']


# -----------------------------------------------------------------------------

def release_client(id: str) -> None:
    pass
