"""
scenario (1):
    ╭─ computer A ─────────────╮
    │  ╭─ python program ────╮ │
    │  │  server_runtime     │ │
    │  │        ││           │ │
    │  │  server_connector ○─┼─┼─╮
    │  ╰─────────────────────╯ │ │
    ╰──────────────────────────╯ │
    ╭─ computer B ─────────────╮ │
    │  ╭─ python program ────╮ │ │
    │  │  client_runtime     │ │ │
    │  │        ││           │ │ │
    │  │  client_connector ●─┼─┼─╯
    │  ╰─────────────────────╯ │
    ╰──────────────────────────╯
        server_connector: http://<server_ip>:2140
        client_connector: http://localhost:2142
        
scenario (2):
    ╭─ computer A ──────────────╮
    │  ╭─ python program ─────╮ │
    │  │  webapp_backend      │ │
    │  │        ││            │ │
    │  │  webapp_connector ○──┼─┼────────────╮
    │  ╰──────────────────────╯ │            │
    ╰───────────────────────────╯            │
    ╭─ computer B ───────────────────────────┼──────╮
    │  ╭─ python program ────╮ ╭─ browser ───┼────╮ │
    │  │  client_runtime     │ │             │    │ │
    │  │        ││           │ │             │    │ │
    │  │  client_connector ●─┼─┼─ webapp_frontend │ │
    │  ╰─────────────────────╯ ╰──────────────────╯ │
    ╰───────────────────────────────────────────────╯
        webapp_connector: http://example.com:2141
        webapp_frontend : https://example.com/some/path
        client_connector: http://localhost:2142
"""

DEFAULT_HOST = '0.0.0.0'
DEFAULT_PORT = 2140
ALTER_PORT = 2141
FRP_PUBLIC_PORT = 2142
FRP_PRIVATE_PORT = 2143
FRP_TRANSCEIVER_PORT = 2144
STANDALONE_UI_PORT = 2145

class AutoId:
    def __init__(self) -> None:
        self._number = 0
    
    def __call__(self) -> int:
        self._number += 1
        return self._number

_autoid = AutoId()

# FLAG
CALL_FUNCTION = _autoid()
CLOSED = _autoid()
DELEGATE = _autoid()
ERROR = _autoid()
INTERNAL = _autoid()
ITERATOR = _autoid()
NORMAL = _autoid()
YIELD = _autoid()
YIELD_OVER = _autoid()

# class InternalCommand:
#     EXIT_ROLEPLAY = _autoid()
#     NOHTING = _autoid()
#     SWITCH_ROLEPLAY = _autoid()
#     WHAT_DO_YOU_WANT = _autoid()
