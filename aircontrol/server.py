"""
guide: docs/server-webapp-client-structure.zh.md
"""
import socket
import sys
import typing as t
from asyncio import sleep
from collections import deque
from functools import cache

from sanic import Sanic
from sanic import Websocket as SanicWebSocket

# server_runner = Sanic('aircontrol-server')
server_runner = Sanic.get_app('aircontrol-server', force_create=True)


@server_runner.websocket('/webapp')  # noqa
async def _on_webapp_message(_, ws: SanicWebSocket) -> None:
    while True:
        await sleep(2e-3)
        data = await ws.recv()
        #   `<id>:done?` | str serialized_data
        resp = messenger.send_sync(data)
        await ws.send(resp)


@server_runner.websocket('/server')  # noqa
async def _on_server_message(_, ws: SanicWebSocket) -> None:
    print(':r', '[green dim]setup websocket "/server"[/]')
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


@cache
def get_local_ip_address() -> str:
    # https://stackoverflow.com/a/166520/9695911
    if sys.platform == 'linux':
        return socket.gethostbyname(socket.getfqdn())
    else:
        return socket.gethostbyname(socket.gethostname())
