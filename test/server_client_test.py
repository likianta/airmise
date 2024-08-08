import streamlit as st
import streamlit.components.v1 as st_comps
from lk_utils import fs

from aircontrol import client_call


def main() -> None:
    st.title('AirControl')
    
    # st_comps.html(fs.load(fs.xpath('../aircontrol/frontend.html')), height=0)
    
    if st.button('Get file tree from client computer'):
        files = client_call(
            '''
            import os
            return os.listdir('aircontrol')
            '''
        )
        print(files, ':l')
        for x in files:
            st.text(x)


if __name__ == '__main__':
    # user: pox -m aircontrol run-client
    # server: strun 3001 test/server_client_test.py
    # user: visit http://localhost:3001
    main()
