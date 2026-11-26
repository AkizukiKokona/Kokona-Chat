"""密码哈希、登录态、邮箱验证码。全部用标准库。"""

import hashlib
import hmac
import secrets

from . import config, db

PBKDF2_ITER = 120_000


def hash_password(password):
    salt = secrets.token_bytes(16)
    dk = hashlib.pbkdf2_hmac("sha256", str(password).encode("utf-8"), salt, PBKDF2_ITER)
    return "pbkdf2$%d$%s$%s" % (PBKDF2_ITER, salt.hex(), dk.hex())


def verify_password(password, stored):
    try:
        algo, iters, salt_hex, hash_hex = str(stored).split("$")
        if algo != "pbkdf2":
            return False
        dk = hashlib.pbkdf2_hmac(
            "sha256", str(password).encode("utf-8"), bytes.fromhex(salt_hex), int(iters)
        )
        return hmac.compare_digest(dk.hex(), hash_hex)
    except Exception:
        return False


# ---------------- 登录态 ----------------

def create_session(user_id):
    token = secrets.token_hex(32)
    t = db.now()
    db.run(
        "INSERT INTO sessions (token, user_id, created_at, expires_at) VALUES (?, ?, ?, ?)",
        (token, user_id, t, t + config.SESSION_TTL),
    )
    return token


def user_by_session(token):
    if not token:
        return None
    return db.qone(
        "SELECT u.* FROM sessions s JOIN users u ON u.id = s.user_id "
        "WHERE s.token = ? AND s.expires_at > ?",
        (token, db.now()),
    )


def destroy_session(token):
    if token:
        db.run("DELETE FROM sessions WHERE token = ?", (token,))


# ---------------- 用户 ----------------

def find_by_username(username):
    return db.qone("SELECT * FROM users WHERE username = ?", (str(username or "").strip(),))


def find_by_email(email):
    e = str(email or "").strip().lower()
    if not e:
        return None
    return db.qone("SELECT * FROM users WHERE lower(email) = ?", (e,))


def create_user(username, password, email=None, role="user", is_sub=0, parent_id=None, display_name=""):
    username = str(username).strip()
    if email:
        email = str(email).strip().lower()
    cur = db.run(
        "INSERT INTO users (username, display_name, password_hash, email, role, is_sub, parent_id, created_at) "
        "VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
        (username, display_name or username, hash_password(password), email, role, int(is_sub), parent_id, db.now()),
    )
    return cur.lastrowid


def authenticate(username, password, allow_sub=True):
    """返回 (user_row, error)。error 是给用户看的中文说明。

    WSS 子账号不再有自己的用户名：用「主账号用户名 + 子账号密码」登录。
    所以主账号密码不对时，再拿同一串密码去比对该账号名下的子账号。

    allow_sub=False 时**不接受子账号**：HTTP 登录只能用主账号，
    子账号只允许走 WSS 专有协议（这是它唯一的入口）。
    """
    row = find_by_username(username)
    if row is not None:
        if row["status"] == "banned":
            return None, "这个账号已被封禁"
        if verify_password(password, row["password_hash"]):
            return row, ""
        # 子账号走同一个用户名
        if allow_sub:
            sub = _match_sub(row["id"], password)
            if sub is not None:
                return sub, ""
        return None, "账号或密码不正确"

    # 也允许用邮箱登录
    row = find_by_email(username)
    if row is None:
        return None, "账号或密码不正确"
    if row["status"] == "banned":
        return None, "这个账号已被封禁"
    if not verify_password(password, row["password_hash"]):
        if allow_sub:
            sub = _match_sub(row["id"], password)
            if sub is not None:
                return sub, ""
        return None, "账号或密码不正确"
    return row, ""


def _match_sub(owner_id, password):
    """在主账号名下的子账号里找一个密码匹配的。"""
    if not password or owner_id is None:
        return None
    for row in db.qall(
        "SELECT * FROM users WHERE parent_id = ? AND is_sub = 1 ORDER BY id",
        (int(owner_id),),
    ):
        if row["status"] != "banned" and verify_password(password, row["password_hash"]):
            return row
    return None


# ---------------- 邮箱验证码 ----------------

def issue_code(email, purpose):
    """返回 (code, retry_after)。retry_after > 0 表示还在冷却，别发。"""
    email = str(email or "").strip().lower()
    last = db.qone(
        "SELECT created_at FROM email_codes WHERE email = ? AND purpose = ? ORDER BY id DESC LIMIT 1",
        (email, purpose),
    )
    if last is not None:
        wait = config.CODE_COOLDOWN - (db.now() - last["created_at"])
        if wait > 0:
            return None, wait
    code = "%06d" % secrets.randbelow(1000000)
    t = db.now()
    db.run(
        "INSERT INTO email_codes (email, code, purpose, created_at, expires_at) VALUES (?, ?, ?, ?, ?)",
        (email, code, purpose, t, t + config.CODE_TTL),
    )
    return code, 0


def verify_code(email, purpose, code):
    email = str(email or "").strip().lower()
    row = db.qone(
        "SELECT * FROM email_codes WHERE email = ? AND purpose = ? AND used = 0 AND expires_at > ? "
        "ORDER BY id DESC LIMIT 1",
        (email, purpose, db.now()),
    )
    if row is None:
        return False
    if not hmac.compare_digest(str(row["code"]), str(code or "").strip()):
        return False
    db.run("UPDATE email_codes SET used = 1 WHERE id = ?", (row["id"],))
    return True


def latest_code(email, purpose):
    """仅用于未配置 SMTP 时的降级显示（管理后台/日志）。"""
    return db.qone(
        "SELECT code, created_at FROM email_codes WHERE email = ? AND purpose = ? AND used = 0 "
        "ORDER BY id DESC LIMIT 1",
        (str(email or "").strip().lower(), purpose),
    )
