import pinkrain as pr

import aircontrol as air


def main():
    with pr.daisy.MainPage():
        with pr.html.Script() as item:
            session_id = item.id.plain.split('_')[1]
            client = air.WebClient(uid=session_id)
            item.text = client.front_script
        
        with pr.comp.Column():
            with pr.daisy.Button('Test') as btn:
                @btn.on_click
                def _():
                    data = client.run(
                        '''
                        from random import randint
                        memo alist := []
                        alist.append(randint(0, 0xFFFF))
                        return hex(alist[-1])
                        '''
                    )
                    print(data)
                    para.text = 'Got data: ' + data
            
            with pr.html.p() as para:
                para.text = 'Click the button to test the websocket connection.'


if __name__ == '__main__':
    # A: pox -m aircontrol run-web-server
    # A: pox test/webapp_test.py
    # B: pox -m aircontrol run-local-server
    # B: open http://<host_of_A>:<port_of_A>
    pr.app.run(main, host=air.get_local_ip_address(), debug=True)
