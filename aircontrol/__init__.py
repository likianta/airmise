if 1:
    import sys
    sys.path.append('deps/core')
    sys.path.append('deps/extra')

if 2:
    import lk_logger
    lk_logger.setup(quiet=True)

from .client import client_runner
from .const import CLIENT_DEFAULT_PORT
from .const import SERVER_DEFAULT_PORT
from .const import WEBAPP_DEFAULT_PORT
from .executor import connect
from .executor import executor
from .executor import run
from .frontend import FRONTEND_SCRIPT
from .frontend import FRONTEND_TAG
from .frontend import is_frontend_online
from .serdes import dump
from .serdes import load
from .server import run_server as serving
from .util import get_local_ip_address
from .util import random_name
from .webapp import messenger
from .webapp import webapp_runner
