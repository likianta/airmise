import airmise as air
from argsense import cli
from lk_utils import start_ipython
from neoprint import print


@cli
def server() -> None:
    air.frp.run_transceiver(port=2144)


@cli
def client(target_host: str, target_port: int = 2144) -> None:
    air.frp.connect_to_public_transport(
        {'test': _greeting},
        source_port=2140,
        target_host=target_host,
        target_port=target_port,
    )


@cli
def proxy_role_1() -> None:
    air.frp.Router().run(port=2140)


@cli
def proxy_role_2() -> None:
    callee = air.frp.Callee().connect(port=2140)
    callee.mainloop({'greeting': _greeting, 'ping': _ping})


@cli
def proxy_role_3(
    uid: str, interactive: bool = False, close: bool = True
) -> None:
    caller = air.frp.Caller(uid).connect(port=2140)
    caller.call('greeting', 'Alice')
    pong = caller.call('ping')
    print(pong)
    assert pong == 'pong'
    if interactive:
        start_ipython(locals())
    if close:
        caller.close()


def _greeting(name: str) -> None:
    print(f'Hello {name}')


def _ping() -> str:
    print('ping', ':i')
    return 'pong'


if __name__ == '__main__':
    # python test/frp_test.py server
    # python test/frp_test.py client localhost
    # python test/frp_test.py proxy_role_1
    # python test/frp_test.py proxy_role_2
    # python test/frp_test.py proxy_role_3 <uid>
    # python test/frp_test.py proxy_role_3 <uid> --interactive
    cli.run()
