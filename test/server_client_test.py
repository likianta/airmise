import airmise as air
from argsense import cli
from lk_logger import start_ipython


@cli.cmd()
def server() -> None:
    def foo(*args, **kwargs) -> str:
        print(args, kwargs)
        return 'ok'
    
    air.Server().run({'foo': foo})


@cli.cmd()
def client(
    server_host: str = air.DEFAULT_HOST,
    server_port: int = air.DEFAULT_PORT,
    interactive: bool = False,
) -> None:
    """
    kwargs:
        interactive (-i):
    """
    air.connect(server_host, server_port)
    
    result = air.call('foo', 123, 456, abc='xyz')
    print(result)
    
    result = air.run(
        '''
        print('hello world')  # this should be found in the server console
        return 123
        '''
    )
    print(result)
    
    if interactive:
        start_ipython(user_ns={'air': air})


if __name__ == '__main__':
    # pox test/server_client_test.py server
    # pox test/server_client_test.py client
    cli.run()
