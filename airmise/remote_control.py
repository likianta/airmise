import typing as t
from functools import partial
from . import client
from . import environment

_references = {}


class T:
    Object = t.TypeVar('Object', bound=t.Union[t.Type, t.Callable])


def wrap(obj: T.Object) -> T.Object:
    if str(type(obj)) == "<class 'type'>":
        # obj is a class
        
        _references[obj.__qualname__] = obj
        
        def _instantiate_class(*args, **kwargs):
            if environment.working_mode == 'client':
                remote_obj_id = client.run(
                    '''
                    import airmise as air
                    from uuid import uuid1
                    some_class = air.remote_control.seek_reference(qualname)
                    instance = some_class(*args, **kwargs)
                    uid = uuid1().hex
                    air.remote_control.store_object(uid, instance)
                    return uid
                    ''',
                    qualname=obj.__qualname__,
                    args=args,
                    kwargs=kwargs,
                )
                return RemoteCall(remote_obj_id)
            else:
                return obj(*args, **kwargs)
            
        return _instantiate_class
    else:
        raise NotImplementedError


def fetch_object(key):
    return _references[key]


def store_object(key: str, obj: t.Any):
    _references[key] = obj


def seek_reference(qualname: str) -> object:
    return _references[qualname]


class RemoteCall:
    
    def __init__(self, remote_object_id: str):
        self._id = remote_object_id
    
    def __getattr__(self, item):
        return partial(self._call, item)
    
    def _call(self, funcname: str, *args, **kwargs):
        return client.run(
            '''
            import airmise as air
            obj = air.remote_control.fetch_object(uid)
            return getattr(obj, funcname)(*args, **kwargs)
            ''',
            uid=self._id,
            funcname=funcname,
            args=args,
            kwargs=kwargs,
        )
