from argsense import cli

from . import const
from .client import client
from .server import server
from .util import get_local_ip_address


@cli.cmd()
def show_my_ip() -> None:
    print(get_local_ip_address(), ':v2s1')


@cli.cmd()
def run_server(
    host: str = '0.0.0.0',
    port: int = const.SERVER_DEFAULT_PORT,
    **kwargs
) -> None:
    server.run(host=host, port=port, user_namespace=kwargs)


@cli.cmd()
def run_local_server(
    host: str = 'localhost',
    port: int = const.SERVER_DEFAULT_PORT,
    **kwargs
) -> None:
    if host not in ('localhost', '127.0.0.1', '0.0.0.0'):
        print(':v3', 'the local server should be run on "local" host')
    server.run(host=host, port=port, user_namespace=kwargs)


@cli.cmd()
def run_client(
    host: str = 'localhost',
    port: int = const.SERVER_DEFAULT_PORT,
) -> None:
    from lk_logger import start_ipython
    client.connect(host, port, lazy=False)
    start_ipython({
        'client': client,
        'run'   : client.run,
    })


if __name__ == '__main__':
    # pox -m aircontrol run-local-server
    # pox -m aircontrol run-client
    cli.run()
