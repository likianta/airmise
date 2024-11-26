import inspect
import re
import typing as t
from textwrap import dedent
from types import FunctionType
from uuid import uuid1

from websocket import WebSocket
from websocket import create_connection

from . import const
from .serdes import dump
from .serdes import load


class Client:
    host: str
    path: str
    port: int
    _ws: t.Optional[WebSocket]
    
    def __init__(self) -> None:
        self.host = const.DEFAULT_HOST
        self.port = const.DEFAULT_PORT
        self.path = '/'
        self._ws = None
        # atexit.register(self.close)
    
    @property
    def is_opened(self) -> bool:
        return bool(self._ws)
    
    @property
    def url(self) -> str:
        return 'ws://{}:{}/{}'.format(
            self.host, self.port, self.path.lstrip('/')
        )
    
    def config(self, host: str, port: int, path: str = '/') -> t.Self:
        if (self.host, self.port, self.path) == (host, port, path):
            return
        if self.is_opened:
            print('restart client to apply new config', ':pv')
            self.close()
        self.host, self.port, self.path = host, port, path
        return self
    
    def open(self, **kwargs) -> None:
        if self.is_opened:
            # print(
            #     ':v6p',
            #     'client already connected. if you want to reconnect, please '
            #     'use `reopen` method'
            # )
            return
        try:
            print(self.url, ':p')
            self._ws = create_connection(
                self.url, skip_utf8_validation=True, **kwargs
            )
            # assert self._ws.recv() == 'CONNECTED'
            #   see `.server2.Server._on_connect`
        except Exception:
            print(
                ':v8',
                'cannot connect to server via "{}"! '
                'please check if server online.'.format(self.url)
            )
            raise
        else:
            print(':v4', 'server connected', self.url)
    
    def close(self) -> None:
        if self.is_opened:
            print('close connection', ':v')
            self._ws.close(timeout=0.1)  # noqa
            self._ws = None
    
    def reopen(self) -> None:
        self.close()
        self.open()
    
    def run(
        self, source: t.Union[str, FunctionType], _iter: bool = False, **kwargs
    ) -> t.Any:
        if not self.is_opened:
            self.open()
        # TODO: check if source is a file path.
        if isinstance(source, str):
            # print(':vr2', '```python\n{}\n```'.format(dedent(source).strip()))
            code = _interpret_code(source)
        else:
            # print(':v', source)
            code = _interpret_func(source)
        # print(':r2', '```python\n{}\n```'.format(code.strip()))
        
        if _iter:
            def iterator(id: str) -> t.Iterator:
                encoded_data = dump((
                    '', None, {'is_iterator': True, 'id': id}
                ))
                while True:
                    self._send(encoded_data)
                    code, result = self._recv()
                    if code == const.YIELD:
                        yield result
                    elif code == const.YIELD_END:
                        break
                    else:
                        raise Exception(code, result)
            
            iter_id = uuid1().hex
            self._send(dump((
                code, kwargs or None, {'is_iterator': True, 'id': iter_id})
            ))
            code, result = self._recv()
            assert result == 'ready'
            return iterator(iter_id)
        else:
            self._send(dump((code, kwargs or None)))
        
        code, result = self._recv()
        if code == const.RETURN:
            return result
        elif code == const.CLOSED:  # TODO
            print(':v7', 'server closed connection')
            self.close()
    
    # TODO: there should be a better way
    def call(
        self, func_name: str, *args, _iter: bool = False, **kwargs
    ) -> t.Any:
        if args and kwargs:
            return self.run(
                'return {}(*args, **kwargs)'.format(func_name),
                args=args, kwargs=kwargs, _iter=_iter,
            )
        elif args:
            return self.run(
                'return {}(*args)'.format(func_name),
                args=args, _iter=_iter,
            )
        elif kwargs:
            return self.run(
                'return {}(**kwargs)'.format(func_name),
                kwargs=kwargs, _iter=_iter,
            )
        else:
            return self.run(
                'return {}()'.format(func_name), _iter=_iter,
            )
    
    def _send(self, encoded_data: str) -> None:
        try:
            self._ws.send(encoded_data)
        except ConnectionResetError:
            print(':v5', 'test auto reconnect', self.url)
            self.reopen()
            self._ws.send(encoded_data)
    
    def _recv(self) -> t.Tuple[int, t.Any]:
        code, result = load(self._ws.recv())
        if code == const.ERROR:
            raise Exception(result)
        else:
            return code, result


default_client = Client()
run = default_client.run
call = default_client.call
config = default_client.config
# connect = _default_client.open


def connect(host: str = None, port: int = None, path: str = None) -> None:
    if host: default_client.host = host
    if port: default_client.port = port
    if path: default_client.path = path
    default_client.open()


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
        
        # noinspection PyUnresolvedReferences
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
