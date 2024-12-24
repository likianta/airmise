import airmise as air
from argsense import cli


@cli.cmd()
def server() -> None:
    def foo(*args, **kwargs) -> str:
        print(args, kwargs)
        return 'ok'
    
    server = air.Server()
    server.run({'foo': foo}, host=air.get_local_ip_address(), port=2140)


@cli.cmd()
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
    
    result = client.run(
        '''
        print('hello world')  # this should be found in the server console
        return 123
        '''
    )
    print(result)  # -> 123


if __name__ == '__main__':
    # pox test/server_client_test.py server
    # pox test/server_client_test.py client
    cli.run()
