
## Prepare

### Dependencies

```sh
py -m lk_utils mklink <poetry_venv> build/venv
pip install -r requirements.lock -t deps/core  # optional
pip install -r requirements_extra.lock -t deps/extra
```

### Launcher and Icon

```sh
# 1. download icns file (follow `build/lancher/readme.md`)
# 2. convert icns to ico:
cd <depsland_project>
pox sidework/image_converter.py all <this_project>/build/launcher/airmagic.icns
# 3. convert bat to exe:
pox build/build.py bat-2-exe <this_project>/build/launcher/run.bat --show-console --icon <this_project>/build/launcher/airmagic.ico
```

## Make Distribution

```sh
cd <python_tree_shaking_project>
pox -m tree_shaking batch-dump-module-graphs <this_project>/build/modules.yaml
pox -m tree_shaking build-tree <this_project>/build/modules.yaml <this_project>/build/mini_deps
#   if you want to rebuild, remove `build/mini_deps` first.

cd <this_project>
# (optional) remove this symlink in case of recursion error:
rm build/mini_deps/aircontrol/build
# manually bump `pyproject.toml:[tool.poetry]:version`
pox build/build.py dist
```

## Test

```sh
cd dist/standalone/aircontrol-<version>
AirControl.exe
# server will start at http://localhost:2140
```

```sh
cd <this_project>
pox -m aircontrol run-client
```

```py
# entered ipython
run('print("hello world")')
```
