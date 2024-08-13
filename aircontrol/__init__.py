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
from .executor import client
from .executor import replace_default_executor
from .executor import run
from .executor import server  # DELETE?
from .executor import webapp
from .frontend import FRONTEND_SCRIPT
from .frontend import FRONTEND_TAG
from .frontend import is_frontend_online
# from .serdes import dump
# from .serdes import load
from .server import messenger
from .server import server_runner
from .util import get_local_ip_address
from .util import random_name
