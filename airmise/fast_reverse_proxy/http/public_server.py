import asyncio
import pickle
import typing as tp
from aiohttp import web
from argsense import cli
from asyncio import Future
from collections import namedtuple
from functools import partial
from ...util import get_free_port

class T:
    AppName = str
    Client = namedtuple('Client', 'websocket source_port proxy_port')
    Clients = tp.Dict[AppName, Client]
    TunnelData = tp.Union[
        tp.TypedDict('Register', {  # type: ignore
            'type': tp.Literal['register'],
            'app_name': AppName,
            'source_port': int,
        }),
        tp.TypedDict('Response', {  # type: ignore
            'type': tp.Literal['response'],
            'request_id': str,
        })
    ]

_clients: T.Clients = {}
_pending_results: tp.Dict[str, Future] = {}

@cli
def run_server(port: int = 8080) -> None:
    """
    discussion: https://chatgpt.com/share/69d767dd-7fa0-8322-ac20-4640222d1a87
    """
    # this app plays role of "clients manager and port allocator".
    app = web.Application()
    app.router.add_route('*', '/tunnel', _tunnel)
    app.router.add_route('*', '/app/{name}', _proxy_on_subpath)
    app.router.add_route('*', '/app/{name}/{tail:.*}', _proxy_on_subpath)
    web.run_app(app, port=port)

async def _proxy_on_subpath(request):
    app_name = request.match_info['name']
    client = _clients.get(app_name)
    if not client:
        return web.Response(status=502, text='Client offline')

    ws = client.websocket
    # prefix = f'/app/{app_name}'
    # real_path = request.path_qs.removeprefix(prefix)
    # print(real_path)

    req_id = str(id(request))
    future = asyncio.get_event_loop().create_future()
    _pending_results[req_id] = future

    body = await request.read()
    await ws.send_bytes(pickle.dumps(
        {
            'type': 'request',
            'request_id': req_id,
            'method': request.method,
            'path': request.path_qs.removeprefix(f'/app/{app_name}'),
            'headers': dict(request.headers),
            'body': body,
        }
    ))

    result = await future
    return web.Response(
        status=result['status'],
        headers=result['headers'],
        body=result['body']
    )

async def _proxy_on_subport(
    name: T.AppName, request: web.Request
) -> web.Response:
    client = _clients.get(name)
    if not client:
        return web.Response(status=502, text='Client offline')
    
    ws = client.websocket
    req_id = str(id(request))
    future = asyncio.get_event_loop().create_future()
    _pending_results[req_id] = future
    
    body = await request.read()
    await ws.send_bytes(pickle.dumps({
        'type'   : 'request',
        'request_id' : req_id,
        'method' : request.method,
        'path'   : request.path_qs,
        'headers': dict(request.headers),
        'body'   : body,
    }))  # -> see `./private_server.py : main : if data['type'] == 'request'`
    
    result = await future
    return web.Response(
        status=result['status'],
        headers=result['headers'],
        body=result['body']
    )

async def _tunnel(request: web.Request) -> web.WebSocketResponse:
    ws = web.WebSocketResponse()
    await ws.prepare(request)
    
    app_name = ''
    async for msg in ws:
        assert msg.type == web.WSMsgType.BINARY
        data: T.TunnelData = pickle.loads(msg.data)  # noqa
        
        if data['type'] == 'register':
            if data['app_name'] in _clients:
                await ws.send_bytes(pickle.dumps({
                    'type': 'connection_refused',
                    'reason': 'application is already registered: {}@{}'.format(
                        app_name, _clients[app_name].proxy_port
                    ),
                }))
                break
            else:
                app_name = data['app_name']
            
            assert app_name not in _clients, (
                'Application already registered', data
            )
            
            src_port = data['source_port']
            proxy_port = get_free_port(src_port, 20000 + src_port)
            
            proxy_app = web.Application()
            proxy_app.router.add_route(
                '*',
                '/{tail:.*}',
                partial(_proxy_on_subport, app_name)
            )
            runner = web.AppRunner(proxy_app)
            await runner.setup()
            site = web.TCPSite(runner, '0.0.0.0', proxy_port)
            await site.start()
            
            _clients[app_name] = T.Client(ws, src_port, proxy_port)
            print('setup application: {} ({} <--> {})'.format(
                app_name, proxy_port, src_port
            ))
            
            await ws.send_bytes(pickle.dumps({
                'type'       : 'connection_established',
                'public_port': proxy_port,
            }))
        
        elif data['type'] == 'response':
            # response from private server
            future = _pending_results.pop(data['request_id'])
            future.set_result(data)
            # -> see `_proxy_on_subport : result = await future`
    
    if app_name:
        info = _clients.pop(app_name)
        print('uninstall application: {} ({} <--> {})'.format(
            app_name, info.proxy_port, info.source_port
        ))
    return ws

if __name__ == '__main__':
    cli.run(run_server)
