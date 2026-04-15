import aiohttp
import asyncio
import pickle
import typing as tp
from argsense import cli
from functools import partial

class T:
    _ConnectionEstablished = tp.TypedDict('_ConnectionEstablished', {
        'type': tp.Literal['connection_established'],
        'public_port': int,
    })
    _ConnectionRefused = tp.TypedDict('_ConnectionRefused', {
        'type': tp.Literal['connection_refused'],
        'reason': str,
    })
    _Request = tp.TypedDict('_Request', {
        'type': tp.Literal['request'],
        'request_id': str,
        'method': str,
        'path': str,
        'headers': dict,
        'body': bytes,
    })
    Data = tp.Union[_ConnectionEstablished, _ConnectionRefused, _Request]

@cli
async def connect_to_public_server(
    name: str,
    source_port: int,
    target_host: str,
    target_port: int = 8080,
):
    # print(name, source_port, target_host, target_port)
    source_url = f'http://localhost:{source_port}'
    target_url = f'http://{target_host}:{target_port}/tunnel'
    async with aiohttp.ClientSession() as session:
        async with session.ws_connect(target_url) as ws:
            # register
            await ws.send_bytes(pickle.dumps({
                'type': 'register',
                'app_name': name,
            }))
            async for msg in ws:
                data: T.Data = pickle.loads(msg.data)
                # print(data['req_id'], data['path'], ':i')
                
                if data['type'] == 'connection_established':
                    print(
                        'connection established ({} -> {}). we can access '
                        '"http://{}:{}" to reach public site'.format(
                            source_port, data['public_port'],
                            target_host, data['public_port'],
                        ),
                        ':v4'
                    )
                
                elif data['type'] == 'connection_refused':
                    raise Exception(data['reason'])
                
                elif data['type'] == 'request':
                    req_id = data['request_id']
                    async with session.request(
                        data['method'],
                        source_url + data['path'],
                        headers=data['headers'],
                        data=data['body']
                    ) as resp:
                        body = await resp.read()
                        await ws.send_bytes(pickle.dumps({
                            'type': 'response',
                            'request_id': req_id,
                            'status': resp.status,
                            'headers': dict(resp.headers),
                            'body': body
                        }))  # -> see `./public_server.py : tunnel :
                        #   if data['type'] == 'response'`

if __name__ == '__main__':
    asyncio.run(partial(cli.run, connect_to_public_server)())
