import atexit
import inspect
import re
import typing as t
from textwrap import dedent
from types import FunctionType

from websockets.sync.client import ClientConnection
from websockets.sync.client import connect

from . import const
from .serdes import dump
from .serdes import load


class Executor:
    port: int
    _conn: t.Optional[ClientConnection]
    
    def __init__(self, url: str) -> None:
        assert url.startswith(('ws://', 'wss://'))
        self.url = url
        self._conn = None
        atexit.register(self.close)
    
    @property
    def is_opened(self) -> bool:
        return bool(self._conn)
    
    def open(self) -> None:
        self._conn = connect(self.url)
    
    def close(self) -> None:
        if self._conn:
            print('close connection', ':vs')
            self._conn.close()
            self._conn = None
    
    def reopen(self) -> None:
        self.close()
        self.open()
    
    def run(
        self,
        source: t.Union[str, FunctionType],
        kwargs: dict = None
    ) -> t.Any:
        if not self.is_opened:  # lazily open connection.
            self.open()
        # TODO: check if source is a file path.
        if isinstance(source, str):
            print(':vr2', '```python\n{}\n```'.format(dedent(source).strip()))
            code = _interpret_code(source)
        else:
            print(':v', source)
            code = _interpret_func(source)
        # print(':r2', '```python\n{}\n```'.format(code.strip()))
        self._conn.send(dump((code, kwargs)))
        return load(self._conn.recv())


server_call = Executor(f'ws://localhost:{const.SERVER_DEFAULT_PORT}/server').run
client_call = Executor(f'ws://localhost:{const.CLIENT_DEFAULT_PORT}/client').run


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

    example 1:
        raw_code:
            from random import randint
            def aaa() -> int:
                memo history? = []
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
    """
    scope = []
    out = ''
    
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
    return '{}\n{}'.format(
        _interpret_code(inspect.getsource(func), interpret_return=False),
        '__ref__["__result__"] = {}(*args, **kwargs)'.format(func.__name__)
    )
