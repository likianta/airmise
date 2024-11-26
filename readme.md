# Airmise

Expose local runtime namespace to local network. Others who have access to the 
network can call the functions, classes, use the variables, import the modules
in the runtime namespace.

## How to use

Server side:

```python
import airmise as air

aaa = 123
bbb = []

def ccc(*args, **kwargs):
    print(args, kwargs)
    return 'ok'

class DDD:
    def eee(self):
        return 'eee'

air.Server().run(host='0.0.0.0', port=2014, user_namespace=globals())
```

Client side:

```python
import airmise as air

air.connect(<host>, port=2014)
#   the host is the server's ip address, for example '192.168.10.123'. 
#   you need to get it from the server manager.

# run code
result = air.run(
    '''
    print(aaa)
    bbb.append(456)
    result = ccc(1, 2, 3, a=4, b=5)
    ddd = DDD()
    print(ddd.eee())
    return result
    '''
)
print(result)  # -> 'ok'

# call function
result = air.call('ccc', 1, 2, 3, a=4, b=5)
print(result)  # -> 'ok'
```
