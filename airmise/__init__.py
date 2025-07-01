if 1:
    import lk_logger
    lk_logger.setup(quiet=True)

from . import const
from . import remote_control
from .client import Client
from .client import call
from .client import config
from .client import connect
from .client import default_client
from .client import run
from .client import run as exec
from .const import CLIENT_DEFAULT_PORT
from .const import DEFAULT_HOST
from .const import DEFAULT_PORT
from .const import SERVER_DEFAULT_PORT
from .const import WEBAPP_DEFAULT_PORT
from .environment import non_native
from .export import export_functions
from .remote_control import delegate
from .remote_control import register
from .remote_control import wrap
from .server import Server
from .server import run_server
from .serdes import dump
from .serdes import load
from .util import get_local_ip_address
from .util import random_name
# from .webapp import UserLocalServer
# from .webapp import WebClient
# from .webapp import WebServer

__version__ = '0.4.0'
