import typing as t

from robyn import Robyn
from robyn import WebSocket

from .serdes import dump
from .serdes import load

app = Robyn(__file__)
ws = WebSocket(app, '/')

__ref__ = {}


@ws.on('connect')
async def _connect() -> str:
    print('connected', ':v2')
    return ''


# noinspection PyUnusedLocal
@ws.on('message')
async def _message(ws, msg: str) -> str:
    """
    notice: we cannot change the param signature of this function, otherwise
    robyn will raise an error.
    """
    print(msg, ':lv')
    code, kwargs = load(msg)
    # return dump(_execute1(code, kwargs))
    return dump(_execute2(code, kwargs))


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
    # FIXME: there is a weird bug that if we use
    #   `exec(msg, {'__ref__': __ref__}, __ref__)`, it may report name not
    #   defined error. it is likely related to <https://stackoverflow.com
    #   /questions/29979313/python-weird-nameerror-name-is-not-defined-in-an
    #   -exec-environment> but i don't know how to figure it out.
    #   so i use `exec(msg, globals(), globals())` as a workaround. see below.
    exec(code, globals(), globals())
    globals().update(__ref__)
    return __ref__['__result__']


@ws.on('close')
async def _close() -> str:
    print('closed', ':v2')
    return ''


class Server:
    
    @staticmethod
    def run(port: int = 2005) -> None:
        app.start(host='127.0.0.1', port=port)
