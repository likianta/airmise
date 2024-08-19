# from IPython import start_ipython
from argsense import cli
from lk_logger import start_ipython

import aircontrol as air


@cli.cmd()
def test_client(
    server_host: str,
    server_port: int = air.SERVER_DEFAULT_PORT
) -> None:
    air.connect(server_host, server_port)
    result = air.run(
        '''
        print('hello world')  # this should be found in the server console
        return 123
        '''
    )
    print(result)
    start_ipython(user_ns={'air': air})


if __name__ == '__main__':
    # computer A: pox -m aircontrol run-server
    #   got server running url.
    # computer B: pox test/server_client_test.py <server_host> <server_port>
    #   entered ipython:
    #       air.run(...)
    cli.run(test_client)
