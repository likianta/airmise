"""
this file is used for `build/build.py` to track all imported modules. please
don't run this file directly.
"""

if 1:
    import sys
    sys.path.append('deps/core')
    sys.path.append('deps/extra')

if 2:
    from aircontrol import SERVER_DEFAULT_PORT
    from aircontrol import server

if 3:  # extra
    import hid
    import modbus_tk
    import serial

server.run(
    host='localhost',
    port=SERVER_DEFAULT_PORT,
    user_namespace={
        'hid'      : hid,
        'serial'   : serial,
        'modbus_tk': modbus_tk,
    }
)
