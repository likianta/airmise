import aircontrol as air
from lk_logger import start_ipython

air.connect()
start_ipython({'air': air})

# pox -m aircontrol run-server
# pox test/timeout_waiting_for_pong.py
#   wait one minute to see if there is any warning message.
