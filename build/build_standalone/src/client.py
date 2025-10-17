import airmise as air
import webbrowser
from argsense import cli


@cli
def main(host: str, frontend_port: int, backend_port: int) -> None:
    """
    params:
        frontend_port (-f):
        backend_port (-b):
            suggest using a bigger number (usually `frontend_port + 1`) as -
            backend port.
    """
    client = air.Client(host, backend_port)
    client.open()
    
    # url = 'http://{}:{}/?id={}'.format(host, frontend_port, client.id)
    # if os.name == 'nt':
    #     os.startfile(url)
    # else:
    #     raise NotImplementedError
    webbrowser.open('http://{}:{}/?id={}'.format(
        host, frontend_port, client.id
    ))
    
    client.master.set_passive({'hello': _greet})  # blocking


def _greet(name: str) -> str:
    print(name)
    return f'hello, {name}!'


if __name__ == '__main__':
    # doc: readme.zh.md
    # test in source:
    #   pox src/client.py localhost -f 3001 -b 3002
    # compile:
    #   por nuitka --standalone --onefile src/client.py
    cli.run(main)
