import re
import typing as t

_re_escape = re.compile(r'[\\"]')


def dump(data: t.Any) -> str:
    """
    warning: very limited support!
    """
    _caller_layer = 1
    
    def serialize(node: t.Any) -> t.Union[str, tuple, dict]:
        nonlocal _caller_layer
        _caller_layer += 1
        
        if isinstance(node, str):
            return node
        if isinstance(node, (tuple, list, set)):
            return tuple(map(serialize, node))
        if isinstance(node, dict):
            return {k: serialize(v) for k, v in node.items()}
        
        # trusted types
        if isinstance(node, (bool, bytes, int, float, type(None))):
            return node
        
        # untrusted object
        # # raise Exception('unserializable object!')
        x = str(node)
        #   e.g. '<object at 0x7f...>', '[object, object, ...]'
        if x.startswith('<') and x.endswith('>'):
            print(':v3', 'this maybe a unserializable object!', node)
        return x
    
    out = serialize(data)
    if isinstance(out, str):
        return '\\' + out  # the leading backslash is a custom flag that \
        #   notifies deserializer to treat it as plain string.
    return str(out)


def load(data: str) -> t.Any:
    if data.startswith('\\'):  # fast recognize pure str type.
        return data[1:]
    try:
        return eval(data)
    except Exception as e:
        print(':v4', 'failed deserializing data!', data)
        raise e
