import sys

from argsense import cli
from lk_utils import run_cmd_args

import airmise as air


@cli.cmd()
def server() -> None:
    air.Server().run({'foo': _foo})


def _foo(*args, client_backdoor, **kwargs) -> str:
    print(args, kwargs)
    _list_client_files(*client_backdoor)
    return 'ok'


def _list_client_files(client_host, client_port):
    air.connect(client_host, client_port)
    files = air.run(
        '''
        import os
        return os.listdir(os.getcwd())
        '''
    )
    print(files, ':l')


# -----------------------------------------------------------------------------

@cli.cmd()
def client() -> None:
    run_cmd_args(
        (
            sys.executable, '-m', 'airmise', 'remote-call', 'localhost', 'foo',
            'aaa', 'bbb', '--ccc', 'ddd', '--interactive'
        ),
        verbose=True,
        force_term_color=True,
    )


if __name__ == '__main__':
    # pox test/remote_call.py server
    # pox test/remote_call.py client
    cli.run()
