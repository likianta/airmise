import atexit
import inspect
import re
import typing as t
from textwrap import dedent
from types import FunctionType

# from lk_utils import load as load_file
from websockets.sync.client import connect

from .serdes import dump
from .serdes import load


class Client:
    
    def __init__(self, port: int = 2005, open_now: bool = True) -> None:
        self.port = port
        self._conn = None
        if open_now: self.open()
        atexit.register(self.close)
    
    @property
    def is_opened(self) -> bool:
        return bool(self._conn)
    
    def open(self) -> None:
        self._conn = connect(f'ws://localhost:{self.port}')
        self._conn.recv()  # consume message from on_connect handler
    
    def close(self) -> None:
        if self._conn:
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
        # TODO: check if source is a file path.
        if isinstance(source, str):
            print(':vr2', '```python\n{}\n```'.format(dedent(source).strip()))
            code = _interpret_code(source)
        else:
            print(':v', source)
            code = _interpret_function(source)
        # print(':r2', '```python\n{}\n```'.format(code.strip()))
        self._conn.send(dump((code, kwargs)))
        return load(self._conn.recv())


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
    out = ''
    for line in dedent(raw_code).splitlines():
        if line.lstrip().startswith('memo '):
            whitespaces = re.match(' *', line).group()
            a, b, c = re.match(
                r'memo (\w+)(?: (:)?= (.+))?',
                line
            ).groups()
            if b:
                out += (
                    '{}{} = __ref__["{}"] if "{}" in __ref__ else '
                    '__ref__.setdefault("{}", {})\n'
                    .format(whitespaces, a, a, a, a, c)
                )
            elif c:
                out += '{}{} = __ref__["{}"] = {}\n' \
                    .format(whitespaces, a, a, c)
            else:
                out += '{}{} = __ref__["{}"]\n'.format(whitespaces, a, a)
        elif line.lstrip().startswith('return ') and interpret_return:
            whitespaces = re.match(' *', line).group()
            out += '{}__ref__["__result__"] = {}\n' \
                .format(whitespaces, line.lstrip()[7:])
        else:
            out += line + '\n'
    return out


def _interpret_function(func: FunctionType) -> str:
    return '{}\n{}'.format(
        _interpret_code(inspect.getsource(func), interpret_return=False),
        '__ref__["__result__"] = {}(*args, **kwargs)'.format(func.__name__)
    )
