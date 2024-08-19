from textwrap import dedent

from .webapp import messenger

FRONTEND_SCRIPT = dedent(
    '''
    // see `aircontrol.server:server_runner.websocket('/server')`
    const host = window.location.hostname;
    // console.log(host);
    //  e.g. `http://<server_ip>[:<server_port>]/server` -> '<server_ip>`
    const ws_server = new WebSocket(`ws://${host}:2140/server`);
    ws_server.onmessage = (e) => { ws_client.send(e.data); }

    // see `aircontrol.client:client_runner.websocket('/client')`
    const ws_client = new WebSocket('ws://localhost:2141/client');
    ws_client.onmessage = (e) => { ws_server.send(e.data); }
    '''
).strip()

FRONTEND_TAG = '<script>\n{}\n</script>'.format(FRONTEND_SCRIPT)


def is_frontend_online() -> bool:
    return messenger.frontend_active
