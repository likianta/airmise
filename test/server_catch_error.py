import aircontrol as air
from argsense import cli


@cli.cmd()
def server():
    air.Server().run('localhost')


@cli.cmd()
def client(case: int):
    air.connect()
    if case == 1:
        air.run(
            '''
            print(1 / 0)
            '''
        )
    if case == 2:
        air.run(
            '''
            from lk_utils import new_thread
            @new_thread()
            def foo():
                print(1 / 0)
            foo()
            '''
        )


if __name__ == '__main__':
    # pox test/server_catch_error.py server
    # pox test/server_catch_error.py client
    cli.run()
