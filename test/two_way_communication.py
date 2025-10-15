import airmise as air
from argsense import cli
from lk_utils import run_new_thread
from lk_utils import wait


@cli
def server() -> None:
    svr = air.Server(port=2184)
    # svr.run()
    run_new_thread(svr.run)
    
    input('press enter to continue: ')
    
    conn = None
    for _ in wait(3, 0.1):
        if svr.connections:
            print(svr.connections)
            for one in svr.connections.values():
                conn = one
                break
            break
    
    conn.set_active()
    print(conn.call('hello', 'world'))


@cli
def client() -> None:
    # client = air.Client('47.102.108.149', 2184)
    client = air.Client('localhost', 2184)
    client.open()
    
    def _echo(name):
        print(f'hello {name}')
        return 'ok'
    
    client.master.set_passive({
        'hello': _echo,
    })


if __name__ == '__main__':
    cli.run()
