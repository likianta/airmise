import airmise as air
import streamlit as st
import streamlit_canary as sc


@sc.init_state
class State:
    client = None
    numbers = []
    __version__ = 7


def main():
    if not State.client:
        State.client = air.Client().open()
        State.client.exec('from random import randint\nreturn None')
        _init_remote_env()

    if st.button('Refresh numbers'):
        State.numbers = State.client.exec(
            'return [randint(0, 100) for _ in range(10)]'
        )

    if State.numbers:
        st.write(f'Numbers: {State.numbers}')


def _init_remote_env() -> None:
    assert State.client
    State.client.exec(
        """
        import os
        import sys
        from lk_utils import fs
        from time import sleep

        def get_current_working_dir() -> str:
            return os.getcwd()
        
        def get_manifest_data(file: str) -> bytes:
            # transmit the raw data (bytes) to server.
            if not file:
                file = fs.here('source/.depsland/manifest.pkl')
            assert fs.exist(file), file
            return fs.load(file, 'binary')
        
        print('remote init done')
        return None
        """
    )


if __name__ == '__main__':
    # python -m airmise run_server
    # strun 3001 test/webapp_test.py

    # test schedule:
    #   1. edit State.__version__
    #   2. refresh gui
    #   3. see if error occurs

    main()
