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
7. **图片不走外链**：前端用 canvas 裁好、导出 webp 再上传。
   - 头像：`POST /api/avatar`，256×256，存 `data/avatars/`，`users.avatar = av:<文件名>`
   - 封面：`POST /api/cover`，720×480，存 `data/covers/`，`users.cover = cv:<文件名>`
   渲染拼 `BASE + '/avatar|cover/' + 文件名`；没设时头像回退站点头像/名字首字，封面回退棕色渐变。
8. **子账号（WSS）没有独立用户名**：库里存隐藏名 `~sub:<id>`，对外一律用
   「主账号用户名 + 子账号密码」登录（`auth._match_sub`）。每个账号最多一个，
   只能改显示名和密码，不能改用户名。入口只在「设置 → WSS 账号」。
9. **PKN 会接管「只有自己」的 legacy 会话**（`store.get_or_create_pkn`），
   所以旧「频道一」就是账号的专属 WSS 聊天，不会再额外建一条导致列表出现两个。

## 界面结构（别改回去）

- `.app` 是 `grid`（桌面 340px + 1fr），`.main` 是纵向 flex。
- **`.chat-view` 必须是 `display:flex;flex-direction:column;flex:1;min-height:0`**。
  少了这条，`.msgs` 的 `flex:1` 不生效，消息少的时候输入框会被顶到屏幕中间。
- 移动端靠 `body.chat-open` / `body.panel-open` 切视图，`sidebar` 与 `main` 互斥显示；
  **不要再加底部 tabbar**——它挂在 sidebar 里，进面板时会被一起隐藏，回到列表就没入口了。
- 抽屉（`.drawer`）从左侧滑出，顶部是**可自定义封面**的个人卡片（默认棕色渐变），
  下面是「设置 / 通讯录 / 公告板 / 刷新 / 管理后台」。
- 「设置」页：封面/头像、显示名、WSS 账号、改密码、公告板、退出。
- 点好友 / 群成员 / 聊天标题 → 资料卡（`openUserCard`），样式与自己的卡片一致。
- 会话行的按压底色是 `.conv.press`，由 `pointerdown/up` 加删；**不要用 `:active`**，
  移动端会把按下状态黏在那一行，退出聊天后还是深色。
- 「当前打开的会话」高亮看 `S.openId`（`showList()` 里清空），**不要用 `S.cur`**——
  `S.cur` 退出后还留着给 SSE 用，拿它判高亮会导致退出后那行一直是选中色。
- 气泡上方的发送人名字只在**群聊/频道**里出现，而且必须在气泡**外面**（`.col > .b-meta` +
  `.bubble`）。私聊（`kind==='direct'`）和 WSS 那条（`kind==='pkn'`）都不显示名字，自己的消息也不显示。
- **消息时间只出现在居中的小条上**（`fmtSep` → 「今天 14:32」），气泡里不再挂时间角标。
  插入规则 `needSep()`：首条、跨天、**与上一条间隔 ≥5 分钟**才插一条。点气泡弹 toast 显示
  完整时间（`fmtFull`，读 `data-ts`）。
- 主色是**棕金**（`--brand:#9a6c3c`，取自头像图里的金色），不要改回绿色。


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

## 邮件模板

- `mailer._wrap()` 出 HTML，`send()` 组装成 `multipart/alternative`，HTML 那支再包一层
  `multipart/related` 挂图标。**图标走 cid 内嵌**（`cid:kokona-icon`，读
  `kokona_chat/static/icon.png`），不要改成外链 URL——多数客户端默认不加载远程图。
- 视觉：纯色米底 `#efe4d2` + 白色卡片 + 棕金头部 `#9a6c3c`，头部左侧图标、右侧
  产品名与 slogan；验证码是一块 `#f4e3c4` 的大字块。样式全内联，用 table 布局。
- 文案规矩：**称呼用「您」**；只写事实（用途、验证码、有效期、发送时间北京时间、
  站点地址），不写「感谢您的支持」「如有疑问请随时联系我们」这类客套。
- 可配项：`CHAT_MAIL_NAME`（产品名）、`CHAT_SLOGAN`（头部副标题）、
  `CHAT_SITE_URL`（页脚与隐藏预览里的站点地址）。

## 群头像

- 存在 `conversations.avatar`，值形如 `gv:<文件名>`，文件落 `data/groups/`，路由 `GET /gavatar/<名>`。
- **只有群创建者（`conversations.created_by`）能换**；接口 `POST /api/conversations/<cid>/avatar`
  对其他人返回 403「只有群主能换群头像」。群名仍然谁都能改（这是现状，别当 bug 改掉）。
- 前端统一用 `convAvatar(c, cls)` 渲染群头像，别再手写首字 div。

## 浏览器推送

- `kokona_chat/push.py`：自实现 VAPID(ES256) + aes128gcm，依赖 `cryptography`（服务器 3.3 已自带）。
  没装这个库时 `HAVE_CRYPTO=False`，接口自动降级、设置里的开关显示为不支持。
