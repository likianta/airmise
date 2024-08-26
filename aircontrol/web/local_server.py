from sanic import Sanic
from sanic import Websocket as SanicWebSocket

webapp_runner = Sanic.get_app('aircontrol-local-server', force_create=True)
