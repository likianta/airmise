"""
DELETE: not working.
"""
import typing as t
import asyncio
from asyncio import sleep
from collections import deque
# from time import sleep

import threading
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
        print(len(self.queue), ':v')
        
        async def _wait_for_result() -> t.Any:
            while self._callbacks[self._auto_id] is self._UNDEFINED:
                await sleep(2e-3)
            return self._callbacks.pop(self._auto_id)
        
        # print('wait for result')
        # from asgiref.sync import async_to_sync
        # f = async_to_sync(_wait_for_result, force_new_loop=True)
        # print(':v', f)
        # result = f()
        # print(':v', result)
        # return result
        
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            # https://stackoverflow.com/questions/46727787/runtimeerror-there
            # -is-no-current-event-loop-in-thread-in-async-apscheduler
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
        # # return loop.run_until_complete(_wait_for_result())
        # # result = loop.run_in_executor(_wait_for_result())
        # # print(':v', result)
        # # return result
        task = loop.create_task(_wait_for_result())
        return task
        # while not task.done():
        #     sleep_sync(2e-3)
        # return task.result()
    
    async def send_async(self, data: str, callback: t.Callable = None) -> None:
        self._auto_id += 1
        self._callbacks[self._auto_id] = callback
        self.queue.append((self._auto_id, data))
        
    async def send_async_2(self, data: str) -> t.Any:
        self._auto_id += 1
        self._callbacks[self._auto_id] = self._UNDEFINED
        self.queue.append((self._auto_id, data))
        self.queue_updated.set()
        print(self.queue, messenger.queue, ':v')
        while self._callbacks[self._auto_id] is self._UNDEFINED:
            await sleep(1)
            print(self._callbacks, ':vi')
        print(':v', 'got result')
        return self._callbacks.pop(self._auto_id)
    
    def callback(self, id: str, data: str) -> None:
        if cb := self._callbacks.pop(id):
            cb(data)


messenger = Messenger()


@server_runner.websocket('/server')  # noqa
async def _on_message(_, ws: SanicWebSocket) -> None:
    """
    workflow:
        1.  assume the server wants to get devices from client computer.
        2.  server: `aircontrol.executor.remote_exe` pushes request to
            `<this_module>.messenger`.
        3.  this function sends the request to webpage (see
            `aircontrol/frontend.html:ws_server.onmessage`).
        4.  webpage transfers request to client side.
        5.  the client has established a local websocket that listens to the
            webpage events, so it will handle the request, enumerates the
            devices in client computer, and generates the device list data
            (see `aircontrol.client._on_message`).
        6.  client sends result back to webpage.
        7.  webpage transfers the response to server (i.e. this function).
        8.  we call `message.callback` to trigger the callback function.
        9.  finally, server gets the device list.
    """
    print(':r', '[green dim]setup websocket "/server"[/]')
    while True:
        await sleep(2e-3)
        if messenger.queue:
            id, data = messenger.queue.popleft()
            print(id, data, ':v')
            await ws.send(data)
            resp = await ws.recv()
