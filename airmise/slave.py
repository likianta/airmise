import json
import typing as tp
from textwrap import dedent
from time import time
from traceback import format_exception
from types import FunctionType
from types import GeneratorType

from lk_utils import timestamp
from lk_utils import uuid

from . import const
from .codec import decode
from .codec import encode
from .master import Master
from .remote_control import store_object
from .socket_wrapper import Socket
from .socket_wrapper import SocketClosed


class Slave(Master):
    def __init__(
        self, socket: Socket, user_namespace: tp.Optional[dict] = None
    ) -> None:
        super().__init__(socket)
        self.active = False
        self.verbose = False
        self._mainloop_running = False
        self._user_namespace = user_namespace or {}

    def call(self, func_name: str, *args, **kwargs) -> tp.Any:
        assert self.active
        return super().call(func_name, *args, **kwargs)

    def exec(  # type: ignore
        self, source: tp.Union[str, FunctionType], **kwargs
    ) -> tp.Any:
        assert self.active
        return super().exec(source, **kwargs)

    def mainloop(self) -> None:
        # design thinking:
        #   we decouple mainloop into an interator method (`_mainloop`) and a
        #   shell method (`mainloop`), the former one is good for subclass to
        #   operate on it more flexible, while later is good for general caller
        #   to use, which is intuitive and simple (simply blocking).
        #   see also `./server.py : NonblockingSlave`.
        self._mainloop_running = True
        for _ in self._mainloop(self.socket, self._user_namespace):
            if not self._mainloop_running:
                break
        print('mainloop exited', ':pv7')

    def _mainloop(self, socket: Socket, namespace: dict) -> tp.Iterator:
        ctx = {**namespace, '__ref__': {'__result__': None}}
        session_data = {}

        def exec_code() -> tp.Any:
            ctx['__ref__']['__result__'] = None
            exec(code, ctx)
            return ctx['__ref__']['__result__']

        def calibrate_exception(e: Exception) -> tp.Iterable[str]:
            src_file = tp.cast(tp.Optional[str], ctx.get('_source_file'))
            src_lineno = tp.cast(tp.Optional[int], ctx.get('_source_lineno'))
            if src_file and src_lineno:
                for line in format_exception(e):
                    if line.lstrip().startswith('File "<string>"'):
                        a, b, c = line.split(', ', 2)
                        wrong_lineno = int(b)
                        correct_lineno = src_lineno + wrong_lineno
                        yield 'File "{}", line {}, {}'.format(
                            src_file, correct_lineno, c
                        )
                    else:
                        yield line
                return format_exception(e)

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
                            resp = (
                                const.ERROR,
                                ''.join(calibrate_exception(e)),
                            )
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
                    print(
                        ':vr2',
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
                                    args,
                                    default=str,
                                    ensure_ascii=False,
                                    indent=4,
                                )
                            )
                            if args
                            else '',
                        )
                        .strip(),
                    )

                try:
                    if flag == const.CALL_FUNCTION:
                        func = tp.cast(FunctionType, ctx[code])
                        if args:
                            result = func(*args['args'], **args['kwargs'])
                        else:
                            result = func()
                    else:
                        if args:
                            ctx.update(args)
                        result = exec_code()
                except Exception as e:
                    resp = (const.ERROR, ''.join(format_exception(e)))
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

    def set_active(self) -> None:
        if not self.active:
            self._mainloop_running = False
            self.active = True

    def set_passive(self, user_namespace: tp.Optional[dict] = None) -> None:
        if self.active:
            self.active = False
            # self._socket.sendall(encode((const.INTERNAL, 'exit_loop', None)))
            self._send(const.INTERNAL, 'exit_loop')
