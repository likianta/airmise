if 1:
    import sys
    from os.path import exists
    from lk_utils import xpath
    if exists(xpath('../.airmise_standalone.txt')):
        sys.path.extend(('deps/core', 'deps/extra'))

if 2:
    import lk_logger
    lk_logger.setup(quiet=True)

from . import const
from .client import Client
from .client import config
from .client import connect
from .client import call
from .client import run
from .const import CLIENT_DEFAULT_PORT
from .const import DEFAULT_HOST
from .const import DEFAULT_PORT
from .const import SERVER_DEFAULT_PORT
from .const import WEBAPP_DEFAULT_PORT
from .server3 import Server
from .serdes import dump
from .serdes import load
from .util import get_local_ip_address
from .util import random_name
# from .webapp import UserLocalServer
# from .webapp import WebClient
# from .webapp import WebServer

__version__ = '0.1.0'
