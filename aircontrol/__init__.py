if 1:
    import sys
    sys.path.append('deps/core')
    sys.path.append('deps/extra')

if 2:
    import lk_logger
    lk_logger.setup(quiet=True)

from .client import client_runner
from .executor import LocalExecutor
from .executor import RemoteExecutor
# from .executor import local_exe
from .executor import remote_exe
from .serdes import dump
from .serdes import load
from .server import messenger
from .server import server_runner
