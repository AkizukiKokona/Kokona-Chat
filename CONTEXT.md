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
  - `chat.akizukikokona.com/` → nginx 传空，`proxy_pass ...:8298`（**正式入口**）
  - `akizukikokona.com/chat/` → 已 301 跳子域
  改代码时**不要**把 `BASE` 写死。

## WS 入口（已统一）

`/ws` 只有一个上游：新服务 8298。旧的兼容分流已删除。

**正式地址**：`wss://chat.akizukikokona.com/ws`
（老的 `wss://akizukikokona.com/chat/ws` 会 301，WebSocket 不跟随，等于失效）

- 鉴权：`?user=用户名&pass=密码`（也认 Cookie / Bearer）
- 协议：客户端发 `{"action":"send","conv_id":N,"text":"..."}`，服务端推 `{"type":"message",...}`
- 旧协议（`?token=&ch=`）已废弃，插件已改，说明见 `D:\Project-Kokona\wss重适配.md`
- PKN 协议：`pkn.hello` 由服务端下发专属会话 id（`pkn.welcome`），之后 `pkn.send` 不用带 conv_id
- PKN 协议：`pkn.hello` 让服务端下发专属会话 id，见文档第五章

**频道分配**：conv 1 = 管理员默认聊天，conv 2 = DSH 插件，conv 3 = 备用。
旧服务 `kokona-chat.service`（8299）已停用，`/opt/kokona-chat/data/*.jsonl` 仅作归档。

## 消息顺序

服务端 `id` 自增、`created_at` 单调；前端按 id 有序插入，重连后以服务端为准重建列表。
**不要**改回「先到先 append」。

## 部署

```bash
systemctl restart kokona-im     # 唯一在跑的服务 8298
nginx -t && systemctl reload nginx
```

备份文件：`/etc/nginx/sites-available/akizukikokona.com.bak-*`

## 已知限制

- **出站 25 被 VPS 上游封死**，自建 MTA 直投不可行。只能走 587/465 中继。
- 未配 SMTP 时验证码显示在注册页 + `/admin`，对外开放注册前必须配好。
- 子域证书与主域共用一张（SAN 含 chat），由 certbot 续期；系统自带 certbot 1.12 太旧，
  新版在 `/opt/certbot-venv/bin/certbot`，续期请用它。
