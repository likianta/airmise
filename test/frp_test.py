import airmise as air
from argsense import cli

@cli
def start_server():
    air.frp.run_transceiver(port=2144)

@cli
def start_client(target_host, target_port=2144):
    air.frp.connect_to_public_transport(
        {'test': _greeting_test},
        source_port=2140,
        target_host=target_host,
        target_port=target_port,
    )

def _greeting_test(name):
    print(f'hello {name}')

if __name__ == '__main__':
    # pox test/frp_test.py start-server
    # pox test/frp_test.py start-client localhost
    cli.run()
