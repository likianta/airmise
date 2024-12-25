import airmise as air


def main(aaa: str, bbb: int, *ccc, ddd: dict = None, **fff) -> dict:
    """
    fly two thus too describe. kind many will.
    """
    pass


air.export_functions(
    {'foo': main},
    'test/_shell.py'
)
