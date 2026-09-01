import json
import typing as tp
from textwrap import dedent
from time import time
from traceback import format_exception
from types import FunctionType
from types import GeneratorType

from lk_utils import timestamp
from lk_utils import uuid
from lk_utils.subproc import Thread
from lk_utils.subproc import run_new_thread

from . import const
from .codec import decode
from .codec import encode
from .remote_control import store_object
from .requester import Requester
from .socket_wrapper import Socket
from .socket_wrapper import SocketClosed


class T:
    Namespace = tp.Dict[str, tp.Union[tp.Callable, '_ConnectionRequired']]


class Responder(Requester):
    def __init__(
        self, socket: Socket, user_namespace: tp.Optional[T.Namespace] = None
    ) -> None:
        super().__init__(socket)
        self.active = False
        self.verbose = False
        self._mainloop_living = False
        self._mainloop_thread: tp.Optional[Thread] = None
        self._user_namespace = user_namespace or {}

    @property
    def connection(self) -> Socket:
        return self.socket

    def call(self, func_name: str, *args, **kwargs) -> tp.Any:
        assert self.active
        return super().call(func_name, *args, **kwargs)

    def exec(  # type: ignore
        self, source: tp.Union[str, FunctionType], **kwargs
    ) -> tp.Any:
        assert self.active
        return super().exec(source, **kwargs)

    def set_active(self) -> None:
        if not self.active:
            self.active = True
            self._mainloop_living = False
            if self._mainloop_thread:
                self._mainloop_thread.stop()

    def set_passive(self, *_, **__) -> None:
        if self.active:
            self.active = False
            # self._socket.sendall(encode((const.INTERNAL, 'exit_loop', None)))
            self._send(const.INTERNAL, 'exit_loop')

    def mainloop(
        self,
        user_namespace: tp.Optional[T.Namespace] = None,
        blocking: bool = True,
    ) -> None:
        if user_namespace is None:
            user_namespace = self._user_namespace

        def living_mainloop() -> tp.Iterator:
            self._mainloop_living = True
            for _ in self._mainloop(self.socket, user_namespace):
                if not self._mainloop_living:
                    break
                yield
            print('mainloop exited', ':{}v7'.format('p2' if blocking else ''))

        if blocking:
            for _ in living_mainloop():
                pass
        else:
            self._mainloop_thread = run_new_thread(
                living_mainloop, interruptible=True
            )

    def _mainloop(self, socket: Socket, namespace: T.Namespace) -> tp.Iterator:
        ctx: tp.Dict[str, tp.Any] = {
            **namespace,
            '__ref__': {'__result__': None},
        }
        session_data = {}

        def code_glance() -> None:
            print(
                ':pvr2',
                dedent(
                    """
                    > *message at {}*

                    ```python
                    {}
                    ```

                    {}
                    """
                )
                .format(
                    timestamp(),
                    code.strip(),
                    '```json\n{}\n```'.format(
                        json.dumps(
                            args, default=str, ensure_ascii=False, indent=4
                        )
                    )
                    if args
                    else '',
                )
                .strip(),
            )

        def exec_code() -> tp.Any:
            ctx['__ref__']['__result__'] = None
            exec(code, ctx)
            return ctx['__ref__']['__result__']

        # FIXME
        def calibrate_exception(
            e: Exception, source_file: str, source_lineno: int
        ) -> tp.Iterable[str]:
            # https://chatgpt.com/share/6a9161d8-c738-83e8-a06c-04c44dfd896a
            for line in format_exception(e):
                if line.lstrip().startswith('File "<string>"'):
                    a, b, c = line.split(', ', 2)
                    wrong_lineno = int(b.removeprefix('line '))
                    correct_lineno = source_lineno + wrong_lineno
                    yield 'File "{}", line {}, {}'.format(
                        source_file, correct_lineno, c
                    )
                else:
                    yield line

        flag: int
        code: str
        args: tp.Optional[dict]
        resp: tp.Tuple[int, tp.Any]

        while True:
            yield
            try:
                data_bytes = socket.recvall()
            except (SocketClosed, ConnectionResetError):
                return

            flag, code, args = decode(data_bytes)

            if flag == const.INTERNAL:
                if code == 'exit_loop':
                    return
                elif code == 'get_socket_port':
                    resp = (const.NORMAL, socket.port)
                elif code == 'switch_roleplay':
                    self.set_active()
                    print('change role from "slave" to "master"', ':v')
                    return
                else:
                    raise Exception(flag, code, args)

            elif flag == const.ITERATOR:
                iter_id = args['id']  # noqa
                if iter_id in session_data:
                    # --- a.
                    # try:
                    #     datum = next(session_data[iter_id])
                    #     resp = (const.YIELD, datum)
                    # except StopIteration:
                    #     resp = (const.YIELD_OVER, None)
                    #     session_data.pop(iter_id)
                    # except Exception as e:
                    #     resp = (const.ERROR, ''.join(format_exception(e)))
                    # --- b.
                    buffer = []
                    start_time = time()
                    while True:
                        try:
                            datum = next(session_data[iter_id])
                        except StopIteration:
                            resp = (const.YIELD_OVER, buffer)
                            break
                        except Exception as e:
                            resp = (const.ERROR, ''.join(format_exception(e)))
                            break
                        else:
                            buffer.append(datum)
                            if time() - start_time > 1:
                                resp = (const.YIELD, buffer)
                                break
                else:
                    raise Exception
                    # try:
                    #     session_data[iter_id] = exec_code()
                    # except Exception as e:
                    #     resp = (const.ERROR, ''.join(format_exception(e)))
                    # else:
                    #     resp = (const.NORMAL, 'ready')

            else:  # CALL_FUNCTION | DELEGATE | NORMAL
                if self.verbose and code:
                    code_glance()

                try:
                    if flag == const.CALL_FUNCTION:
                        x = tp.cast(
                            tp.Union[FunctionType, _ConnectionRequired],
                            ctx[code],
                        )
                        if isinstance(x, _ConnectionRequired):
                            func = x.target
                            args['args'] = (self.connection,) + args['args']
                        else:
                            func = x
                        if args['args'] or args['kwargs']:
                            result = func(*args['args'], **args['kwargs'])
                        else:
                            result = func()
                    else:
                        if args:
                            ctx.update(args)
                        result = exec_code()
                except Exception as e:
                    code_glance()
                    resp = (
                        const.ERROR,
                        ''.join(
                            format_exception(e)
                            # calibrate_exception(
                            #     e, args['_source_file'], args['_source_lineno']
                            # )
                        ),
                    )
                else:
                    if flag == const.DELEGATE:
                        store_object(x := str(id(result)), result)
                        resp = (const.DELEGATE, x)
                    else:
                        if isinstance(result, GeneratorType):
                            # resp = (const.NORMAL, tuple(result))
                            iter_id = uuid()
                            session_data[iter_id] = result
                            resp = (const.ITERATOR, iter_id)
                        else:
                            resp = (const.NORMAL, result)

            # assert resp
            socket.sendall(encode(resp))


# class NonblockingSlave(Slave):
#     def __init__(self, *args, **kwargs) -> None:
#         super().__init__(*args, **kwargs)
#         self._mainloop_thread: tp.Optional[Thread] = None

#     def mainloop(self) -> None:
#         assert not self._mainloop_thread
#         self._mainloop_thread = run_new_thread(
#             self._mainloop,
#             self.socket,
#             self._user_namespace,
#             interruptible=True,
#         )

#     def set_active(self) -> None:
#         if not self.active:
#             assert self._mainloop_thread
#             self._mainloop_running = False
#             self.active = True
#             self._mainloop_thread.stop()


class _ConnectionRequired:
    def __init__(self, target: tp.Callable) -> None:
        self.target = target


def inject_connection(target_func: tp.Callable) -> _ConnectionRequired:
    """
    This wrapper is used for objects in server's namespace.

    Usage:
        import airmise as air

        def echo(connection: air.Connection, msg: str) -> None:
            print(connection.host, connection.port, msg)

        air.run_server(
            namespace=dict(
                foo=air.inject_connection(echo)
            )
        )
    """
    return _ConnectionRequired(target_func)
