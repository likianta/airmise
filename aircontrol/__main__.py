from argsense import cli

from . import const
from .client import Client
from .server2 import Server
from .util import get_local_ip_address
from .webapp import UserLocalServer
from .webapp import WebServer


@cli.cmd()
def show_my_ip() -> None:
    print(get_local_ip_address(), ':v2s1')


@cli.cmd()
def run_server(
    host: str = '0.0.0.0',
    port: int = const.SERVER_DEFAULT_PORT,
    **kwargs
) -> None:
    server = Server()
    server.run(host=host, port=port, user_namespace=kwargs)


@cli.cmd()
def run_local_server(  # DELETE
    # host: str = 'localhost',
    # port: int = const.SERVER_DEFAULT_PORT,
    **kwargs
) -> None:
    # if host not in ('localhost', '127.0.0.1', '0.0.0.0'):
    #     print(':v3', 'the local server should be run on "local" host')
    server = UserLocalServer()
    server.run(user_namespace=kwargs)


@cli.cmd()
def run_web_server():
    server = WebServer()
    server.run()


@cli.cmd()
def run_client(
    host: str = 'localhost',
    port: int = const.SERVER_DEFAULT_PORT,
    path: str = '/',
) -> None:
    from lk_logger import start_ipython
    client = Client()
    client.config(host, port, path)
    start_ipython({
        'client': client,
        'run'   : client.run,
    })


if __name__ == '__main__':
    # pox -m aircontrol run-server
    # pox -m aircontrol run-client
    # pox -m aircontrol run-local-server
    cli.run()
