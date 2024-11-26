import airmise as air
from argsense import cli


@cli.cmd()
def server() -> None:
    def foo():
        for i in range(10):
            yield i
    
    air.Server().run({'foo': foo})


@cli.cmd()
def client() -> None:
    for i in air.call('foo', _iter=True):
        print(i)
        if i == 5:
            print('break')
            break
    
    for i in air.call('foo', _iter=True):
        print(i)


if __name__ == '__main__':
    cli.run()
