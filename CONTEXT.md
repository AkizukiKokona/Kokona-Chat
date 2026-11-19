# CONTEXT —— 派活前的速览

> 给接手的子代理/新会话看的。读完这份再动代码，别重复踩坑。

## 一句话

单文件、零依赖的 A/B 双端聊天：WebSocket 连进来是「心夏」，浏览器打开是「秋月不会解梦」，支持多频道、消息落盘、Markdown 渲染。

## 结构

```
kokonachat/
├── chat_server.py      # 全部实现（~1200 行），HTTP + SSE + WebSocket + 存储 + 页面
├── deploy/
│   ├── kokona-chat.service
│   └── nginx-chat.conf
└── data/               # 运行期生成，不入库：ch-<id>.jsonl
```

`chat_server.py` 内部顺序：存储 `MessageStore` → `Channel` → 页面常量 `PAGE`/`LOGIN_PAGE` → `Handler`（GET/POST/SSE/WS）。

## 端点

| 路径 | 说明 |
|---|---|
| `GET /chat/`、`/chat/<id>/` | 页面，未登录给登录页 |
| `POST /chat/login` | token 换 cookie（HttpOnly，365 天） |
| `GET /chat/ws?token=&ch=` | WebSocket（A 端），JSON 或纯文本 |
| `GET /chat/stream?ch=` | SSE（B 端），首帧是 `event: meta` |
| `POST /chat/send?ch=` | 发消息 `{"text": "..."}` |
| `GET /chat/history?ch=` | 历史 |
| `GET/POST /chat/channels*` | 列表 / 新建 / 改名 / 清空 |
| `POST /chat/log` | 前端异常上报（免 token） |

鉴权：query `token`、`X-Token`、`Authorization: Bearer`、cookie 四选一。

## 部署（改完必须做）

```bash
cd D:/kokonachat && python -m py_compile chat_server.py
scp chat_server.py root@<host>:/opt/kokona-chat/
ssh root@<host> 'cd /opt/kokona-chat && python3 -m py_compile chat_server.py && systemctl restart kokona-chat'
```

nginx 反代在 `/etc/nginx/sites-available/akizukikokona.com` 的 `location /chat/`，**SSE 必须 `proxy_buffering off`**。

## 改前端时的铁律

1. **页面 JS 有两个 `<script>` 块**：第一个是 Markdown 渲染器，第二个是业务 IIFE。用正则替换时要区分，别只改第一个。
2. **接口一律写绝对路径 `/chat/xxx`**。曾经用相对路径，导致 `/chat/2/` 下请求变成 `/chat/2/channels` 全挂。
3. **UI 的关键行为不能依赖可选事件**。曾经把"是否滚动到底"绑在 SSE 的 `meta` 事件上，meta 一丢就永远不滚动，看起来像消息消失。现在用「350ms 静默」判定批次结束。
4. **HTML 先转义再渲染 Markdown**，链接只放行 `http(s)/mailto`。
5. 页面响应带 `no-store`，改完让用户刷新即可，不用强刷。

## 存储

每频道一个 `data/ch-<id>.jsonl`，一行一条。追加 + `fsync`，启动时从文件尾反向读最近 300 条进内存。超 4MB 自动压缩保留 2000 条。损坏行直接跳过。

## 本地验证技巧

- `curl -b <cookiejar>` 才拿得到真实页面，否则只有登录页
- 测 URL 参数必须用 `%2F` 编码 —— **Git Bash 会把 `/chat/2/` 转成 `C:/Program Files/.../chat/2/`**
- Edge headless 在用户开着浏览器时会静默失败（截图 0 字节），此时改用 `node --check` 验语法
- 提取页面 JS 做单测：`re.findall(r"<script>(.*?)</script>", src, re.S)` 取第 2 块，`node --check` + eval

## 已知边界

- 内存 300 条 / 磁盘更多，`/chat/history` 只回内存那批
- 单进程写锁，不支持多实例同时写
- 页面与接口都要 token，A 端用 `?token=`
