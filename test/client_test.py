from lk_logger import start_ipython

from aircontrol import Client


def test() -> None:
    client = Client()
    
    def _demo() -> None:
        from random import choice
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
    
    start_ipython({
        'client': client,
        'run'   : client.run,
        'demo'  : _demo,
    })


if __name__ == '__main__':
    # pox test/client_test.py
    test()
