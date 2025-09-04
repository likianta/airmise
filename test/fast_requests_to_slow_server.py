import airmise as air
from argsense import cli
from time import sleep


@cli
def server() -> None:
    def echo(msg):
        sleep(3)
        return 'ok ({})'.format(msg)
    
    air.run_server(locals())


@cli
def client() -> None:
    print(air.call('echo', 'hello'))
    sleep(1)
    print(air.call('echo', 'world'))


if __name__ == '__main__':
    cli.run()
