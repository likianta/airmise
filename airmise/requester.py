import inspect
import sys
import typing as tp
from types import FrameType
from types import FunctionType

from lk_utils import dedent

from . import const
from .codec import decode
from .codec import encode
from .socket_wrapper import Socket


class Requester:
    def __init__(self, socket: Socket) -> None:
        self.socket = socket

    @property
    def host(self) -> str:
        return self.socket.peer_host

    @property
    def port(self) -> int:
        return self.socket.peer_port

    def call(self, func_name: str, *args, **kwargs) -> tp.Any:
        frame: FrameType = inspect.currentframe().f_back  # type: ignore
        self._send(
            const.CALL_FUNCTION,
            func_name,
            {
                'args': args,
                'kwargs': kwargs,
                '_source_file': frame.f_code.co_filename,
                '_source_lineno': frame.f_lineno,
            },
        )
        return self._recv()

    def exec(
        self,
        source: tp.Union[str, FunctionType],
        delegate: bool = False,
        **kwargs,
    ) -> tp.Any:
        # TODO: check if source is a file path.
        if isinstance(source, str):
            # print(':vr2', '```python\n{}\n```'.format(dedent(source).strip()))
            code = interpret_code(source)
        else:
            # print(':v', source)
            code = interpret_func(source)

        frame: FrameType = inspect.currentframe().f_back  # type: ignore
        kwargs['_source_file'] = frame.f_code.co_filename
        kwargs['_source_lineno'] = frame.f_lineno

        # print(':r2', '```python\n{}\n```'.format(code.strip()))

        self._send(const.DELEGATE if delegate else const.NORMAL, code, kwargs)
        return self._recv()

    def set_passive(
        self,
        user_namespace: tp.Optional[dict] = None,
        switch_roleplay: bool = True,
    ) -> None:
        from .responder import Responder

        if switch_roleplay:
            self._send(const.INTERNAL, 'switch_roleplay')
        res = Responder(self.socket, user_namespace)
        res.active = True
        res.mainloop()  # blocking

    def _recv(self) -> tp.Any:
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
            # result is an iter_id.
            return self._iterate(result)
        elif code == const.NORMAL:
            return result
        elif code == const.YIELD:
            return result
        elif code == const.YIELD_OVER:
            return StopIteration
        else:
            raise Exception(code, result)

    def _iterate(self, id: str) -> tp.Iterator:
        _args = {'is_iterator': True, 'id': id}
        while True:
            self._send(const.ITERATOR, None, _args)
            code, result = decode(self.socket.recvall())
            if code == const.YIELD:
                yield from result
            elif code == const.YIELD_OVER:
                yield from result
                break
            else:
                raise Exception(code, result)

    def _send(
        self, flag: int, code: tp.Optional[str], args: tp.Optional[dict] = None
    ) -> None:
        self.socket.sendall(encode((flag, code, args)))


# ------------------------------------------------------------------------------


def interpret_code(raw_code: str, interpret_return: bool = True) -> str:
    """
    The `raw_code` is like valid Python code, but has "top return" statements:
        req.exec('return os.getcwd()')
        req.exec(
            '''
            if os.getenv('SOMETHING'):
                return 'ON'
            else:
                return 'OFF'
            '''
        )
        req.exec(
            '''
            def foo():
                return 'foo'
            return 'bar'
            '''
        )
    We will convert the `return` statements to `__ref__["__result__"] = ...`:
        (1) __ref__["__result__"] = os.getcwd()
        (2)
            if os.getenv('SOMETHING'):
                __ref__["__result__"] = 'ON'
            else:
                __ref__["__result__"] = 'OFF'
        (3)
            def foo():
                return 'foo'
                #   be noticed, function returns are not "top-level" returns, so
                #   they won't be translated.
            __ref__["__result__"] = 'bar'
    Limitation:
        This function cannot handle triple quoted strings well.
        For example, this will fail:
            req.exec(
                ```
                def foo():  # foo must return 'foo'
                    '''
                return 'bar'
                    '''
                    return 'foo'
                return 'baz'
                ```
            )
        It becomes:
            def foo():  # warning: foo returns None
                '''
            __ref__["__result__"] = 'bar'
                '''
                __ref__["__result__"] = 'foo'
            __ref__["__result__"] = 'baz'
    """

    if '\n' in raw_code:
        out_lines = []
        flag = 'START'
        has_return_statement = False
        for line in dedent(raw_code).splitlines():
            if flag == 'START':
                line_stripped = line.lstrip()
                space = ' ' * (len(line) - len(line_stripped))
                if line_stripped.startswith('return '):
                    has_return_statement = True
                    out_lines.append(
                        '{}__ref__["__result__"] = {}'.format(
                            space, line_stripped[7:]
                        )
                    )
                else:
                    out_lines.append(line)
                    if line_stripped.startswith(
                        ('def ', 'class ', 'lambda ', 'lambda:', 'async ')
                    ):
                        flag = 'SCOPED'
            elif flag == 'SCOPED':
                if line.startswith('return '):
                    has_return_statement = True
                    out_lines.append(
                        '__ref__["__result__"] = {}'.format(line[7:])
                    )
                    flag = 'START'
                else:
                    out_lines.append(line)
                    if line and line[0] != '#' and line[0] != ' ':
                        if line_stripped.startswith(
                            ('def ', 'class ', 'lambda ', 'lambda:', 'async ')
                        ):
                            pass  # new scope
                        else:
                            flag = 'START'
            else:
                raise Exception(flag)
        if flag == 'START' and not has_return_statement:
            out_lines.append('__ref__["__result__"] = None')
        return '\n'.join(out_lines)
    else:
        if raw_code.startswith('return '):
            return '__ref__["__result__"] = {}'.format(raw_code[7:])
        else:
            return '__ref__["__result__"] = {}'.format(raw_code)


def interpret_func(func: FunctionType) -> str:
    return '\n'.join(
        (
            interpret_code(inspect.getsource(func), interpret_return=False),
            '__ref__["__result__"] = {}(*args, **kwargs)'.format(func.__name__),
        )
    )
