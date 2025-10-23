import inspect
import re
import sys
import typing as t
from textwrap import dedent
from types import FunctionType

from . import const
from .codec2 import decode
from .codec2 import encode
from .socket_wrapper import Socket


class Master:
    def __init__(self, socket: Socket) -> None:
        self.socket = socket
    
    def call(self, func_name: str, *args, **kwargs) -> t.Any:
        self._send(
            const.CALL_FUNCTION,
            func_name,
            {'args': args, 'kwargs': kwargs} if args or kwargs else None,
        )
        return self._recv()
    
    def exec(
        self,
        source: t.Union[str, FunctionType],
        delegate: bool = False,
        **kwargs
    ) -> t.Any:
        # TODO: check if source is a file path.
        if isinstance(source, str):
            # print(':vr2', '```python\n{}\n```'.format(dedent(source).strip()))
            code = _interpret_code(source)
        else:
            # print(':v', source)
            code = _interpret_func(source)
        
        # print(':r2', '```python\n{}\n```'.format(code.strip()))
        
        self._send(
            const.DELEGATE if delegate else const.NORMAL,
            code,
            kwargs or None
        )
        return self._recv()
    
    def set_passive(self, user_namespace: dict = None) -> None:
        from .slave import Slave
        self._send(const.INTERNAL, 'switch_roleplay')
        s = Slave(self.socket, user_namespace)
        s.active = True
        s.mainloop()  # blocking
    
    def _recv(self) -> t.Any:
        code, result = decode(self.socket.recvall())
        if code == const.CLOSED:
            print(':v7', 'server closed connection')
            sys.exit()
        elif code == const.DELEGATE:
            from .remote_control import RemoteCall
            return RemoteCall(remote_object_id=result)
        elif code == const.ERROR:
            raise Exception(result)
        elif code == const.ITERATOR:
            # result is an id.
            return self._iterate(result)
        elif code == const.NORMAL:
            return result
        elif code == const.YIELD:
            return result
        elif code == const.YIELD_OVER:
            return StopIteration
    
    def _iterate(self, id: str) -> t.Iterator:
        _args = {'is_iterator': True, 'id': id}
        while True:
            self._send(const.ITERATOR, None, _args)
            code, result = decode(self.socket.recvall())
            if code == const.YIELD:
                yield result
            elif code == const.YIELD_OVER:
                break
            else:
                raise Exception(code, result)
    
    def _send(
        self,
        flag: int,
        code: t.Optional[str],
        args: t.Optional[dict] = None
    ) -> None:
        self.socket.sendall(encode((flag, code, args)))
    

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
                a, b, c = re.match(
                    r'memo (\w+)(?: (:)?= (.+))?', linex
                ).groups()
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
