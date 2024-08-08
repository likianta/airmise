if 1:
    import sys
    sys.path.append('deps/core')
    sys.path.append('deps/extra')

if 2:
    import lk_logger
    lk_logger.setup(quiet=True)

from .client import client_runner
# from .executor import client_call
# from .executor import server_call
from .executor import local_exe
from .serdes import dump
from .serdes import load
# from .server import messenger
# from .server import server_runner
