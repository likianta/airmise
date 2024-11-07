from argsense import cli
from lk_utils import fs

import airmise as air


@cli.cmd()
def server() -> None:
    def foo() -> bytes:
        return fs.load(r'C:\Likianta\temp\2024-11\util.py', 'binary')
    
    air.Server().run(user_namespace={'foo': foo})


@cli.cmd()
def client() -> None:
    air.connect()
    data = air.call('foo')
    fs.dump(data, 'test/_downloaded.txt', 'binary')


if __name__ == '__main__':
    # pox test/transfer_file_in_binary.py server
    # pox test/transfer_file_in_binary.py client
    #   see test/_downloaded.txt
    cli.run()
