# 心夏通讯

单机部署的轻量 IM：账号、邮箱验证码、好友、群聊、子账号（WSS）、公告、管理后台、浏览器推送。
只用 Python 标准库和 SQLite，没有 pip 依赖。

线上：`https://chat.akizukikokona.com`
代码在 `kokona_chat/`，入口 `run.py`。旧单文件 `chat_server.py` 保留但已停用。

## 跑起来

```bash
python3 run.py
```

默认 `127.0.0.1:8299`，前缀 `/chat`。子域挂根路径时把 `CHAT_BASE` 设为空：

```bash
CHAT_BASE="" CHAT_PORT=8298 CHAT_DATA_DIR=./data python3 run.py
```

首次启动会用 `CHAT_TOKEN`（默认 `sukikokona1212`）建管理员账号，用户名 `CHAT_ADMIN_USER`。

## 配置

全部走环境变量，`kokona_chat/config.py` 是唯一出口。

| 变量 | 默认 | 说明 |
|---|---|---|
| `CHAT_HOST` / `CHAT_PORT` | `127.0.0.1` / `8299` | 监听地址 |
| `CHAT_BASE` | `/chat` | 站点前缀，子域下设空串 |
| `CHAT_DATA_DIR` | `./data` | 数据库、头像、封面、图片、VAPID 密钥 |
| `CHAT_DB` | `<DATA_DIR>/chat.db` | SQLite 路径 |
| `CHAT_HISTORY` | `100` | 容量兜底值；实际按 `conversations.history_max`（默认 200 / 建群 300，可扩到 1000） |
| `CHAT_TOKEN` | `sukikokona1212` | 首次建管理员用的密码 |
| `CHAT_ADMIN_USER` | `akizukikokona` | 管理员用户名 |
| `CHAT_MAIL_FROM` / `CHAT_MAIL_NAME` | `noreply@…` / `心夏通讯` | 发件地址与显示名 |
| `CHAT_SMTP_HOST/PORT/USER/PASS/MODE` | 空 / `587` / … / `starttls` | 不配则验证码只显示在页面和后台 |
| `CHAT_SITE_URL` | `https://chat.akizukikokona.com` | 邮件页脚、图片地址、通知链接 |
| `CHAT_SLOGAN` | `轻量 · 安静 · 只聊天` | 邮件头部副标题 |
| `CHAT_PUSH_SUBJECT` | `mailto:admin@…` | VAPID 的 sub |
| `CHAT_SESSION_TTL` | 30 天 | 登录态有效期 |

## 结构

```
kokonachat/
├── run.py                 启动入口
├── kokona_chat/
│   ├── config.py          配置
│   ├── db.py              建表与迁移
│   ├── auth.py            PBKDF2、登录态、邮箱验证码
│   ├── mailer.py          发信（HTML 模板 + cid 内嵌图标）
│   ├── store.py           会话、消息、好友、表情、群角色
│   ├── hub.py             SSE / WS 广播
│   ├── push.py            VAPID + aes128gcm，自实现
│   ├── wskit.py           RFC6455 帧
│   ├── server.py          HTTP / API / SSE / WS
│   ├── pages.py           全部页面（内联 CSS/JS）
│   └── static/            icon.png、sw.js
└── data/                  运行期生成
```

## 接口

网页用 Cookie，程序用 `Authorization: Bearer`，WS 用 `?user=&pass=`。

```
POST /api/send_code                    发验证码
POST /api/register | /api/login        注册 / 登录
GET  /api/conversations                会话列表
POST /api/conversations/{id}/messages  发消息
POST /api/media                        上传图片（webp，sha1 去重）
POST /api/messages/{id}/recall         撤回
POST /api/messages/{id}/hide           本地删除
POST /api/stickers                     存表情
GET  /api/stream                       SSE
GET  /ws                               WebSocket
```

WS 协议见 `D:\Project-Kokona\wss重适配.md`。

## 部署

```bash
systemctl restart kokona-im     # 线上唯一服务，8298
nginx -t && systemctl reload nginx
```

`deploy/` 里是旧单文件服务的 unit 与 nginx 片段，仅作参考。

## 已知边界

- 单进程 + SQLite，不要开多实例写同一个 `data/`
- 云端每个会话只留最近 N 条，超出的直接删，没有归档
- 出站 25 被封，发信只能走 465/587 中继
- 推送依赖 `cryptography`，没装则接口降级为不支持
- iOS 要先「添加到主屏幕」才有 Push
