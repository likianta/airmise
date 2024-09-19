import atexit
import inspect
import re
import typing as t
from textwrap import dedent
from types import FunctionType

from websocket import WebSocket
from websocket import create_connection  # pip install websocket-client

from .const import SERVER_DEFAULT_PORT
from .serdes import dump
from .serdes import load


class Client:
    host: str
    path: str
    port: int
    _ws: t.Optional[WebSocket]
    
    def __init__(
        self, host: str = None, port: int = None, path: str = '/'
    ) -> None:
        self._ws = None
        if host and port and path:
            self.config(host, port, path)
        atexit.register(self.close)
    
    @property
    def is_opened(self) -> bool:
        return bool(self._ws)
    
    @property
    def url(self) -> str:
        return 'ws://{}:{}/{}'.format(
            self.host, self.port, self.path.lstrip('/')
        )
    
    def config(self, host: str, port: int, path: str = '/') -> None:
        assert not self.is_opened, 'cannot config while connection is opened'
        self.host, self.port, self.path = host, port, path
    
    def open(self, **kwargs) -> None:
        if self.is_opened:
            print(
                ':v3p',
                'client already connected. if you want to reconnect, please '
                'use `reopen` method'
            )
            return
        try:
            print(self.url, ':p')
            self._ws = create_connection(self.url, **kwargs)
        except Exception:
            print(
                ':v4',
                'cannot connect to server via "{}"! '
                'please check if server online.'.format(self.url)
            )
            raise
        else:
            print(':v2', 'server connected', self.url)
    
    def close(self) -> None:
        if self.is_opened:
            print('close connection', ':vs')
            self._ws.close()
            self._ws = None
    
    def reopen(self) -> None:
        self.close()
        self.open()
    
    def run(self, source: t.Union[str, FunctionType], **kwargs) -> t.Any:
        assert self.is_opened
        # TODO: check if source is a file path.
        if isinstance(source, str):
            # print(':vr2', '```python\n{}\n```'.format(dedent(source).strip()))
            code = _interpret_code(source)
        else:
            # print(':v', source)
            code = _interpret_func(source)
        # print(':r2', '```python\n{}\n```'.format(code.strip()))
        self._ws.send(dump((code, kwargs or None)))
        code, result = load(self._ws.recv())
        if code == 0:
            return result
        else:
            raise Exception(result)


_default_client = Client(host='localhost', port=SERVER_DEFAULT_PORT)
run = _default_client.run


def connect(host: str = None, port: int = None, path: str = None):
    if host: _default_client.host = host
    if port: _default_client.port = port
    if path: _default_client.path = path
    _default_client.open()


# -----------------------------------------------------------------------------

def _interpret_code(raw_code: str, interpret_return: bool = True) -> str:
    """
    special syntax:
        memo <varname> := <value>
            get <varname>, if not exist, init with <value>.
        memo <varname> = <value>
            set <varname> to <value>. no matter if <varname> exists.
        memo <varname>
            get <varname>, assert it already exists.
        return <obj>
            store <obj> to `__result__`.

    example:
        raw_code:
            from random import randint
            def aaa() -> int:
                memo history := []
                history.append(randint(0, 9))
                return sum(history)
            return aaa()
        interpreted:
            from random import randint
            def aaa() -> int:
                if 'history' not in __ref__:
                    __ref__['history'] = []
                history = __ref__['history']
                history.append(randint(0, 9))
                return sum(history)
            __ref__['__result__'] = aaa()
            __ctx__.update(locals())
        note:
            `__ctx__` and `__ref__` are explained in
            `.server.Server._on_message`.
    """
    scope = []
    out = ''
    
    # var abbrs:
    #   ws: whitespaces
    #   linex: left stripped line
    #   __ctx__: context namespace. see also `.server.Server._context`
    
    for line in dedent(raw_code).splitlines():
        ws, linex = re.match(r'( *)(.*)', line).groups()
        indent = len(ws)
        
        if linex and scope and indent <= scope[-1]:
            scope.pop()
        if linex.startswith(('class ', 'def ')):
            scope.append(indent)
        
        if linex.startswith('memo '):
            a, b, c = re.match(r'memo (\w+)(?: (:)?= (.+))?', linex).groups()
            if b:
                out += (
                    '{}{} = __ref__["{}"] if "{}" in __ref__ else '
                    '__ref__.setdefault("{}", {})\n'
                    .format(ws, a, a, a, a, c)
                )
            elif c:
                out += '{}{} = __ref__["{}"] = {}\n'.format(ws, a, a, c)
            else:
                out += '{}{} = __ref__["{}"]\n'.format(ws, a, a)
        elif linex.startswith('return ') and not scope and interpret_return:
            out += '{}__ref__["__result__"] = {}\n'.format(ws, linex[7:])
        else:
            out += line + '\n'
    
    assert not scope
    return out


def _interpret_func(func: FunctionType) -> str:
    return '\n'.join((
        _interpret_code(inspect.getsource(func), interpret_return=False),
        '__ref__["__result__"] = {}(*args, **kwargs)'.format(func.__name__),
    ))
