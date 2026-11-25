# CONTEXT —— 派活前的速览

> 给接手的子代理/新会话看的。读完这份再动代码，别重复踩坑。

## 一句话

`kokona_chat` 是一个零第三方依赖（标准库 + SQLite）的轻量 IM：账号体系、邮箱验证、好友、群聊、
子账号（wss）、公告、管理后台。旧的单文件 `chat_server.py` 保留为「老 WS 客户端兼容服务」。

## 结构

```
kokonachat/
├── run.py                 启动入口
├── kokona_chat/
│   ├── config.py          全部配置（环境变量可覆盖）
│   ├── db.py              SQLite 建表 / 迁移
│   ├── auth.py            PBKDF2 密码、登录态、邮箱验证码
│   ├── mailer.py          发信（SMTP 可配，未配置则降级到页面/后台可见）
│   ├── store.py           会话 / 消息 / 好友 / 黑名单 / 公告
│   ├── hub.py             SSE + WebSocket 广播中心
│   ├── wskit.py           RFC6455 帧
│   ├── server.py          HTTP 路由 / API / SSE / WS
│   └── pages.py           全部页面（内联 CSS/JS，亮色，移动优先）
├── chat_server.py         旧版单文件（8299，老 WS 客户端专用）
└── data/chat.db           运行后生成
```

## 必须守住的规则

1. **云端每个会话只留最近 100 条**（`CHAT_HISTORY`）。插入时立即删旧的，别改成「查的时候才截」。
2. **私聊唯一**：`conversations.dm_key = "小id:大id"` + 唯一索引。别用「查成员集合」来判重。
3. **只能和好友私聊**；被拉黑 / 被封禁一律拒绝，返回中文原因。
4. **子账号（`is_sub=1`）** 只能和主账号聊，不能加好友 / 建群 / 建子账号。
5. **legacy 频道 1/2/3** 的 id 永远占位，只有管理员能进。
6. 主管理员 `akizukikokona` 不可被封禁。

## 鉴权与挂载

- 网页：`kc_session` Cookie；程序：`Authorization: Bearer` 或 WS 的 `?user=&pass=`。
- 首次启动会把 `CHAT_TOKEN`（默认 `sukikokona1212`）写成管理员密码。
- 页面注入的 `BASE` 来自 `X-Forwarded-Prefix`：
  - `akizukikokona.com/chat/` → nginx 传 `/chat`，`proxy_pass ...:8298/`
  - `chat.akizukikokona.com/` → nginx 传空，`proxy_pass ...:8298`
  改代码时**不要**把 `BASE` 写死。

## WS 分流（不能删）

`/etc/nginx/conf.d/chat-ws-split.conf`：

```
map $arg_token $chat_ws_backend { default 127.0.0.1:8299; "" 127.0.0.1:8298; }
```

带 `token` 参数的是旧的 DSH/QQ 桥接程序 → 老服务；不带的是新网页 → 新服务。

## 消息顺序

服务端 `id` 自增、`created_at` 单调；前端按 id 有序插入，重连后以服务端为准重建列表。
**不要**改回「先到先 append」。

## 部署

```bash
systemctl restart kokona-im     # 新服务 8298
systemctl restart kokona-chat   # 旧服务 8299（老 WS 客户端）
nginx -t && systemctl reload nginx
```

备份文件：`/etc/nginx/sites-available/akizukikokona.com.bak-*`

## 已知限制

- **出站 25 被 VPS 上游封死**，自建 MTA 直投不可行。只能走 587/465 中继。
- 未配 SMTP 时验证码显示在注册页 + `/admin`，对外开放注册前必须配好。
- `chat.akizukikokona.com` 尚未加 DNS；证书也不含该子域，需 DNS 生效后跑 certbot。
