import streamlit as st
import streamlit.components.v1 as stv1

from aircontrol import webapp
from aircontrol.frontend import FRONTEND_TAG


def main() -> None:
    st.title('AirControl')
    stv1.html(FRONTEND_TAG, width=0, height=0)
    dirpath = st.text_input('Enter a directory path')
    if st.button('Get file tree from client computer'):
        files = webapp.run(
            '''
            import os
            return os.listdir(dirpath)
            ''',
            {'dirpath': dirpath}
        )
        print(files, ':l')
        for x in files:
            st.text(x)


if __name__ == '__main__':
    # user: pox -m aircontrol run-client
    # server: pox -m aircontrol run-server
    # server: strun 3001 test/server_client_test.py
    # user: visit http://localhost:3001
    webapp.open(True)
    main()
