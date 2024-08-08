import typing as t
from asyncio import sleep
from collections import deque
from time import sleep as sleep_sync

from sanic import Sanic
from sanic import Websocket as SanicWebSocket

server_runner = Sanic('aircontrol-server')


class Messenger:
    class _Undefined:
        def __bool__(self) -> bool:
            return False
    
    _UNDEFINED = _Undefined()
    
    def __init__(self) -> None:
        self.queue = deque()
        self._auto_id = 0
        self._callbacks = {}  # {id: (None | _UNDEFINED | callable), ...}
    
    def send_sync(self, data: str) -> t.Any:
        self._auto_id += 1
        self._callbacks[self._auto_id] = self._UNDEFINED
        self.queue.append((self._auto_id, data))
        while self._callbacks[self._auto_id] is self._UNDEFINED:
            sleep_sync(1e-3)
        return self._callbacks.pop(self._auto_id)
    
    async def send_async(self, data: str, callback: t.Callable = None) -> None:
        self._auto_id += 1
        self._callbacks[self._auto_id] = callback
        self.queue.append((self._auto_id, data))
    
    def callback(self, id: str, data: str) -> None:
        if cb := self._callbacks.pop(id):
            cb(data)


messenger = Messenger()


@server_runner.websocket('/server')  # noqa
async def _on_message(_, ws: SanicWebSocket) -> None:
    while True:
        await sleep(1e-3)
        if messenger.queue:
            id, data = messenger.queue.popleft()
            await ws.send(data)
            resp = await ws.recv()
            messenger.callback(id, resp)
