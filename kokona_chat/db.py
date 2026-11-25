"""SQLite 数据层：建表、迁移、线程本地连接。"""

import os
import sqlite3
import threading
import time

from . import config

_local = threading.local()

SCHEMA = """
PRAGMA journal_mode=WAL;

CREATE TABLE IF NOT EXISTS users (
  id            INTEGER PRIMARY KEY AUTOINCREMENT,
  username      TEXT NOT NULL UNIQUE,
  display_name  TEXT NOT NULL DEFAULT '',
  password_hash TEXT NOT NULL,
  email         TEXT UNIQUE,
  role          TEXT NOT NULL DEFAULT 'user',       -- admin / user
  avatar        TEXT NOT NULL DEFAULT '',
  cover         TEXT NOT NULL DEFAULT '',            -- 资料卡封面，cv:<文件名>
  is_sub        INTEGER NOT NULL DEFAULT 0,         -- 1 = 子账号(wss)
  parent_id     INTEGER,                            -- 子账号归属的主账号
  status        TEXT NOT NULL DEFAULT 'active',     -- active / banned
  created_at    INTEGER NOT NULL
);

CREATE TABLE IF NOT EXISTS sessions (
  token      TEXT PRIMARY KEY,
  user_id    INTEGER NOT NULL,
  created_at INTEGER NOT NULL,
  expires_at INTEGER NOT NULL
);

CREATE TABLE IF NOT EXISTS conversations (
  id         INTEGER PRIMARY KEY AUTOINCREMENT,
  kind       TEXT NOT NULL,                          -- direct / group / legacy
  title      TEXT NOT NULL DEFAULT '',
  dm_key     TEXT,                                   -- direct 会话唯一键 "小id:大id"
  created_by INTEGER,
  avatar     TEXT NOT NULL DEFAULT '',               -- gv:<文件名>，群头像
  notice     TEXT NOT NULL DEFAULT '',               -- 群公告（≠ 网站公告）
  history_max INTEGER NOT NULL DEFAULT 0,            -- 云端留存条数，0 = 按默认规则
  created_at INTEGER NOT NULL,
  last_at    INTEGER NOT NULL DEFAULT 0              -- 方便按最近活跃排序
);

CREATE TABLE IF NOT EXISTS conversation_members (
  conv_id   INTEGER NOT NULL,
  user_id   INTEGER NOT NULL,
  alias     TEXT NOT NULL DEFAULT '',                -- 我对这个会话的备注
  role      TEXT NOT NULL DEFAULT 'member',          -- owner / admin / member（群内角色）
  joined_at INTEGER NOT NULL,
  PRIMARY KEY (conv_id, user_id)
);

CREATE TABLE IF NOT EXISTS messages (
  id         INTEGER PRIMARY KEY AUTOINCREMENT,
  conv_id    INTEGER NOT NULL,
  sender_id  INTEGER,
  body       TEXT NOT NULL,
  kind       TEXT NOT NULL DEFAULT 'text',           -- text / image
  media_id   INTEGER,
  recalled   INTEGER NOT NULL DEFAULT 0,
  recall_by  INTEGER,
  created_at INTEGER NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_messages_conv ON messages(conv_id, id);

CREATE TABLE IF NOT EXISTS friends (
  user_id    INTEGER NOT NULL,
  peer_id    INTEGER NOT NULL,
  created_at INTEGER NOT NULL,
  PRIMARY KEY (user_id, peer_id)
);

CREATE TABLE IF NOT EXISTS read_state (
  conv_id      INTEGER NOT NULL,
  user_id      INTEGER NOT NULL,
  last_read_id INTEGER NOT NULL DEFAULT 0,
  PRIMARY KEY (conv_id, user_id)
);

CREATE TABLE IF NOT EXISTS blocks (
  user_id    INTEGER NOT NULL,
  peer_id    INTEGER NOT NULL,
  created_at INTEGER NOT NULL,
  PRIMARY KEY (user_id, peer_id)
);

CREATE TABLE IF NOT EXISTS announcements (
  id         INTEGER PRIMARY KEY AUTOINCREMENT,
  author_id  INTEGER NOT NULL,
  title      TEXT NOT NULL DEFAULT '',
  body       TEXT NOT NULL,
  created_at INTEGER NOT NULL
);

CREATE TABLE IF NOT EXISTS announcement_reads (
  announcement_id INTEGER NOT NULL,
  user_id         INTEGER NOT NULL,
  read_at         INTEGER NOT NULL,
  PRIMARY KEY (announcement_id, user_id)
);

CREATE TABLE IF NOT EXISTS email_codes (
  id         INTEGER PRIMARY KEY AUTOINCREMENT,
  email      TEXT NOT NULL,
  code       TEXT NOT NULL,
  purpose    TEXT NOT NULL,                          -- register / reset_password / find_username
  created_at INTEGER NOT NULL,
  expires_at INTEGER NOT NULL,
  used       INTEGER NOT NULL DEFAULT 0
);
CREATE INDEX IF NOT EXISTS idx_codes_email ON email_codes(email, purpose, created_at);

CREATE TABLE IF NOT EXISTS media (
  id         INTEGER PRIMARY KEY AUTOINCREMENT,
  hash       TEXT NOT NULL UNIQUE,                   -- sha1(webp)，同图只存一份
  bytes      INTEGER NOT NULL,
  w          INTEGER NOT NULL DEFAULT 0,
  h          INTEGER NOT NULL DEFAULT 0,
  created_at INTEGER NOT NULL
);

CREATE TABLE IF NOT EXISTS stickers (
  id         INTEGER PRIMARY KEY AUTOINCREMENT,
  user_id    INTEGER NOT NULL,
  media_id   INTEGER NOT NULL,
  created_at INTEGER NOT NULL,
  UNIQUE(user_id, media_id)
);

-- 本地删除：只对这个人隐藏，别人照常看到
CREATE TABLE IF NOT EXISTS msg_hidden (
  user_id INTEGER NOT NULL,
  msg_id  INTEGER NOT NULL,
  PRIMARY KEY (user_id, msg_id)
);

CREATE TABLE IF NOT EXISTS push_subs (
  id         INTEGER PRIMARY KEY AUTOINCREMENT,
  user_id    INTEGER NOT NULL,
  endpoint   TEXT NOT NULL UNIQUE,
  p256dh     TEXT NOT NULL,
  auth       TEXT NOT NULL,
  created_at INTEGER NOT NULL
);

CREATE TABLE IF NOT EXISTS mail_log (
  id         INTEGER PRIMARY KEY AUTOINCREMENT,
  to_addr    TEXT NOT NULL,
  subject    TEXT NOT NULL,
  body       TEXT NOT NULL,
  status     TEXT NOT NULL,                          -- sent / queued / failed
  error      TEXT NOT NULL DEFAULT '',
  created_at INTEGER NOT NULL
);
"""


