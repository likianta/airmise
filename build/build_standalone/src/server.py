import airmise as air
import streamlit as st
import streamlit_canary as sc
from lk_utils import run_new_thread


@st.cache_resource
def _init_air_server():
    svr = air.Server(port=3002)
    run_new_thread(svr.run)
    return svr


state = sc.get_state(lambda: {
    'air_server': _init_air_server(),
    'client': None,
    'client_id': None,
})


def main():
    st.title('Depsland AirTest')
    
    # if st.button('Refresh'):
    #     st.rerun()
    
    print(st.context.url, st.query_params)
    #   e.g.
    #       http://localhost:3001
    #       http://localhost:3001/?id=55210
    if st.query_params:
        if state['client_id'] != st.query_params['id']:
            svr: air.Server = state['air_server']
            print(':vl', svr.connections)
            state['client_id'] = st.query_params['id']
            state['client'] = svr.connections[int(state['client_id'])]
            assert state['client'].active
    
    if state['client_id']:
        st.text('Client ID: {}'.format(state['client_id']))
        name = st.text_input('Input your name')
        if name:
            conn: air.Slave = state['client']
            msg = conn.call('hello', name)
            st.success('Here is a message from remote side: {}'.format(msg))
    else:
        sc.hint('No client found.')


if __name__ == '__main__':
    main()
