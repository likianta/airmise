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
from collections import defaultdict
from inspect import getfullargspec
from types import FunctionType

from lk_utils import fs
from lk_utils.textwrap import dedent
from lk_utils.textwrap import join


class T:
    FallbackType = t.Literal['any', 'str']
    PlainParamType = t.Literal[
        'any', 'bool', 'dict', 'float', 'int',
        'list', 'none', 'set', 'str', 'tuple',
    ]


def export_functions(
    funcs: t.Iterable[t.Union[FunctionType, t.Callable]], output_path: str
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
        _export_functions_to_file(funcs, output_path)
    else:
        pass


# -----------------------------------------------------------------------------

def _export_functions_to_file(
    funcs: t.Iterable[FunctionType], output_path: str
) -> None:
    classified_funcs = _classify_functions(funcs)
    # if len(classified_funcs) > 1:
    #     used_names = set()
    #     for xdict in classified_funcs.values():
    #         for func_name, func_info in xdict.items():
    #             if func_name in used_names:
    #                 raise Exception(
    #                     'duplicate func name across modules', func_info
    #                 )
    #             else:
    #                 used_names.add(func_name)
    
    write_rows = [
        'import airmise as air',
        'from functools import partial',
        'from typing import Any',
        '',
    ]
    show_module_name_divider_line = len(classified_funcs) > 1
    defined_funcnames = []
    
    for key0 in sorted(classified_funcs.keys()):
        if show_module_name_divider_line:
            module_name = key0
            write_rows.append('# {} {}'.format(
                '-' * (80 - 2 - len(module_name) - 1), module_name
            ))
            write_rows.append('')
        
        for key1 in sorted(classified_funcs[key0].keys()):
            func_name = key1
            func_info = classified_funcs[key0][key1]
            signature = func_info['signature']
            
            write_rows.append(
                'def {}({}) -> {}:  # noqa'.format(
                    func_name,
                    ', '.join(filter(None, (
                        ', '.join(
                            (
                                name if name.startswith('*') else
                                '{}: {}'.format(name, _translate_type(type_))
                            )
                            for name, type_ in signature['args']
                        ),
                        ', '.join(
                            (
                                name if name.startswith('**') else
                                '{}: {} = {}'.format(
                                    name, _translate_type(type_), default
                                )
                            )
                            for name, type_, default in signature['kwargs']
                        )
                    ))),
                    _translate_type(signature['return'])
                )
            )
            if func_info['document']:
                write_rows.append(
                    '    """{}"""'.format(func_info['document'])
                )
            write_rows.append('    ...')
            write_rows.append('')
            
            defined_funcnames.append(func_name)
    
    write_rows.append(dedent(
        '''
        globals().update({{
            {}
        }})
        '''
    ).format(join(
        (
            '"{}": partial(air.call, "{}"),'.format(x, x)
            for x in sorted(set(defined_funcnames))
        ),
        4
    )))
    
    fs.dump(write_rows, output_path)


def _export_functions_to_dir(
    funcs: t.Iterable[FunctionType], output_path: str
) -> None:
    raise NotImplementedError


# -----------------------------------------------------------------------------

def _classify_functions(
    funcs: t.Iterable[FunctionType]
) -> t.Dict[str, t.Dict[str, dict]]:
    """
    returns:
        {module_name: {func_name: func_info, ...}, ...}
            module_name: e.g. 'foo.bar.baz'
    """
    out = defaultdict(dict)
    for f in funcs:
        info = _parse_function(f)
        out[info['module']][info['name']] = info
    return out


def _parse_function(func: FunctionType) -> dict:
    spec = getfullargspec(func)
    ''' ^
    example:
        def foo(a: str, b: int, c=123, *args, d: bool = False, **kwargs):
            pass
        spec = getfullargspec(foo)
        #   FullArgSpec(
        #       args=['a', 'b', 'c'],
        #       varargs='args',
        #       varkw='kwargs',
        #       defaults=(123,),
        #       kwonlyargs=['d'],
        #       kwonlydefaults={'d': False},
        #       annotations={
        #           'a': <class 'str'>,
        #           'b': <class 'int'>,
        #           'd': <class 'bool'>,
        #       }
        #   )
    '''
    annotations = Annotations(spec.annotations)
    
    args = []
    if spec.defaults:
        args_count = len(spec.args) - len(spec.defaults)
    else:
        args_count = len(spec.args)
    for i in range(0, args_count):
        name = spec.args[i]
        type_ = annotations.get_arg_type(name)
        args.append((name, type_))
    if spec.varargs:
        args.append(('*' + spec.varargs, 'any'))
    
    kwargs = []
    if spec.defaults:
        enum: t.Iterator[t.Tuple[int, int]] = enumerate(
            range(len(spec.args) - len(spec.defaults), len(spec.args))
        )
        for i, j in enum:
            name = spec.args[j]
            default = spec.defaults[i]
            type_ = annotations.get_kwarg_type(name, default)
            kwargs.append((name, type_, default))
    if spec.kwonlyargs:
        for name, default in spec.kwonlydefaults.items():
            type_ = annotations.get_kwarg_type(name, default)
            kwargs.append((name, type_, default))
    if spec.varkw:
        kwargs.append(('**' + spec.varkw, 'any', ...))
    
    return_ = annotations.get_return_type()
    
    return {
        'module'   : func.__module__,
        'name'     : func.__name__,
        'document' : func.__doc__ or '',
        'signature': {
            'args'  : args,
            'kwargs': kwargs,
            'return': return_,
        }
    }


def _translate_type(type0: T.PlainParamType) -> str:
    if type0 == 'any':
        return 'Any'
    elif type0 == 'none':
        return 'None'
    else:
        return type0


class Annotations:
    
    def __init__(
        self,
        annotations: t.Dict[str, t.Any],
        fallback_type: T.FallbackType = 'any'
    ) -> None:
        self.annotations = annotations
        self._fallback_type = fallback_type
        self._type_2_str = {
            'any'    : 'any',
            'anystr' : 'str',
            'bool'   : 'bool',
            'dict'   : 'dict',
            'float'  : 'float',
            'int'    : 'int',
            'list'   : 'list',
            'literal': 'str',
            'none'   : 'none',
            'set'    : 'set',
            'str'    : 'str',
            'tuple'  : 'tuple',
            'union'  : 'any',
        }
        # if config.BARE_NONE_MEANS_ANY:
        #     self._type_2_str['none'] = 'any'
    
    # noinspection PyUnresolvedReferences,PyProtectedMember
    def _normalize_type(self, type_: t.Any) -> T.PlainParamType:
        out = str(type_)
        
        if isinstance(type_, str):
            pass
        elif isinstance(type_, t._TypedDictMeta):
            return 'dict'
        elif (
            (x := getattr(type_, '__base__', None)) and
            str(x) == "<class 'tuple'>"
        ):
            return 'tuple'  # typing.NamedTuple
        else:
            # if we are running in lower version python, be noted some classes -
            # are not available.
            _is_legacy_typing: bool = (
                getattr(t, '_LiteralGenericAlias', None) is None
            )
            if _is_legacy_typing:
                if isinstance(type_, t._GenericAlias):
                    return 'any'
            else:
                if isinstance(type_, t._LiteralGenericAlias):
                    # e.g.
                    #   sometype = typing.Literal['A', 'B', 'C']
                    #   type(sometype)  # -> typing._LiteralGenericAlias
                    return 'str'
                elif isinstance(type_, t._UnionGenericAlias):
                    # e.g.
                    #   sometype = typing.Union[str, None]
                    #   type(sometype)  # -> typing._UnionGenericAlias
                    return self._normalize_type(type_.__args__[0])
                elif isinstance(type_, t._GenericAlias):
                    out = type_._name
        
        assert isinstance(out, str)
        out = out.lower()
        if out.startswith('<class '):
            out = out[8:-2]  # "<class 'list'>" -> "list"
        if '[' in out:
            out = out.split('[', 1)[0]
        # print(':v', type_, out)
        if out in self._type_2_str:
            return self._type_2_str[out]
        return 'any'
    
    def get_arg_type(self, name: str) -> T.PlainParamType:
        if name in self.annotations:
            return self._normalize_type(self.annotations[name])
        else:
            return self._fallback_type
    
    def get_kwarg_type(self, name: str, value: t.Any) -> T.PlainParamType:
        if name in self.annotations:
            out = self._normalize_type(self.annotations[name])
        else:
            out = self.deduce_type_by_value(value)
        # noinspection PyTypeChecker
        return out
    
    def get_return_type(self) -> T.PlainParamType:
        if 'return' in self.annotations:
            return self._normalize_type(self.annotations['return'])
        else:
            return 'none'
    
    @staticmethod
    def deduce_type_by_value(default: t.Any) -> T.PlainParamType:
        dict_ = {
            bool : 'bool',
            dict : 'dict',
            float: 'float',
            int  : 'int',
            list : 'list',
            set  : 'set',
            str  : 'str',
            tuple: 'tuple',
        }
        # noinspection PyTypeChecker
        return dict_.get(type(default), 'any')
