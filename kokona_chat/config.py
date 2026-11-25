"""kokona_chat —— 集中配置。全部可从环境变量覆盖，方便同一份代码在不同机器跑。"""

import os

# 包根目录：.../kokonachat/kokona_chat/ -> .../kokonachat
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

HOST = os.environ.get("CHAT_HOST", "127.0.0.1")
PORT = int(os.environ.get("CHAT_PORT", "8299"))

DATA_DIR = os.environ.get("CHAT_DATA_DIR", os.path.join(ROOT, "data"))
DB_PATH = os.environ.get("CHAT_DB", os.path.join(DATA_DIR, "chat.db"))

# 站点前缀：所有页面/接口都挂在这个前缀下（nginx 反代 /chat/）
BASE = os.environ.get("CHAT_BASE", "/chat").rstrip("/") or ""

# 云端每个会话只保留最近 100 条
HISTORY_MAX = int(os.environ.get("CHAT_HISTORY", "100"))

# 老版本兼容：历史上用同一个 token 直接登录；正式版把它迁移成管理员密码
LEGACY_TOKEN = os.environ.get("CHAT_TOKEN", "sukikokona1212")
ADMIN_USERNAME = os.environ.get("CHAT_ADMIN_USER", "akizukikokona")

# 邮件
MAIL_FROM = os.environ.get("CHAT_MAIL_FROM", "noreply@akizukikokona.com")
MAIL_NAME = os.environ.get("CHAT_MAIL_NAME", "心夏 Chat")
# 邮件头部那行副标题，也是站点顺手用的 slogan
SLOGAN = os.environ.get("CHAT_SLOGAN", "轻量 · 安静 · 只聊天")
# 邮件页脚、找回入口等处引用的站点地址（不带末尾斜杠）
SITE_URL = os.environ.get("CHAT_SITE_URL", "https://chat.akizukikokona.com").rstrip("/")
# Web Push：VAPID 的 sub 字段，一般填站长邮箱
PUSH_SUBJECT = os.environ.get("CHAT_PUSH_SUBJECT", "mailto:admin@akizukikokona.com")
SMTP_HOST = os.environ.get("CHAT_SMTP_HOST", "")
SMTP_PORT = int(os.environ.get("CHAT_SMTP_PORT", "587"))
SMTP_USER = os.environ.get("CHAT_SMTP_USER", "")
SMTP_PASS = os.environ.get("CHAT_SMTP_PASS", "")
# starttls / ssl / none
SMTP_MODE = os.environ.get("CHAT_SMTP_MODE", "starttls")

# 验证码
CODE_TTL = int(os.environ.get("CHAT_CODE_TTL", str(10 * 60)))       # 10 分钟有效
CODE_COOLDOWN = int(os.environ.get("CHAT_CODE_COOLDOWN", "60"))     # 同邮箱 60s 一次

# 登录态
SESSION_TTL = int(os.environ.get("CHAT_SESSION_TTL", str(30 * 24 * 3600)))  # 30 天
SESSION_COOKIE = "kc_session"

# 保留的旧频道 id（1/2/3），只有管理员及其子账号能连
LEGACY_CHANNELS = ("1", "2", "3")
