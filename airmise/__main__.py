from argsense import cli
from lk_utils import run_new_thread
from . import const
from . import util
from .client import Client
from .server import Server

@cli
def show_my_ip() -> None:
    print(util.get_local_ip_address(), ':v2s1')

@cli
def run_server(
    host: str = '0.0.0.0',
    port: int = const.DEFAULT_PORT,
    **kwargs
) -> None:
    """
    params:
        port (-p):
    """
    server = Server()
    server.run(kwargs, host=host, port=port)

@cli
def run_client(
    host: str = 'localhost',
    port: int = const.ALTER_PORT,
    path: str = '/',
) -> None:
    import airmise as air
    from lk_utils import start_ipython
    air.connect(host, port, path)
    start_ipython({'air': air})

@cli
def remote_call(
    host: str,
    func_name: str,
    *args,
    port: int = const.DEFAULT_PORT,
    backdoor: bool = False,
    **kwargs
) -> None:
    if backdoor:
        back_host, back_port = util.get_local_ip_address(), const.ALTER_PORT
        # run_server(back_host, back_port)
        run_new_thread(run_server, (back_host, back_port))
        kwargs['client_backdoor'] = (back_host, back_port)
    client = Client()
    client.config(host=host, port=port)
    client.open()
    client.call(func_name, *args, **kwargs)

@cli
def is_port_occupied(port: int) -> None:
    # from lk_utils.time import timeit
    # from functools import partial
    # if timeit(partial(util.is_port_occupied, port), 'callable'):
    if util.is_port_occupied(port):
        print(f'port {port} is occupied', ':v8')
    else:
        print(f'port {port} is free to use', ':v4')

if __name__ == '__main__':
    # pox -m airmise show-my-ip
    # pox -m airmise run-server
    # pox -m airmise run-client
    # pox -m airmise run-local-server
    cli.run()
