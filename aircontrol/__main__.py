from argsense import cli

from . import const
from .client import client_runner
from .server import get_local_ip_address
from .server import server_runner


@cli.cmd()
def show_ip() -> None:
    print(get_local_ip_address(), ':v2s1')


@cli.cmd()
def run_server(
    host: str = get_local_ip_address(),
    port: int = const.SERVER_DEFAULT_PORT,
    debug: bool = False,
) -> None:
    server_runner.run(
        host=host,
        port=port,
        auto_reload=debug,
        access_log=False,
        single_process=True,  # FIXME: why multi-process does not work?
    )


@cli.cmd()
def run_client(
    host: str = 'localhost',
    port: int = const.CLIENT_DEFAULT_PORT,
) -> None:
    if host not in ('localhost', '127.0.0.1'):
        print(':v3', 'generally client should be run on localhost')
    client_runner.run(host=host, port=port, single_process=True)


if __name__ == '__main__':
    # pox -m aircontrol run-server
    # pox -m aircontrol run-client
    cli.run()
