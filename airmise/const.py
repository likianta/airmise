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

import os


class AutoId:
    def __init__(self) -> None:
        self._number = 0
    
    def __call__(self) -> int:
        self._number += 1
        return self._number


_autoid = AutoId()

DEFAULT_HOST = '0.0.0.0'
DEFAULT_PORT = 2140
SECONDARY_PORT = 2141

# FLAG
CALL_FUNCTION = _autoid()
NORMAL_OBJECT = _autoid()
SPECIAL_OBJECT = _autoid()
INTERNAL = _autoid()
ITERATOR = _autoid()
YIELD = _autoid()
YIELD_OVER = _autoid()
ERROR = _autoid()
CLOSED = _autoid()


# class InternalCommand:
#     EXIT_ROLEPLAY = _autoid()
#     NOHTING = _autoid()
#     SWITCH_ROLEPLAY = _autoid()
#     WHAT_DO_YOU_WANT = _autoid()


# DELETE BELOW
SERVER_DEFAULT_PORT = int(os.getenv('AIRCONTROL_SERVER_PORT', '2140'))
WEBAPP_DEFAULT_PORT = int(os.getenv('AIRCONTROL_WEBAPP_PORT', '2141'))
CLIENT_DEFAULT_PORT = int(os.getenv('AIRCONTROL_CLIENT_PORT', '2142'))
