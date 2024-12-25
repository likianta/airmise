"""
export server functions to client side, like function shell.

illustration:
    server:
        # /<project>/src/foo.py
        def main(a: str, b: int, c: bool = None) -> str:
            print(a, b, c)
            return 'ok'
    client:
        # /site-packages/<server>/foo.py
        def main(a: str, b: int, c: bool = None) -> str:
            ...  # just an ellipsis, no actual code
"""
import typing as t
from types import FunctionType


def export_functions(
    funcs: t.Iterable[FunctionType], output_path: str
) -> None:
    """
    params:
        output_path:
            can be a directory or a file that ends with '.py'.
            if directory, we will create:
                <output_path>  # a directory
                |- __init__.py
                |- <module1>.py
                |- <module2>.py
                |- ...
            if file, we will create:
                <output_path>  # the file ends with '.py'
                #   if `funcs` are come from different modules, `output_path` -
                #   merge them into one.
                #   be careful if there are same function names, the last one -
                #   takes effect.
    """
    if output_path.endswith('.py'):
        pass
    else:
        pass


def _classify_functions(funcs: t.Iterable[FunctionType]) -> t.Dict[str, t.Dict[str, FunctionType]]:
    """
    returns:
        {module_name: (func_info, ...), ...}
            module_name: e.g. 'foo.bar.baz'
            func_info: (func_name, func_signature, func_doc)
    """


def _export_functions_to_file(
    funcs: t.Iterable[FunctionType], output_path: str
) -> None:
    pass


def _export_functions_to_dir(
    funcs: t.Iterable[FunctionType], output_path: str
) -> None:
    pass


