from textwrap import dedent

FRONTEND_SCRIPT = dedent(
    '''
    // see `aircontrol.server:server_runner.websocket('/server')`
    const host = window.location.host;
    console.log(host);
    //  e.g. 'http://192.168.10.17:2140/server' -> '192.168.10.17:2140'
    const ws_server = new WebSocket(`ws://${host}/server`);
    ws_server.onmessage = (e) => { ws_client.send(e.data); }

    // see `aircontrol.client:client_runner.websocket('/client')`
    const ws_client = new WebSocket('ws://localhost:2141/client');
    ws_client.onmessage = (e) => { ws_server.send(e.data); }
    '''
).strip()

FRONTEND_TAG = '<script>\n{}\n</script>'.format(FRONTEND_SCRIPT)
