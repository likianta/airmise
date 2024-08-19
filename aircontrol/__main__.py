from argsense import cli

from . import const
from .client import client_runner
from .server import run_server
from .util import get_local_ip_address


@cli.cmd()
def show_my_ip() -> None:
    print(get_local_ip_address(), ':v2s1')


cli.add_cmd(run_server)


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
