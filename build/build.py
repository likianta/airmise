from argsense import cli
from lk_utils import fs


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
    # pox build/build.py dist
    # main()
    cli.run()
