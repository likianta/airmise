import airmise as air
from argsense import cli
from lk_utils import start_ipython
from neoprint import print


@cli
def start_server() -> None:
    air.frp.run_transceiver(port=2144)


@cli
def start_client(target_host: str, target_port: int = 2144) -> None:
    air.frp.connect_to_public_transport(
        {'test': _greeting},
        source_port=2140,
        target_host=target_host,
        target_port=target_port,
    )


@cli
def proxy_part_1() -> None:
    air.frp.Router().run(port=2140)


@cli
def proxy_part_2() -> None:
    user_client = air.frp.Callee().connect(port=2140)
    # uid = user_client.call('register_user')
    # print(uid, ':v2n')
    # user_client.set_passive({'ping': _ping}, switch_roleplay=False)  # blocking
    user_client.mainloop({'ping': _ping, 'greeting': _greeting})


@cli
def proxy_part_3(
    uid: str, interactive: bool = False, close: bool = True
) -> None:
    master = air.frp.Caller(uid).connect(port=2140)
    pong = master.call('ping')
    print(pong)
    # assert pong == 'pong'
    assert pong.startswith('pong')
    if interactive:
        start_ipython(locals())
    # if close:
    #     master.close()


def _greeting(name: str) -> None:
    print(f'hello {name}')


_idx = 0


def _ping() -> str:
    global _idx
    _idx += 1
    print('ping ({:02})'.format(_idx))
    return 'pong ({:02})'.format(_idx)


if __name__ == '__main__':
    # pox test/frp_test.py start-server
    # pox test/frp_test.py start-client localhost
    cli.run()
