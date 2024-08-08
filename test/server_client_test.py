import streamlit as st

from aircontrol import client


def main() -> None:
    st.title('AirControl')
    if st.button('Get file tree from client computer'):
        files = client.run(
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
    client.open(True)
    main()
