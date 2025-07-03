import atexit
import inspect
import re
import typing as t
from textwrap import dedent
from types import FunctionType
from uuid import uuid1

from . import const
from .serdes import dump
from .serdes import load
from .socket_wrapper import Socket


class Client:
    host: str
    port: int
    _socket: t.Optional[Socket]
    
    def __init__(
        self, 
        host: str = const.DEFAULT_HOST, 
        port: int = const.DEFAULT_PORT,
    ) -> None:
        self.host = host
        self.port = port
        self._socket = None
        atexit.register(self.close)
    
    @property
    def is_opened(self) -> bool:
        return bool(self._socket)
    
    @property
    def url(self) -> str:
        return 'tcp://{}:{}'.format(self.host, self.port)
    
    def config(self, host: str, port: int, verbose: bool = None) -> t.Self:
        if (self.host, self.port) != (host, port):
            self.host, self.port = host, port
            if self.is_opened:
                print('restart client to apply new config', ':pv')
                self.reopen()
                if verbose is not None:
                    self._socket.verbose = verbose
        return self
    
    def open(self) -> None:
        if self.is_opened:
            # print(
            #     ':v6p',
            #     'client already connected. if you want to reconnect, please '
            #     'use `reopen` method'
            # )
            return
        self._socket = Socket()
        self._socket.connect(self.host, self.port)
    
    def close(self) -> None:
        if self.is_opened:
            print('close connection', ':v')
            self._socket.send_close_event()
            self._socket.close()
            self._socket = None
    
    def reopen(self) -> None:
        self.close()
        self.open()
    
    def exec(
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
        
        def iterate(id: str) -> t.Iterator:
            encoded_data = dump((
                '', None, {'is_iterator': True, 'id': id}
            ))
            while True:
                self._socket.sendall(encoded_data)
                code, result = self._recv()
                if code == const.YIELD:
                    yield result
                elif code == const.YIELD_OVER:
                    break
                else:
                    raise Exception(code, result)
        
        if _iter:
            uid = uuid1().hex
            self._socket.sendall(dump((
                code, kwargs or None, {'is_iterator': True, 'id': uid})
            ))
            code, result = self._recv()
            assert result == 'ready'
            return iterate(uid)
        else:
            self._socket.sendall(dump((code, kwargs or None, None)))
        
        code, result = self._recv()
        if code == const.NORMAL_OBJECT:
            return result
        elif code == const.SPECIAL_OBJECT:
            from .remote_control import RemoteCall
            return RemoteCall(remote_object_id=result)
        elif code == const.ITERATOR:
            # result is an id.
            return iterate(result)
        elif code == const.CLOSED:
            print(':v7', 'server closed connection')
            self.close()
        else:
            raise Exception(code, result)
    
    # TODO: there should be a better way
    def call(
        self, func_name: str, *args, _iter: bool = False, **kwargs
    ) -> t.Any:
        if args and kwargs:
            return self.exec(
                'return {}(*args, **kwargs)'.format(func_name),
                args=args, kwargs=kwargs, _iter=_iter,
            )
        elif args:
            return self.exec(
                'return {}(*args)'.format(func_name),
                args=args, _iter=_iter,
            )
        elif kwargs:
            return self.exec(
                'return {}(**kwargs)'.format(func_name),
                kwargs=kwargs, _iter=_iter,
            )
        else:
            return self.exec(
                'return {}()'.format(func_name), _iter=_iter,
            )
    
    def _recv(self) -> t.Tuple[int, t.Any]:
        code, result = load(self._socket.recvall().decode())
        if code == const.ERROR:
            raise Exception(result)
        else:
            return code, result


default_client = Client()
exec = default_client.exec
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
    out = ''
    
    # var abbrs:
    #   ws: whitespaces
    #   linex: left stripped line
    #   __ctx__: context namespace. see also `.server.Server._context`
    
    if '\n' in raw_code:
        scope = []
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
    else:
        if raw_code.startswith('return '):
            out = '__ref__["__result__"] = {}\n'.format(raw_code[7:])
        else:
            out = '__ref__["__result__"] = {}\n'.format(raw_code)
    
    return out


def _interpret_func(func: FunctionType) -> str:
    return '\n'.join((
        _interpret_code(inspect.getsource(func), interpret_return=False),
        '__ref__["__result__"] = {}(*args, **kwargs)'.format(func.__name__),
    ))
