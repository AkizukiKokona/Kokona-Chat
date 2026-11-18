# Kokona Chat

> WebSocket 连进来就是 A，浏览器打开就是 B。

一个单文件、零依赖的双端聊天服务。给「另一端是程序、这一端是人」的场景用：Agent 用 WebSocket 说话，人用浏览器看和回。

线上地址：`https://akizukikokona.com/chat/`

---

## 为什么是这个形态

现成的聊天 UI 都太重了 —— 要登录、要建房间、要数据库、要撤回编辑已读。这里只需要「一条管道」：

- **不需要登录**：页面打开即可用，接口靠 token 区分
- **不需要存储**：消息在内存里，300 条环形缓冲，重启即清
- **不需要社交功能**：没有撤回、删除、编辑、已读、引用

代价是它不适合多人、不适合留档。就这样。

---

## 两个角色

| 角色 | 显示名 | 接入方式 | 能力 |
|---|---|---|---|
| **A** | 心夏 | WebSocket `/chat/ws` | 收发纯 JSON，适合脚本 / Agent / 机器人 |
| **B** | 秋月不会解梦 | 浏览器打开 `/chat/` | SSE 收、POST 发，适合人 |

消息路由：A 发的只推给 B；B 发的推给 A，并回显给所有 B 标签页（多端同步）。

显示名写在页面 JS 顶部的 `NAME_A` / `NAME_B`（还有面板里用的简称 `SHORT_B`），改名字只改这三行。

---

## 快速开始

```bash
python3 chat_server.py
```

默认监听 `127.0.0.1:8299`，然后用浏览器打开 `http://127.0.0.1:8299/chat/`。

环境变量：

| 变量 | 默认 | 说明 |
|---|---|---|
| `CHAT_TOKEN` | `sukikokona1212` | 接口与 WS 的鉴权 token |
| `CHAT_PORT` | `8299` | 监听端口（只绑 127.0.0.1，靠反代对外） |
| `CHAT_HISTORY` | `300` | 每频道保留的消息条数 |
| `CHAT_CHANNELS_FILE` | `/opt/kokona-chat/channels.json` | 频道元数据落盘位置 |

---

## 频道

默认 `频道 1`（`/chat/`）和 `频道 2`（`/chat/2/`）。频道之间完全隔离：各自的连接、各自的历史。

- 页面右上角「频道 N ▾」按钮 → 切换 / 新建 / 改名
- 新建频道会直接给出它的 WS 地址，复制即可用
- 访问不存在的 `/chat/9/` 会自动创建

频道**名字**持久化在 `channels.json`，**消息**只在内存。

---

## 输入

输入框是能长高的 textarea：

- **Enter** 发送，**Shift + Enter** 换行（中文输入法选词时的回车不会误发）
- 内容变多时自动撑高，**最多五行**（132px），再多的部分在框内滚动
- 发送后自动回缩到一行并保持焦点，方便连续输入

## 接口

所有接口除页面本身外都需要 `token`（query、`X-Token` 头、`Authorization: Bearer` 三选一）。

```
GET  /chat/                          页面（频道 1）
GET  /chat/<id>/                     页面（指定频道）
GET  /chat/ws?token=&ch=<id>         WebSocket（A 端）
GET  /chat/stream?token=&ch=<id>     SSE（B 端）
POST /chat/send?token=&ch=<id>       发消息 {"text": "..."}
GET  /chat/history?token=&ch=<id>    历史
GET  /chat/channels?token=           频道列表（含在线数）
POST /chat/channels/new?token=       新建频道
POST /chat/channels/rename?token=&ch=&{"name":"..."}   改名
GET  /chat/health                    健康检查（无需 token）
```

### A 端最小示例

```js
const ws = new WebSocket('wss://akizukikokona.com/chat/ws?token=sukikokona1212&ch=1');
ws.onmessage = e => console.log(JSON.parse(e.data));   // {id, ch, from:"B", text, ts}
ws.send(JSON.stringify({ text: '在的' }));              // 也接受纯文本
```

```python
from websocket import create_connection
ws = create_connection("wss://akizukikokona.com/chat/ws?token=sukikokona1212")
print(ws.recv())
ws.send('{"text": "hello"}')
```

---

## 部署

线上跑在 Debian 11 + nginx 反代后面，systemd 托管。

```bash
# 1. 代码
install -d /opt/kokona-chat
install -m 755 chat_server.py /opt/kokona-chat/

# 2. 服务
install -m 644 deploy/kokona-chat.service /etc/systemd/system/
systemctl daemon-reload && systemctl enable --now kokona-chat

# 3. nginx（把 deploy/nginx-chat.conf 里的 location 加进站点）
nginx -t && systemctl reload nginx
```

nginx 那段有三个关键点：WebSocket 需要 `Upgrade`/`Connection` 头，SSE 必须 `proxy_buffering off`，长连接要放宽 `proxy_read_timeout`。

---

## 结构

```
kokonachat/
├── chat_server.py           # 全部逻辑，单文件零依赖
└── deploy/
    ├── kokona-chat.service  # systemd unit
    └── nginx-chat.conf      # 反代片段（含 upgrade map）
```

`chat_server.py` 内部就四块：

1. **频道** — `Channel` 对象持有连接列表与环形历史
2. **广播** — 按发送方决定投递给哪一侧
3. **HTTP/SSE** — `BaseHTTPRequestHandler` 子类
4. **WebSocket** — 手写 RFC 6455 握手与帧解析（文本/二进制/分片/ping-pong/close）

不用任何第三方库，是因为这个服务的全部价值就是「轻」：拷一个文件、起一个进程，没有依赖可以坏。

---

## 已知边界

- 消息不落盘，重启清空（要留档得加 SQLite）
- 页面免 token，知道 URL 即可当 B（要收紧可以改成必须 `?token=`）
- 单进程内存态，不支持多实例水平扩展
- WebSocket 帧上限 1MB，单条消息上限 4000 字符
