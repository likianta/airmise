from argsense import cli
from lk_utils import fs

from .poetry import poetry

abspath = lambda x: fs.xpath(x, True)


@cli.cmd()
def regenerate_bat_2_exe() -> None:
    poetry.run(
        'python', 'build/build.py', 'bat-2-exe', abspath('../launcher/run.bat'),
        '--show-console', '--icon', abspath('../launcher/airmagic.ico'),
        cwd='C:/Likianta/workspace/dev_master_likianta/depsland',
    )
    print(':t', '"build/launcher/run.exe" is regenerated')


@cli.cmd()
def dist() -> None:
    version = fs.load('pyproject.toml')['tool']['poetry']['version']
    print(version)
    
    dist_dir = 'dist/standalone/aircontrol-{}'.format(version)
    assert not fs.exists(dist_dir), dist_dir
    fs.make_dir(dist_dir)
    fs.make_dir(dist_dir + '/src')
    fs.make_dir(dist_dir + '/lib')
    
    fs.make_link(
        'build/python',
        '{}/python'.format(dist_dir)
    )
    fs.make_link(
        'build/mini_deps/aircontrol/aircontrol',
        '{}/aircontrol'.format(dist_dir)
    )
    # fs.make_link(
    #     'build/mini_deps/core',
    #     '{}/lib/core'.format(dist_dir)
    # )
    fs.make_link(
        'build/mini_deps/venv',
        '{}/lib/core_part1'.format(dist_dir)
    )
    fs.make_link(
        'build/mini_deps/_vendor',
        '{}/lib/core_part2'.format(dist_dir)
    )
    fs.make_link(
        'build/mini_deps/extra',
        '{}/lib/extra'.format(dist_dir)
    )
    # for x in os.listdir('build/mini_deps/_vendor'):
    #     fs.make_link(
    #         'build/mini_deps/_vendor/{}'.format(x),
    #         '{}/lib/core/{}'.format(dist_dir, x),
    #         overwrite=False
    #     )
    fs.copy_file(
        'build/launcher/run.exe',
        '{}/AirControl.exe'.format(dist_dir)
    )
    
    print('see result at "{}"'.format(dist_dir), ':v2t')


if __name__ == '__main__':
    # pox -m build.build_tool regenerate-bat-2-exe
    # pox -m build.build_tool dist
    #   before do this, you need to bump the version in pyproject.toml first.
    cli.run()
