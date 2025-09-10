import json
import os
import signal
import typing as t
from textwrap import dedent
from time import sleep
from traceback import format_exception
from types import GeneratorType

from lk_utils import new_thread
from lk_utils import timestamp

from . import const
from .codec2 import decode
from .codec2 import encode
from .remote_control import store_object
from .socket_wrapper import Socket
from .socket_wrapper import SocketClosed
from .util import get_local_ip_address


class Server:
    host: str
    port: int
    verbose: bool
    _default_user_namespace: dict
    _socket: Socket
    
    # @property
    # def url(self) -> str:
    #     return 'tcp://{}:{}'.format(self.host, self.port)
    
    def __init__(
        self,
        host: str = const.DEFAULT_HOST,
        port: int = const.DEFAULT_PORT,
    ) -> None:
        self.host = host
        self.port = port
        self.verbose = False
        self._default_user_namespace = {}
        self._socket = Socket()
    
    def run(
        self,
        user_namespace: dict = None,
        /,
        host: str = None,
        port: int = None,
        verbose: t.Union[bool, int] = 0,
    ) -> None:
        """
        verbose:
            0 (also False): disabled
            1 (also True): enable socket verbose
                see also `./socket_wrapper.py : Socket`
            2: enable both socket and server verbose
                see also `self._mainloop : [code] if self.verbose...`
            usually we use 0/1, i.e. the False/True.
        """
        if user_namespace:
            self._default_user_namespace.update(user_namespace)
        self.verbose = bool(verbose == 2)
        self._socket.verbose = bool(verbose)
        self._socket.bind(host or self.host, port or self.port)
        self._socket.listen(20)
        
        # fix ctrl + c
        if os.name == 'nt':
            signal.signal(signal.SIGINT, signal.SIG_DFL)
        
        while True:
            s = self._socket.accept()  # blocking
            self._handle_connection(s)
            sleep(0.1)
    
    @new_thread()
    def _handle_connection(self, socket: Socket) -> None:
        ctx = {
            **self._default_user_namespace,
            '__ref__': {'__result__': None},
        }
        session_data = {}
        
        def exec_() -> t.Any:
            ctx['__ref__']['__result__'] = None
            exec(code, ctx)
            return ctx['__ref__']['__result__']
        
        while True:
            try:
                data_bytes = socket.recvall()
            except SocketClosed:
                return
            
            code, kwargs, options = decode(data_bytes)
            
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
                            kwargs, default=str, ensure_ascii=False, indent=4
                        )) if kwargs else ''
                    ).strip()
                )
            
            if kwargs:
                ctx.update(kwargs)
            
            if options:
                if options.get('is_iterator'):
                    iter_id = options['id']
                    if iter_id not in session_data:
                        try:
                            session_data[iter_id] = exec_()
                        except Exception as e:
                            response = (
                                const.ERROR, ''.join(format_exception(e)))
                        else:
                            response = (const.NORMAL_OBJECT, 'ready')
                    else:
                        try:
                            datum = next(session_data[iter_id])
                            response = (const.YIELD, datum)
                        except StopIteration:
                            response = (const.YIELD_OVER, None)
                            session_data.pop(iter_id)
                        except Exception as e:
                            response = (
                                const.ERROR, ''.join(format_exception(e)))
                else:
                    raise NotImplementedError(options)
            else:
                try:
                    result = exec_()
                except Exception as e:
                    response = (const.ERROR, ''.join(format_exception(e)))
                else:
                    if isinstance(result, GeneratorType):
                        # uid = uuid1().hex
                        # session_data[uid] = result
                        # response = dump((const.ITERATOR, uid))
                        response = (const.NORMAL_OBJECT, tuple(result))
                    else:
                        try:
                            response = (const.NORMAL_OBJECT, result)
                        except Exception:
                            store_object(x := str(id(result)), result)
                            response = (const.SPECIAL_OBJECT, x)
            
            # assert response
            socket.sendall(encode(response))


def run_server(
    user_namespace: dict = None,
    /,
    host: str = const.DEFAULT_HOST,
    port: int = const.DEFAULT_PORT,
    verbose: bool = False,
) -> None:
    if host == '0.0.0.0':
        print('server is working on: \n- {}\n- {}'.format(
            'http://localhost:{}'.format(port),
            'http://{}:{}'.format(get_local_ip_address(), port)
        ))
    server = Server(host, port)
    server.run(user_namespace, verbose=verbose)
