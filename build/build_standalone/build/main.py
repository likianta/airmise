import re
import sys
from argsense import cli
from lk_utils import fs
from lk_utils import run_cmd_args


@cli
def init_project() -> None:
    if not fs.exist('build/.venv'):
        print(sys.exec_prefix)
        site_dir = '{}/Lib/site-packages'.format(
            sys.exec_prefix.replace('\\', '/')
        )
        fs.make_link(site_dir, 'build/.venv')
    
    if not fs.exist('build/client_config.yaml'):
        fs.dump(
            {'host': 'localhost', 'frontend_port': 3001, 'backend_port': 3002},
            'build/client_config.yaml'
        )
    
    dir_i = 'C:/Likianta/workspace/dev.master.likianta'
    if not fs.exist('lib'):
        fs.make_dir('lib')
    for k, v in {
        f'{dir_i}/python-tree-shaking/tree_shaking': 'lib/tree_shaking',
    }.items():
        if not fs.exist(v):
            fs.make_link(k, v)
    
    if not fs.exist('build/rcedit.exe'):
        print(
            'if you want to build app with custom icon, you need to download '
            '"rcedit.exe" and put it to "build/rcedit.exe".'
        )


@cli
def build_airclient_standalone() -> None:
    """
    note: if you have changed poetry.lock, rerun this function.
    """
    import tree_shaking
    tree_shaking.build_module_graphs('build/tree_shaking.yaml')
    tree_shaking.dump_tree('build/tree_shaking.yaml')
    fs.zip_dir('airclient_standalone', overwrite=True)
    print('next: dufs -p 2184')


@cli
def vcompile_client(
    app_name: str = 'AirClient',
    site: str = None,
    icon: str = None,
) -> None:
    """
    params:
        site (-s): `{host}:{port1},{port2}`, for example 'localhost:3001,3002'
            `port1` is frontend port, `port2` is backend port.
            if set site, will update `build/client_config.yaml`, which makes -
            vlang to compile client.v with embedding this info.
        icon (-i):
    """
    if site:
        host, port1, port2 = re.fullmatch(r'(.+):(\d+),(\d+)', site).groups()
        fs.dump(
            {
                'host': host,
                'frontend_port': int(port1),
                'backend_port': int(port2)
            },
            'build/client_config.yaml'
        )
    exe = f'dist/{app_name}.exe'
    run_cmd_args('v', '-o', exe, 'src/client.v')
    if icon:
        run_cmd_args(
            fs.xpath('rcedit.exe'), exe, '--set-icon', fs.abspath(icon)
        )


if __name__ == '__main__':
    # pox build/main.py -h
    # pox build/main.py init_project
    # pox build/main.py vcompile_client
    cli.run()
