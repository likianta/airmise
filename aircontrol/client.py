import typing as t
from asyncio import sleep

from sanic import Sanic
from sanic import Websocket as SanicWebSocket

from .serdes import dump
from .serdes import load

# client_runner = Sanic('aircontrol-client')
client_runner = Sanic.get_app('aircontrol-client', force_create=True)


@client_runner.websocket('/client')  # noqa
async def _on_message(_, ws: SanicWebSocket) -> None:
    while True:
        await sleep(1e-3)
        data = await ws.recv()
        code, kwargs = load(data)
        print(':vr2', '```python\n{}\n```'.format(code.strip()))
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
