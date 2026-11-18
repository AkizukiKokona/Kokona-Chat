# Kokona Chat

> WebSocket 连进来就是 A，浏览器打开就是 B。

一个单文件、零依赖的双端聊天服务。给「另一端是程序、这一端是人」的场景用：Agent 用 WebSocket 说话，人用浏览器看和回。

线上地址：`https://akizukikokona.com/chat/`

---

## 为什么是这个形态

现成的聊天 UI 都太重了 —— 要登录、要建房间、要数据库、要撤回编辑已读。这里只需要「一条管道」：

- **不需要注册**：一个共享 token 就够，页面登录一次就记住
- **不需要社交功能**：没有撤回、删除、编辑、已读、引用
- **消息落盘但不建库**：每频道一个追加日志，重启不丢

代价是它不适合多人、不适合做检索。就这样。

---

## 消息怎么存

没有用 SQLite。这个数据只有两种访问：**按时间追加**、**读最近 N 条**，用不上关系查询和索引。所以用的是日志结构：

```
data/
├── ch-1.jsonl      # 频道 1 的消息，一行一条 JSON
└── ch-2.jsonl
```

- **写**：追加一行 + `flush` + `fsync`，写完再广播给对端，发出去的一定留得住
- **读**：启动时从文件尾部反向读最后 `CHAT_HISTORY` 条进内存，不整文件载入
- **崩溃**：最多坏最后一行，读取时自动跳过（不用修数据）
- **压缩**：单个文件超过 4MB 时重写只保留最近 2000 条，自动做，不用管
- **隔离**：频道 = 文件，以后上多用户只是再多几个文件

内存里仍是 300 条环形缓冲，磁盘保留更多；真要换引擎（SQLite / LMDB / PG），只需要替换 `MessageStore` 这一个类。

想直接看数据：

```bash
tail -f /opt/kokona-chat/data/ch-1.jsonl
```

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

默认监听 `127.0.0.1:8299`，然后用浏览器打开 `http://127.0.0.1:8299/chat/`，首次会要求输入 token（默认 `sukikokona1212`），登录一次后记在 cookie 里，一年内不用再输。

也可以直接把 token 拼在地址上，服务端会种好 cookie 再跳回干净 URL：

```
http://127.0.0.1:8299/chat/?token=sukikokona1212
```

环境变量：

| 变量 | 默认 | 说明 |
|---|---|---|
| `CHAT_TOKEN` | `sukikokona1212` | 接口与 WS 的鉴权 token |
| `CHAT_PORT` | `8299` | 监听端口（只绑 127.0.0.1，靠反代对外） |
| `CHAT_HISTORY` | `300` | 每频道在内存里保留的条数（磁盘保留更多） |
| `CHAT_CHANNELS_FILE` | `/opt/kokona-chat/channels.json` | 频道元数据落盘位置 |
| `CHAT_DATA_DIR` | `/opt/kokona-chat/data` | 消息日志目录 |
| `CHAT_FSYNC` | `1` | 每条消息 `fsync`；设 `0` 只 flush，更快但断电可能丢最后几条 |

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
GET  /chat/                          页面（频道 1，未登录给登录页）
GET  /chat/<id>/                     页面（指定频道）
POST /chat/login                     token 换 cookie（表单）
GET  /chat/ws?token=&ch=<id>         WebSocket（A 端）
GET  /chat/stream?token=&ch=<id>     SSE（B 端）
POST /chat/send?token=&ch=<id>       发消息 {"text": "..."}
GET  /chat/history?token=&ch=<id>    历史
GET  /chat/channels?token=           频道列表（含在线数）
POST /chat/channels/new?token=       新建频道
POST /chat/channels/rename?token=&ch=&{"name":"..."}   改名
POST /chat/channels/clear?token=&ch=<id>                清空该频道消息（内存 + 磁盘）
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
├── deploy/
│   ├── kokona-chat.service  # systemd unit
│   └── nginx-chat.conf      # 反代片段（含 upgrade map）
└── data/                    # 运行期生成：每频道一个 ch-*.jsonl（不入库）
```

`chat_server.py` 内部就五块：

1. **存储** — `MessageStore` 追加日志，尾部读、自动压缩
2. **频道** — `Channel` 对象持有连接列表与内存环形缓冲
3. **广播** — 按发送方决定投递给哪一侧
4. **HTTP/SSE** — `BaseHTTPRequestHandler` 子类
5. **WebSocket** — 手写 RFC 6455 握手与帧解析（文本/二进制/分片/ping-pong/close）

不用任何第三方库，是因为这个服务的全部价值就是「轻」：拷一个文件、起一个进程，没有依赖可以坏。

---

## 已知边界

- 内存只保留最近 300 条（磁盘更多，但 `/chat/history` 目前只回内存那批）
- 页面与接口都需要 token：页面登录后靠 cookie（HttpOnly、一年有效），A 端仍用 `?token=`
- 单进程持有写锁，不支持多实例同时写同一份 data 目录
- WebSocket 帧上限 1MB，单条消息上限 4000 字符
