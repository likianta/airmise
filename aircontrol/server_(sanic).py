from sanic import Sanic
from sanic import Websocket

from .serdes import dump

app = Sanic('aircontrol', configure_logging=False)


@app.route('/')
async def _index(_) -> str:
    return 'aircontrol is running!'


@app.websocket('/exe')  # noqa
async def _execute(_, ws: Websocket) -> None:
    result = _NotDefined
    while True:
        data = await ws.recv()
        print(data, ':v')
        exec(data, globals(), locals())
        if result is not _NotDefined:
            await ws.send(dump(result))
            result = _NotDefined


class _NotDefined:
    pass
