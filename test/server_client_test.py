import streamlit as st

from aircontrol import local_exe


def main() -> None:
    st.title('AirControl')
    if st.button('Get file tree from client computer'):
        files = local_exe.run(
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
    local_exe.open(True)
    main()