def now():
    return int(time.time())


def get_conn():
    """每个线程一个连接（ThreadingHTTPServer 是多线程的）。"""
    conn = getattr(_local, "conn", None)
    if conn is None:
        os.makedirs(os.path.dirname(config.DB_PATH), exist_ok=True)
        conn = sqlite3.connect(config.DB_PATH, timeout=15, check_same_thread=False)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys=ON")
        _local.conn = conn
    return conn


def q(sql, params=()):
    return get_conn().execute(sql, params)


def qall(sql, params=()):
    return get_conn().execute(sql, params).fetchall()


def qone(sql, params=()):
    return get_conn().execute(sql, params).fetchone()


def run(sql, params=()):
    conn = get_conn()
    cur = conn.execute(sql, params)
    conn.commit()
    return cur


def init_db():
    conn = get_conn()
    conn.executescript(SCHEMA)
    conn.commit()
    _migrate()
    _ensure_admin()
    _ensure_legacy_conversations()


def _migrate():
    """给老库补新列，幂等。"""
    cols = {row["name"] for row in qall("PRAGMA table_info(conversations)")}
    if "dm_key" not in cols:
        run("ALTER TABLE conversations ADD COLUMN dm_key TEXT")
    if "last_at" not in cols:
        run("ALTER TABLE conversations ADD COLUMN last_at INTEGER NOT NULL DEFAULT 0")
    if "avatar" not in cols:
        run("ALTER TABLE conversations ADD COLUMN avatar TEXT NOT NULL DEFAULT ''")
    if "notice" not in cols:
        run("ALTER TABLE conversations ADD COLUMN notice TEXT NOT NULL DEFAULT ''")
    if "history_max" not in cols:
        run("ALTER TABLE conversations ADD COLUMN history_max INTEGER NOT NULL DEFAULT 0")

    mcols = {row["name"] for row in qall("PRAGMA table_info(conversation_members)")}
    if "role" not in mcols:
        run("ALTER TABLE conversation_members ADD COLUMN role TEXT NOT NULL DEFAULT 'member'")

    gcols = {row["name"] for row in qall("PRAGMA table_info(messages)")}
    if "kind" not in gcols:
        run("ALTER TABLE messages ADD COLUMN kind TEXT NOT NULL DEFAULT 'text'")
        run("ALTER TABLE messages ADD COLUMN media_id INTEGER")
        run("ALTER TABLE messages ADD COLUMN recalled INTEGER NOT NULL DEFAULT 0")
        run("ALTER TABLE messages ADD COLUMN recall_by INTEGER")
    run(
        "CREATE UNIQUE INDEX IF NOT EXISTS idx_conv_dm "
        "ON conversations(dm_key) WHERE dm_key IS NOT NULL"
    )

    ucols = {row["name"] for row in qall("PRAGMA table_info(users)")}
    if "cover" not in ucols:
        run("ALTER TABLE users ADD COLUMN cover TEXT NOT NULL DEFAULT ''")

    # WSS 专属聊天统一叫「心夏」
    run("UPDATE conversations SET title = '心夏' WHERE kind = 'pkn' "
        "AND (title = '' OR title IN ('我的 WSS 聊天', '频道 1'))")
    run("UPDATE conversations SET history_max = 200 WHERE kind IN ('pkn', 'direct') AND history_max = 0")

    # 子账号不再单独占一个用户名：统一改成隐藏名 ~sub:<id>，
    # 对外只认「主账号用户名 + 子账号密码」。
    for row in qall("SELECT id, username, is_sub FROM users WHERE is_sub = 1"):
        if not str(row["username"]).startswith("~sub:"):
            run("UPDATE users SET username = ? WHERE id = ?", ("~sub:%d" % int(row["id"]), int(row["id"])))


