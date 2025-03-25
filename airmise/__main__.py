from argsense import cli
from lk_utils import run_new_thread

from . import const
from .client import Client
from .server import Server
from .util import get_local_ip_address


@cli.cmd()
def show_my_ip() -> None:
    print(get_local_ip_address(), ':v2s1')


@cli.cmd()
def run_server(
    host: str = '0.0.0.0',
    port: int = const.DEFAULT_PORT,
    **kwargs
) -> None:
    server = Server()
    server.run(kwargs, host=host, port=port)


@cli.cmd()
def run_client(
    host: str = 'localhost',
    port: int = const.SERVER_DEFAULT_PORT,
    path: str = '/',
) -> None:
    import airmise as air
    from lk_logger import start_ipython
    client = Client()
    client.config(host, port, path)
    client.open()
    start_ipython({
        'air'   : air,
        'client': client,
        'run'   : client.run,
        'call'  : client.call,
    })


@cli.cmd()
def remote_call(
    host: str,
    func_name: str,
    *args,
    port: int = const.DEFAULT_PORT,
    backdoor: bool = False,
    **kwargs
) -> None:
    if backdoor:
        back_host, back_port = get_local_ip_address(), const.SECONDARY_PORT
        # run_server(back_host, back_port)
        run_new_thread(run_server, (back_host, back_port))
        kwargs['client_backdoor'] = (back_host, back_port)
    client = Client()
    client.config(host=host, port=port)
    client.open()
    client.call(func_name, *args, **kwargs)


if __name__ == '__main__':
    # pox -m airmise show-my-ip
    # pox -m airmise run-server
    # pox -m airmise run-client
    # pox -m airmise run-local-server
    cli.run()
