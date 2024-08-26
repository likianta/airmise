import atexit
import inspect
import re
import typing as t
from textwrap import dedent
from types import FunctionType

from lk_utils import run_new_thread
from lk_utils.subproc import ThreadBroker
from websocket import WebSocket
from websocket import create_connection  # pip install websocket-client

from .serdes import dump
from .serdes import load


class Client:
    url: str
    _thread: t.Optional[ThreadBroker]
    _ws: t.Optional[WebSocket]
    
    def __init__(self) -> None:
        self._ws = None
        self._thread = None
        atexit.register(self.close)
    
    def connect(self, host: str, port: int, lazy: bool = True) -> None:
        self.url = 'ws://{}:{}'.format(host, port)
        self.open(lazy)
    
    @property
    def is_opened(self) -> bool:
        return bool(self._ws)
    
    def open(self, lazy: bool = False) -> None:
        def connect() -> None:
            try:
                self._ws = create_connection(self.url)
            except Exception:
                print(':v4', self.url)
                raise
            else:
                print(':v2', 'executor is connected to server', self.url)
            self._thread = None
        
        if lazy:
            self._thread = run_new_thread(connect)
        else:
            if self._thread:
                self._thread.join()
                assert self._ws
            else:
                connect()
    
    def close(self) -> None:
        if self._ws:
            print('close connection', ':vs')
            self._ws.close()
            self._ws = None
    
    def reopen(self) -> None:
        self.close()
        self.open()
    
    def run(self, source: t.Union[str, FunctionType], **kwargs) -> t.Any:
        if not self.is_opened:  # lazily open connection.
            self.open()
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
                if 'history' not in __ctx__:
                    __ctx__['history'] = []
                history = __ctx__['history']
                history.append(randint(0, 9))
                return sum(history)
            __result__ = aaa()
            __ctx__.update(globals())
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
                    '{}{} = __ctx__["{}"] if "{}" in __ctx__ else '
                    '__ctx__.setdefault("{}", {})\n'
                    .format(ws, a, a, a, a, c)
                )
            elif c:
                out += '{}{} = __ctx__["{}"] = {}\n'.format(ws, a, a, c)
            else:
                out += '{}{} = __ctx__["{}"]\n'.format(ws, a, a)
        elif linex.startswith('return ') and not scope and interpret_return:
            out += '{}__result__ = {}\n'.format(ws, linex[7:])
        else:
            out += line + '\n'
    if interpret_return:
        out += '__ctx__.update(globals())'
    
    assert not scope
    return out


def _interpret_func(func: FunctionType) -> str:
    return '\n'.join((
        _interpret_code(inspect.getsource(func), interpret_return=False),
        '__result__ = {}(*args, **kwargs)'.format(func.__name__),
        '__ctx__.update(globals())',
    ))
