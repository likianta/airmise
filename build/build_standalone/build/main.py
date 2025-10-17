import sys
from argsense import cli
from lk_utils import fs


@cli
def init_project():
    if not fs.exist('build/.venv'):
        print(sys.exec_prefix)
        site_dir = '{}/Lib/site-packages'.format(
            sys.exec_prefix.replace('\\', '/')
        )
        fs.make_link(site_dir, 'build/.venv')
        
    dir_i = 'C:/Likianta/workspace/dev.master.likianta'
    if not fs.exist('lib'):
        fs.make_dir('lib')
    for k, v in {
        f'{dir_i}/python-tree-shaking/tree_shaking': 'lib/tree_shaking',
    }.items():
        if not fs.exist(v):
            fs.make_link(k, v)


@cli
def build_airclient_standalone() -> None:
    """
    if you have changed poetry.lock, rerun this function.
    """
    import tree_shaking
    tree_shaking.build_module_graphs('build/tree_shaking.yaml')
    tree_shaking.dump_tree('build/tree_shaking.yaml')
    f = fs.zip_dir('airclient_standalone', overwrite=True)
    fs.make_link(f, 'C:/Likianta/workspace/dev.master.likianta/depsland/chore'
                    '/airclient_standalone.zip')
    print('next: cd <depsland_project> && dufs -p 2184')


if __name__ == '__main__':
    # pox build/main.py -h
    # pox build/main.py init_project
    cli.run()
