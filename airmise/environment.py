import typing as tp
from contextlib import contextmanager

# native: bool = True
working_mode: tp.Literal['native', 'server', 'client'] = 'native'


@contextmanager
def non_native() -> tp.Iterator:
    global working_mode
    backup = working_mode
    working_mode = 'client'
    yield
    working_mode = backup
