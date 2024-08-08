# 服务器 - 网络应用 - 客户端结构

工作流程:

```
server: 启动, 创建两个 websocket 服务:
    2040/server (<public_ip>:2040/server)
    2040/webapp (<public_ip>:2040/webapp)
webapp: 启动

client: 打开 python aircontrol 客户端, 创建一个 ws 服务:
    2041/client (localhost:2041/client)
client: 打开网址, 访问网页应用
webapp: 初始化与三个 websocket 的连接:
    2040/server (<public_ip>:2040/server)
    2040/webapp (<public_ip>:2040/webapp)
    2041/client (localhost:2041/client)
    该操作由网页前端代码执行.

client: 点击某个按钮, 触发事件. 假设该事件是服务器向客户端获取客户机的数据.
webapp: 向 2040/webapp 发起请求
server: 收到请求, 将请求加入到消息队列
    由于 2040/webapp 与 2040/server 同属于一个进程, 它们之间的消息队列是共享的. 所以 
    2040/webapp 存入的消息, 可以被 2040/server 读取.
server: 2040/server 从消息队列中读取请求, 并转发到 2041/client.
    该操作由前端完成:
        <script>
        const ws_server = new WebSocket('ws://<public_ip>:2040/server');
        const ws_client = new WebSocket('ws://localhost:2041/client');
        ws_server.onmessage = (e) => { ws_client.send(e.data); }
        ws_client.onmessage = (e) => { ws_server.send(e.data); }
        </script>
client: 收到请求, 处理请求, 返回数据.
server: 2040/server 收到数据, 将数据加入到消息队列.
server: 2040/webapp 从消息队列中读取数据, 并返回给 webapp.
webapp: 收到数据, 更新页面.
```
