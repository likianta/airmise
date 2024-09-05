import atexit
import inspect
import re
import typing as t
from textwrap import dedent
from types import FunctionType

from websocket import WebSocket
from websocket import create_connection  # pip install websocket-client

from .serdes import dump
from .serdes import load


class Client:
    url: str
    _ws: t.Optional[WebSocket]
    
    def __init__(self, **kwargs) -> None:
        self._ws = None
        self._todo = None
        if kwargs: self.config(**kwargs)
        atexit.register(self.close)
        
    def config(self, host: str, port: int, path: str = '/') -> None:
        self.url = 'ws://{}:{}/{}'.format(host, port, path.lstrip('/'))
    
    # DELETE
    def connect(
        self,
        host: str,
        port: int,
        path: str = '/',
        lazy: bool = True
    ) -> None:
        self.url = 'ws://{}:{}/{}'.format(host, port, path.lstrip('/'))
        if lazy:
            self._todo = self.open
        else:
            self.open()
    
    @property
    def is_opened(self) -> bool:
        if self._todo:
            print(':v', 'open now', self.url)
            self._todo()
            self._todo = None
        return bool(self._ws)
    
    def open(self, **kwargs) -> None:
        try:
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
        if self._ws:
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
        return load(self._ws.recv())


client = Client()
connect = client.connect
run = client.run


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
    if interpret_return:
        out += '__ctx__.update(locals())'
    
    assert not scope
    return out


def _interpret_func(func: FunctionType) -> str:
    return '\n'.join((
        _interpret_code(inspect.getsource(func), interpret_return=False),
        '__ref__["__result__"] = {}(*args, **kwargs)'.format(func.__name__),
        '__ctx__.update(locals())',
    ))
