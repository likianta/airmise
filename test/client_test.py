from random import choice

from argsense import cli

import aircontrol as air


@cli.cmd()
def main(**kwargs) -> None:
    air.connect(**kwargs)
    
    ret = air.run(
        '''
        from random import randint
        class FakeDriver:
            def read(self, reg):
                # from random import randint
                return randint(0, 0xFFFF)
        memo d := FakeDriver()
        return (reg, d.read(reg))
        ''',
        reg=(x := choice((0xA, 0xB, 0xC, 0xD)))
    )
    print(hex(x), hex(ret[0]), hex(ret[1]))
    
    ret = air.run(
        '''
        memo d
        return (reg, d.read(reg))
        ''',
        reg=(x := choice((0xA, 0xB, 0xC, 0xD)))
    )
    print(hex(x), hex(ret[0]), hex(ret[1]))


if __name__ == '__main__':
    # 1. pox -m aircontrol run-local-server
    # 2. pox test/client_test.py
    main()