- VAPID 密钥首次用到时生成，存 `data/vapid.json`（600）。**别删**，删了所有人的订阅都会失效。
- `static/sw.js` 必须能从**站点根路径 `/sw.js`** 取到（scope 才是整站）；nginx 直接反代即可，
  服务端专门加 `Service-Worker-Allowed: /` 和 `no-cache`。
- 合并：同一用户同一会话 2 秒内的多条并成一条，正文变成 `[N条新消息]最新正文`。
- 通知内容：标题=会话名（私聊取备注/对方昵称），图标=对方头像或群头像，点击打开 `/?conv=<id>`。
- SW 行为：有**带焦点的窗口**时不弹（页面里已经能看见），`kokona-test` 例外，方便自测。
- 限制：iOS 必须先把站点「添加到主屏幕」才有 Push；桌面 Chrome/Edge/Firefox 正常。
- 权限引导：`maybeAskPush()` 在启动后 1.6s 跑一次（有公告气泡就先等它）。
  - **只问一次**：弹卡片说明「只用来推你收到的消息」，两个按钮「不再显示」/「请求权限」。
    点任一按钮都会写 `localStorage.kc_push_never=1`，之后永远不再弹，想开只能去设置页。
    只有点「请求权限」才调 `Notification.requestPermission()`。
  - **iOS 且非独立窗口**（`IS_IOS && !IS_STANDALONE`）弹另一套文案，要求先「添加到主屏幕」，
    这时不去请求权限（Safari 标签页里请求了也收不到）。
  - 已被拒绝（`denied`）不打扰，设置页那一行写着「点这里再请求一次权限」，点它会重新触发请求。

## 图片 / 撤回 / 群角色（2026-11-25）

- **图片消息**：`messages.kind='image'` + `media_id`；文件按 `sha1(webp)` 存在 `data/media/<hash>.webp`，
  路由 `GET /m/<hash>.webp` 带 `immutable` 长缓存，**同一张图全服只存一份**。
  上传走 `POST /api/media`（只收 webp，≤800KB），前端 canvas 最长边 1600、按体积降到 0.4~0.86 质量。
- **撤回**：`store.recall_message`。本人 5 分钟内；群主/群管理员对**本群任何人**不限时。
  撤回后 `recalled=1`、`body` 空、`media` 为 null，历史里只留占位；广播 `message_recalled`
  （PKN 连接收到 `pkn.message_recalled`）。
- **本地删除**：`msg_hidden(user_id, msg_id)`，`recent_messages` 带 viewer 时过滤，只影响自己。
- **群角色**在 `conversation_members.role`：`owner` / `admin` / `member`。
  **和 `users.role`（网站管理员）完全无关**，判断一律用 `store.member_role / can_edit_group / can_moderate`。
  - 群主：解散群、任免群管理员、改名字/头像/公告
  - 群管理员：改名字/头像/公告、撤成员消息（不限时）
  - 普通成员：只能退出
- **群公告**在 `conversations.notice`（≠ 网站公告），谁都能看，群主/群管理员能改。
- **容量**：`conversations.history_max`，建群时写死（网站管理员建 300，其他人 200），
  私聊与 PKN 固定 200；网站管理员可通过 `POST /api/conversations/<id>/history` 扩到 200/300/500/1000。
  `_trim()` 按会话各自的容量删，不要再回到全局 `config.HISTORY_MAX`。
- **表情包**：`stickers(user_id, media_id)`，普通用户上限 122，网站管理员不限；长按图片消息可存。
- **正在输入**：`POST /api/conversations/<id>/typing {active}` 或 WS `typing` / `pkn.typing`，
  只对 `direct` / `pkn` 转发，群聊丢弃；前端把标题换成「对方正在输入…」，4 秒后自动恢复，节流 1.5 秒。
- **缓存**：消息首屏缓存 `localStorage.kc_msgs_<conv>`（最近 60 条），先渲染再静默刷新；
  图片靠 `immutable` 头，头像 1 天。

## 已知限制


- **出站 25 被 VPS 上游封死**，自建 MTA 直投不可行。只能走 587/465 中继。
- 发信走 `smtp.yeah.net:465`（SSL，授权码当密码），配置在 `/opt/kokona-im/.env`（600）。
  **踩过的坑**：yeah.net 有「境外客户端登录」保护，服务器 IP 不在常用地会被拒成
  `535 authentication failed`——看着像授权码错了，实际是异地拦截。遇到 535 先让账号主人
  在邮箱设置里放行境外登录（或临时关闭保护），再重试；不要去反复改授权码。
- 主账号 `akizukikokona` 的 email 已设为 `akizukikokona@yeah.net`，否则「找回密码」对它无效。
- 未配 SMTP 时验证码显示在注册页 + `/admin`，对外开放注册前必须配好。
- 子域证书与主域共用一张（SAN 含 chat），由 certbot 续期；系统自带 certbot 1.12 太旧，
  新版在 `/opt/certbot-venv/bin/certbot`，续期请用它。
