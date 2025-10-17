import json
import typing as t
from textwrap import dedent
from traceback import format_exception
from types import FunctionType
from types import GeneratorType

from lk_utils import timestamp

from . import const
from .codec2 import decode
from .codec2 import encode
from .master import Master
from .remote_control import store_object
from .socket_wrapper import Socket
from .socket_wrapper import SocketClosed


class Slave(Master):
    def __init__(
        self,
        socket: Socket,
        user_namespace: dict = None,
    ) -> None:
        super().__init__(socket)
        self.active = False
        self.verbose = False
        self._mainloop_running = False
        self._user_namespace = user_namespace or {}
    
    def call(self, func_name: str, *args, **kwargs) -> t.Any:
        assert self.active
        return super().call(func_name, *args, **kwargs)
    
    def exec(self, source: t.Union[str, FunctionType], **kwargs) -> t.Any:
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
    
    def _mainloop(self, socket: Socket, namespace: dict) -> t.Iterator:
        ctx = {**namespace, '__ref__': {'__result__': None}}
        session_data = {}
        
        def exec_code() -> t.Any:
            ctx['__ref__']['__result__'] = None
            exec(code, ctx)
            return ctx['__ref__']['__result__']
        
        flag: int
        code: str
        args: t.Optional[dict]
        resp: t.Tuple[int, t.Any]
        
        while True:
            yield
            try:
                data_bytes = socket.recvall()
            except SocketClosed:
                return
            
            flag, code, args = decode(data_bytes)
            
            if flag == const.CALL_FUNCTION:
                try:
                    func = t.cast(FunctionType, ctx[code])
                    if args:
                        result = func(*args['args'], **args['kwargs'])
                    else:
                        result = func()
                except Exception as e:
                    resp = (const.ERROR, ''.join(format_exception(e)))
                else:
                    if isinstance(result, GeneratorType):
                        # uid = uuid1().hex
                        # session_data[uid] = result
                        # resp = dump((const.ITERATOR, uid))
                        resp = (const.NORMAL_OBJECT, tuple(result))
                    else:
                        try:
                            resp = (const.NORMAL_OBJECT, result)
                        except Exception:
                            store_object(x := str(id(result)), result)
                            resp = (const.SPECIAL_OBJECT, x)
            
            elif flag == const.INTERNAL:
                if code == 'exit_loop':
                    return
                elif code == 'get_socket_port':
                    resp = (const.NORMAL_OBJECT, socket.port)
                elif code == 'switch_roleplay':
                    self.set_active()
                    print('change role from "slave" to "master"', ':v')
                    return
                else:
                    raise Exception(flag, code, args)
            
            elif flag == const.ITERATOR:
                iter_id = args['id']
                if iter_id not in session_data:
                    try:
                        session_data[iter_id] = exec_code()
                    except Exception as e:
                        resp = (const.ERROR, ''.join(format_exception(e)))
                    else:
                        resp = (const.NORMAL_OBJECT, 'ready')
                else:
                    try:
                        datum = next(session_data[iter_id])
                        resp = (const.YIELD, datum)
                    except StopIteration:
                        resp = (const.YIELD_OVER, None)
                        session_data.pop(iter_id)
                    except Exception as e:
                        resp = (const.ERROR, ''.join(format_exception(e)))
            
            else:  # flag could be: const.NORMAL_OBJECT
                if args:
                    ctx.update(args)
                    
                if self.verbose and code:
                    print(
                        ':vr2',
                        dedent(
                            '''
                            > *message at {}*
    
                            ```python
                            {}
                            ```
    
                            {}
                            '''
                        ).format(
                            timestamp(),
                            code.strip(),
                            '```json\n{}\n```'.format(json.dumps(
                                args, default=str, ensure_ascii=False, indent=4
                            )) if args else ''
                        ).strip()
                    )
                
                try:
                    result = exec_code()
                except Exception as e:
                    resp = (const.ERROR, ''.join(format_exception(e)))
                else:
                    if isinstance(result, GeneratorType):
                        # uid = uuid1().hex
                        # session_data[uid] = result
                        # resp = dump((const.ITERATOR, uid))
                        resp = (const.NORMAL_OBJECT, tuple(result))
                    else:
                        try:
                            resp = (const.NORMAL_OBJECT, result)
                        except Exception:
                            store_object(x := str(id(result)), result)
                            resp = (const.SPECIAL_OBJECT, x)
            
            # assert resp
            socket.sendall(encode(resp))
    
    def set_active(self) -> None:
        if not self.active:
            self._mainloop_running = False
            self.active = True
    
    def set_passive(self, _=None) -> None:
        if self.active:
            self.active = False
            # self._socket.sendall(encode((const.INTERNAL, 'exit_loop', None)))
            self._send(const.INTERNAL, 'exit_loop')
