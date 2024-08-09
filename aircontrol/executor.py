import atexit
import inspect
import re
import typing as t
from textwrap import dedent
from time import sleep
from types import FunctionType

from lk_utils import run_new_thread
from lk_utils.subproc import ThreadBroker
from websockets.sync.client import ClientConnection
from websockets.sync.client import connect

from . import const
from .serdes import dump
from .serdes import load
from .server import get_local_ip_address


class Executor:
    url: str
    _conn: t.Optional[ClientConnection]
    _thread: t.Optional[ThreadBroker]
    
    def __init__(self, url: str) -> None:
        assert url.startswith(('ws://', 'wss://'))
        self.url = url
        self._conn = None
        self._thread = None
        atexit.register(self.close)
    
    @property
    def is_opened(self) -> bool:
        return bool(self._conn)
    
    def open(self, lazy: bool = False) -> None:
        def do_connect() -> None:
            try:
                self._conn = connect(self.url)
            except Exception:
                print(':v4', self.url)
                raise
            self._thread = None
        
        if lazy:
            self._thread = run_new_thread(do_connect)
        else:
            if self._thread:
                self._thread.join()
                assert self._conn
            else:
                do_connect()
    
    def close(self) -> None:
        if self._conn:
            print('close connection', ':vs')
            self._conn.close()
            self._conn = None
    
    def reopen(self) -> None:
        self.close()
        self.open()
    
    def run(self, source: t.Union[str, FunctionType], **kwargs) -> t.Any:
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
        self._conn.send(dump((code, kwargs or None)))
        return load(self._conn.recv())


class WebappExecutor(Executor):
    def run(self, source: t.Union[str, FunctionType], **kwargs) -> t.Any:
        if not self.is_opened:  # lazily open connection.
            self.open()
        if isinstance(source, str):
            print(':vr2', '```python\n{}\n```'.format(dedent(source).strip()))
            code = _interpret_code(source)
        else:
            print(':v', source)
            code = _interpret_func(source)
        # print(':r2', '```python\n{}\n```'.format(code.strip()))
        self._conn.send(dump((code, kwargs or None)))
        while True:
            resp = self._conn.recv()
            #   `<id>:working...` | str serialized_data
            if resp.endswith(':working...'):
                sleep(2e-3)
                task_id = resp.split(':')[0]
                self._conn.send(f'{task_id}:done?')
            else:
                return load(resp)


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


# -----------------------------------------------------------------------------

client = Executor('ws://{}:{}/client'.format(
    'localhost', const.CLIENT_DEFAULT_PORT
))
# FIXME: make sure server ip is visible in client side.
#   currently we are using local ip address, which is visible across local
#   network (that means clients should join the same local network as server).
#   for furtuer usage, especially in production, we should use a public ip
#   address.
server = Executor('ws://{}:{}/server'.format(
    get_local_ip_address(), const.SERVER_DEFAULT_PORT
))
webapp = WebappExecutor('ws://{}:{}/webapp'.format(
    get_local_ip_address(), const.SERVER_DEFAULT_PORT
))

# -----------------------------------------------------------------------------

_default_executor = webapp


def replace_default_executor(exe: Executor) -> None:
    global _default_executor
    _default_executor = exe


def run(source: t.Union[str, FunctionType], **kwargs) -> t.Any:
    return _default_executor.run(source, **kwargs)
