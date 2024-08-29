# WebApp 工作模型

```
user - local server: http://localhost:2141/<uid>
user - browser - user client: ws://localhost:2141/<uid>
user - browser - web front client: ws://<web_host>:2141/frontend/<uid>
web  - server: http://<web_host>:2141/frontend/<uid>
web  - server: http://<web_host>:2141/backend/<uid>
web  - backend - web back client: ws://<web_host>:2141/backend/<uid>
```
