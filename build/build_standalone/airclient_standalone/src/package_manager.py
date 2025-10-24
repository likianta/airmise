import typing as t
from lk_utils import fs


def add_package_to_venv(pkg_id: str, venv_dir):
    name, ver = pkg_id.split('-')
    root_i = 'resources/extracted/{}/{}'.format(name, ver)
    for d in fs.find_dirs(root_i):
        dir_o = '{}/{}'.format(venv_dir, d.relpath)
        if fs.exist(dir_o):
            for f in fs.findall_files(d.path):
                dir_o = '{}/{}'.format(venv_dir, fs.parent(f.relpath))
                file_o = '{}/{}'.format(dir_o, f.name)
                if fs.exist(dir_o):
                    fs.make_link(f.path, file_o, True)
                else:
                    fs.make_dirs(dir_o)
                    fs.make_link(f.path, file_o)
        else:
            fs.make_link(d.path, dir_o)
    for f in fs.find_files(root_i):
        fs.make_link(f.path, '{}/{}'.format(venv_dir, f.relpath), True)
    

def check_missing_packages(required: t.Iterable[str]):
    out = []
    for pkg_id in required:
        if not fs.exist('resources/downloads/{}.zip'.format(pkg_id)):
            out.append(pkg_id)
    return out


def download_packages(packages: t.Iterable[str]):
    for pkg_id in packages:
        url = 'http://localhost:2143/{}.zip'.format(pkg_id)
        file_o = 'resources/downloads/{}.zip'.format(pkg_id)
        fs.download(url, file_o)


def extract_packages(packages: t.Iterable[str]):
    for pkg_id in packages:
        file_i = 'resources/downloads/{}.zip'.format(pkg_id)
        dir0_o = 'resources/downloads/{}'.format(pkg_id.split('-')[0])
        dir1_o = 'resources/extracted/{}/{}'.format(*pkg_id.split('-'))
        if not fs.exist(dir0_o):
            fs.make_dir(dir0_o)
        if not fs.exist(dir1_o):
            fs.unzip_file(file_i, dir1_o, overwrite_top_name=True)


def list_local_packages():
    ...
