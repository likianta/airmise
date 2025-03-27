import typing as t
from contextlib import contextmanager

# native: bool = True
working_mode: t.Literal['native', 'server', 'client'] = 'native'


@contextmanager
def non_native() -> t.Iterator:
    global working_mode
    backup = working_mode
    working_mode = 'client'
    yield
    working_mode = backup
