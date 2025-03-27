import airmise as air
from argsense import cli


# noinspection PyMethodMayBeStatic
@air.wrap
class ServerSide:
    
    def normal(self):
        print('hello world')
        return 'ok'
    
    def special(self):
        return _SpecialObject()


# noinspection PyMethodMayBeStatic
class _SpecialObject:
    def echo(self, name: str) -> None:
        print(f'hello {name}')


@cli.cmd()
def server():
    air.run_server()


@cli.cmd()
def client():
    air.connect(air.get_local_ip_address())
    with air.non_native():
        server = ServerSide()
        resp = server.normal()
        print(resp)
        server.special().echo('alice')


if __name__ == '__main__':
    # pox test/interact_with_remote_object.py server
    # pox test/interact_with_remote_object.py client
    cli.run()
