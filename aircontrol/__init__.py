if 1:
    import sys
    sys.path.append('deps/core')
    sys.path.append('deps/extra')

if 2:
    import lk_logger
    lk_logger.setup(quiet=True)

from . import frontend
from .client import client_runner
from .executor import client
from .executor import server  # DELETE?
from .executor import webapp
from .serdes import dump
from .serdes import load
from .server import messenger
from .server import server_runner
