# from .server import app
#
# if __name__ == '__main__':
#     # pox -m aircontrol
#     app.run(
#         host='localhost',
#         port=2005,
#         auto_reload=True,
#         access_log=False,
#         # single_process=True,
#     )

from .server import Server

if __name__ == '__main__':
    # pox -m robyn -m aircontrol --dev
    Server().run(port=2005)
