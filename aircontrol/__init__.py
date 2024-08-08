if 1:
    import lk_logger
    lk_logger.setup(quiet=True)

if 2:
    import sys
    sys.path.append('third_libs')

from .client import Client
from .server import Server
# from .serdes import dump
# from .serdes import load
