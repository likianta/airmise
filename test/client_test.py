from random import choice

from argsense import cli
from lk_logger import start_ipython

import aircontrol as air


@cli.cmd()
def main(**kwargs) -> None:
    air.connect(**kwargs)
    
    def _demo1() -> None:
        ret = air.run(
            '''
            from random import randint
            class FakeDriver:
                def read(self, reg):
                    return randint(0, 0xFFFF)
            memo d := FakeDriver()
            return (reg, d.read(reg))
            ''',
            {'reg': (x := choice((0xA, 0xB, 0xC, 0xD)))}
        )
        print(hex(x), hex(ret[0]), hex(ret[1]))
    
    def _demo2() -> None:
        ret = air.run(
            '''
            memo d
            return (reg, d.read(reg))
            ''',
            {'reg': (x := choice((0xA, 0xB, 0xC, 0xD)))}
        )
        print(hex(x), hex(ret[0]), hex(ret[1]))
    
    start_ipython({
        'air'  : air,
        'demo1': _demo1,
        'demo2': _demo2,
    })


if __name__ == '__main__':
    # 1. pox -m aircontrol run-local-server
    # 2. pox test/client_test.py
    #   in ipython:
    #       demo1()
    #       demo2()
    #       ...
    main()