def _ensure_admin():
    """把老的 token 迁移成管理员账号：用户名 akizukikokona，密码 = 老 token。"""
    from .auth import hash_password  # 延迟导入，避免循环

    row = qone("SELECT id FROM users WHERE role='admin' LIMIT 1")
    if row is not None:
        return
    exists = qone("SELECT id FROM users WHERE username=?", (config.ADMIN_USERNAME,))
    if exists is not None:
        return
    run(
        "INSERT INTO users (username, display_name, password_hash, email, role, created_at) "
        "VALUES (?, ?, ?, ?, 'admin', ?)",
        (config.ADMIN_USERNAME, "心夏", hash_password(config.LEGACY_TOKEN), None, now()),
    )


def _ensure_legacy_conversations():
    """老频道 1/2/3 继续占位，方便旧的 wss 客户端连回来。"""
    for cid in config.LEGACY_CHANNELS:
        row = qone("SELECT id FROM conversations WHERE id=?", (int(cid),))
        if row is None:
            run(
                "INSERT INTO conversations (id, kind, title, created_at) VALUES (?, 'legacy', ?, ?)",
                (int(cid), "频道 %s" % cid, now()),
            )
    admin = qone("SELECT id FROM users WHERE role='admin' LIMIT 1")
    if admin is not None:
        for cid in config.LEGACY_CHANNELS:
            run(
                "INSERT OR IGNORE INTO conversation_members (conv_id, user_id, joined_at) VALUES (?, ?, ?)",
                (int(cid), admin["id"], now()),
            )
