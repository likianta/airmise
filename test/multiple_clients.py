import airmise as air
from argsense import cli
from lk_utils import start_ipython


@cli
def server(host: str = air.DEFAULT_HOST, port: int = air.DEFAULT_PORT) -> None:
    def foo(*args, **kwargs) -> str:
        print(args, kwargs)
        return 'ok'
    
    server = air.Server(host, port)
    server.run({'foo': foo})


@cli
def client(
    server_host: str = air.DEFAULT_HOST,
    server_port: int = air.DEFAULT_PORT,
) -> None:
    """
    params:
        server_host:
        server_port (-p):
    """
    client = air.Client(server_host, server_port)
    client.open()
    
    result = client.call('foo', 123, 456, abc='xyz')
    print(result)  # -> ok
    
    result = client.exec(
        '''
        print('hello world')  # this should be found in the server console
        return 123
        '''
    )
    print(result)  # -> 123
    start_ipython({'client': client})


if __name__ == '__main__':
    # pox test/server_client_test.py server
    # pox test/server_client_test.py client
    cli.run()
