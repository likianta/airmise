from sanic import Sanic
from sanic import Websocket as SanicWebSocket
from collections import deque
from asyncio import sleep
import typing as t

web_server = Sanic.get_app('aircontrol-web-server', force_create=True)


@web_server.websocket('/frontend')  # noqa
async def _frontend(_, ws: SanicWebSocket) -> None:
    messenger.frontend_active = True
    while True:
        await sleep(2e-3)
        if messenger.queue:
            id, data = messenger.queue.popleft()
            print(id, data, ':v')
            await ws.send(data)
            resp = await ws.recv()
            messenger[id] = resp


class Messenger:
    class _Undefined:
        def __bool__(self) -> bool:
            return False
    
    _UNDEFINED = _Undefined()
    
    def __init__(self) -> None:
        self.frontend_active = False
        self.queue = deque()
        self._auto_id = 0
        self._callbacks = {}  # {id: (None | _UNDEFINED | callable), ...}
    
    def __setitem__(self, id: int, value: str) -> None:
        if self._callbacks[id]:
            # self._callbacks.pop(id)(value)
            self._callbacks[id](value)
        else:
            self._callbacks[id] = value
            #   will be popped in `self.send_sync._wait_for_result`
    
    def send_sync(self, data: str) -> str:
        """
        param data: `<id>:done?` | str serialized_data
        returns: `<id>:working...` | str serialized_data
        """
        # data: `<id>:done?` | str serialized_data
        if data.endswith(':done?'):
            id = int(data.split(':')[0])
            if self._callbacks[id] is self._UNDEFINED:
                return f'{id}:working...'
            else:
                return self._callbacks.pop(id)
        
        # ---------------------------------------------------------------------
        
        if not self.frontend_active:
            raise Exception('frontend is not online')
        
        self._auto_id += 1
        self._callbacks[self._auto_id] = self._UNDEFINED
        self.queue.append((self._auto_id, data))
        print(len(self.queue), ':v')
        return f'{self._auto_id}:working...'
    
    async def send_async(self, data: str, callback: t.Callable = None) -> None:
        self._auto_id += 1
        self._callbacks[self._auto_id] = callback
        self.queue.append((self._auto_id, data))


messenger = Messenger()
