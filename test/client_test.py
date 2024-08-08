from random import choice

from lk_logger import start_ipython

from aircontrol import client


def test() -> None:
    client.open(False)
    
    def _demo1() -> None:
        ret = client.run(
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
        ret = client.run(
            '''
            memo d
            return (reg, d.read(reg))
            ''',
            {'reg': (x := choice((0xA, 0xB, 0xC, 0xD)))}
        )
        print(hex(x), hex(ret[0]), hex(ret[1]))
    
    start_ipython({
        'exe'  : client,
        'run'  : client.run,
        'demo1': _demo1,
        'demo2': _demo2,
    })


if __name__ == '__main__':
    # 1. pox -m aircontrol run-client
    # 2. pox test/client_test.py
    #   in ipython:
    #       demo1()
    #       demo2()
    #       ...
    test()
