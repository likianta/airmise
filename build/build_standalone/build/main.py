import tree_shaking
from lk_utils import fs


def build_airclient_standalone() -> None:
    """
    if you have changed poetry.lock, rerun this function.
    """
    tree_shaking.build_module_graphs('build/tree_shaking.yaml')
    tree_shaking.dump_tree('build/tree_shaking.yaml')
    f = fs.zip_dir('airclient_standalone', overwrite=True)
    fs.make_link(f, 'C:/Likianta/workspace/dev.master.likianta/depsland/chore'
                    '/airclient_standalone.zip')
    print('next: cd <depsland_project> && dufs -p 2184')


if __name__ == '__main__':
    # pox build/main.py
    build_airclient_standalone()
