# Airmise

Expose local runtime namespace to local network area. Others who have access to 
the network can call functions, instantiate classes, use variables, import 
modules etc.

## How to use

### Access variables

```python
# server.py
import airmise as air
a = 'alpha'
b = []
air.run_server(globals(), port=...)
```

```python
# client.py
import airmise as air
air.connect(host=..., port=...)
c = air.exec(
    '''
    print(a)
    print(b)
    b.append(a)
    return b
    '''
)
print(c)  # -> ['alpha']
```

### Call functions

```python
# server.py
import airmise as air

def foo(bar):
    print(bar)
    return 'ok'
    
air.run_server(globals(), port=...)
```

```python
# client.py
import airmise as air
air.connect(host=..., port=...)
air.exec("return foo('bar')")
```

### Iterator

```python
# server.py
import airmise as air

def foo(count: int):
    for i in range(count):
        yield i
    
air.run_server(globals(), port=...)
```

```python
# client.py
import airmise as air
air.connect(host=..., port=...)
for i in air.call('foo', 10):
    print(i)
```

### Share codebase

Server and client can use the same code base, but with different 
`if __name__ == '__main__'`:

```python
# server.py
import airmise as air

class Bar:
    def __init__(self, name: str):
        self.name = name
    def baz(self):
        return f'{self.name} 123'  

if __name__ == '__main__':
    air.register(Bar)
    air.run_server(port=...)
```

```python
# client.py
import airmise as air

class Bar:
    def __init__(self, name: str):
        self.name = name
    def baz(self):
        return f'{self.name} 123'  

if __name__ == '__main__':
    remote_bar = air.delegate(Bar, 'Alice')
    print(remote_bar)  # -> <airmise.RemoteCall>
    print(remote_bar.baz())  # -> 'Alice 123'
```
