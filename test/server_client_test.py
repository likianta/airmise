import airmise as air
from argsense import cli


@cli
def server(port: int = air.DEFAULT_PORT) -> None:
    def foo(*args, **kwargs) -> str:
        print(args, kwargs)
        return 'ok'

    air.Server().run({'foo': foo}, port=port)


@cli
def client(server_port: int = air.DEFAULT_PORT) -> None:
    client = air.Client().connect(port=server_port)

    result = client.call('foo', 123, 456, abc='xyz')
    print(result)  # -> ok

    client.exec(
        """
        from lk_utils import fs
        def bar():
            file = 'uv.lock'
            print(file, fs.filesize(file, str))
            return fs.load(file)

        assert bar() is not None
        return None
        """
    )

    print(len(client.call('bar')))

    result = client.exec(
        """
        print('hello world')  # this should be found in the server console
        return 123
        """
    )
    print(result)  # -> 123


if __name__ == '__main__':
    # python test/server_client_test.py server
    # python test/server_client_test.py client
    cli.run()
