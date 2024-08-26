if 1:
    import sys
    sys.path.append('deps/core')
    sys.path.append('deps/extra')

if 2:
    import lk_logger
    lk_logger.setup(quiet=True)

from . import const
from .client import Client
from .client import client
from .client import connect
from .client import run
from .const import CLIENT_DEFAULT_PORT
from .const import SERVER_DEFAULT_PORT
from .const import WEBAPP_DEFAULT_PORT
from .serdes import dump
from .serdes import load
from .server import run_server as serving
from .server import server
from .util import get_local_ip_address
from .util import random_name
from .webapp import LocalServer
from .webapp import WebClient
from .webapp import WebServer
