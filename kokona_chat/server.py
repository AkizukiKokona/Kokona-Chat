"""kokona_chat 的 HTTP 层：页面、JSON API、SSE、WebSocket。

零第三方依赖，只用标准库。设计目标是能在低配单核 VPS 上跑住。
"""

import base64
import hashlib
import json
import os
import re
import secrets
import time
import traceback
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import parse_qs, unquote, urlparse

from . import auth, config, db, hub, mailer, pages, push, store, wskit

HUB = hub.Hub()

STATIC_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "static")
# 用户头像单独放数据目录，跟只读的代码目录分开
AVATAR_DIR = os.path.join(config.DATA_DIR, "avatars")
COVER_DIR = os.path.join(config.DATA_DIR, "covers")
GROUP_DIR = os.path.join(config.DATA_DIR, "groups")
MEDIA_DIR = os.path.join(config.DATA_DIR, "media")
DIAG_DIR = os.path.join(config.DATA_DIR, "diag")
MAX_MEDIA_BYTES = 800 * 1024
HISTORY_CHOICES = (200, 300, 500, 1000)
MAX_AVATAR_BYTES = 400 * 1024
MAX_COVER_BYTES = 900 * 1024
STATIC_MIME = {
    ".png": "image/png",
    ".ico": "image/x-icon",
    ".svg": "image/svg+xml",
    ".jpg": "image/jpeg",
    ".jpeg": "image/jpeg",
    ".webp": "image/webp",
    ".css": "text/css; charset=utf-8",
    ".js": "application/javascript; charset=utf-8",
}

# 路由：<id> / <name> 这种占位符转成命名组
_ROUTES = []


def route(method, pattern):
    def deco(fn):
        regex = re.compile("^" + re.sub(r"<(\w+)>", r"(?P<\1>[^/]+)", pattern) + "$")
        _ROUTES.append((method, regex, fn))
        return fn
    return deco


def ok(**kw):
    body = {"ok": True}
    body.update(kw)
    return 200, body


def err(message, code=400):
    return code, {"ok": False, "error": message}


class ApiError(Exception):
    def __init__(self, message, code=400):
        super().__init__(message)
        self.message = message
        self.code = code


# ==================================================================== 上下文

class Ctx:
    """一次请求的上下文：带当前登录用户和解析好的参数。"""

    def __init__(self, handler, user, path, query, body, params):
        self.h = handler
        self.user = user
        self.path = path
        self.query = query
        self.body = body
        self.params = params

    def need_login(self):
        if self.user is None:
            raise ApiError("请先登录", 401)
        return self.user

    def need_admin(self):
        user = self.need_login()
        if not store.is_admin(user):
            raise ApiError("需要管理员权限", 403)
        return user

    def arg(self, name, default=""):
        v = self.body.get(name, default)
        return v if v is not None else default

    def q(self, name, default=""):
        return self.query.get(name, [default])[0]

    def push(self, user_ids, payload):
        HUB.push_conversation(user_ids, payload)

    def notify_conv(self, conv_id, payload):
        HUB.push_conversation(store.member_ids(conv_id), payload)


# ==================================================================== 用户

@route("POST", "/api/login")
def api_login(c):
    username = str(c.arg("username")).strip()
    password = str(c.arg("password"))
    if not username or not password:
        raise ApiError("请输入账号和密码")
    user, msg = auth.authenticate(username, password)
    if user is None:
        raise ApiError(msg or "登录失败", 401)
    token = auth.create_session(user["id"])
    c.h.set_cookie(token)
    return ok(user=store.user_brief(user), token=token)


@route("POST", "/api/logout")
def api_logout(c):
    token = c.h.session_token()
    auth.destroy_session(token)
    c.h.clear_cookie()
    return ok()


@route("GET", "/api/me")
def api_me(c):
    user = c.need_login()
    return ok(user=_full_user(c, user), unread_announcements=store.unread_announcements(user["id"]))


def _full_user(c, user):
    data = store.user_brief(user)
    data["email"] = user["email"] or ""
    data["parent_id"] = user["parent_id"]
    data["is_admin"] = store.is_admin(user)
    data["legacy_channels"] = list(config.LEGACY_CHANNELS) if store.is_admin(user) else []
    return data


@route("POST", "/api/profile")
def api_profile(c):
    user = c.need_login()
    display = str(c.arg("display_name", user["display_name"]) or "").strip()[:30]
    if not display:
        raise ApiError("显示名不能为空")
    avatar = str(c.arg("avatar", user["avatar"]) or "")[:200]
    if avatar and not (avatar.startswith("av:") and "/" not in avatar[3:] and ".." not in avatar) \
            and not re.match(r"^https?://", avatar):
        raise ApiError("头像地址不合法")
    db.run("UPDATE users SET display_name = ?, avatar = ? WHERE id = ?", (display, avatar, user["id"]))
    if avatar == "":
        _drop_upload_file(str(user["avatar"] or ""), AVATAR_DIR)
    fresh = db.qone("SELECT * FROM users WHERE id = ?", (user["id"],))
    return ok(user=_full_user(c, fresh))


def _drop_upload_file(stored, folder=AVATAR_DIR):
    """删掉被替换下来的图片，别把磁盘堆满。"""
    for prefix in ("av:", "cv:", "gv:"):
        if stored.startswith(prefix):
            name = stored[len(prefix):]
            if name == "" or "/" in name or ".." in name:
                return
            try:
                os.remove(os.path.join(folder, name))
            except OSError:
                pass
            return


def _save_upload(raw, user_id, kind):
    """解析 data URL → 校验 → 落盘 → 返回 "av:<文件名>" / "cv:<文件名>""。"""
    hit = re.match(r"^data:image/(webp|png);base64,(.+)$", str(raw or ""), re.S)
    if not hit:
        raise ApiError("只接受 webp / png 图片")
    fmt, blob = hit.group(1), hit.group(2)
    try:
        data = base64.b64decode(blob, validate=True)
    except Exception:
        raise ApiError("图片数据损坏")

    is_avatar = kind in ("avatar", "group")
    limit = MAX_AVATAR_BYTES if is_avatar else MAX_COVER_BYTES
    if len(data) < 64:
        raise ApiError("图片太小")
    if len(data) > limit:
        raise ApiError("图片太大（上限 %dKB）" % (limit // 1024))
    if fmt == "webp" and (data[:4] != b"RIFF" or data[8:12] != b"WEBP"):
        raise ApiError("不是有效的 webp")
    if fmt == "png" and data[:8] != b"\x89PNG\r\n\x1a\n":
        raise ApiError("不是有效的 png")

    folder = {"avatar": AVATAR_DIR, "cover": COVER_DIR, "group": GROUP_DIR}[kind]
    tag = {"avatar": "av:", "cover": "cv:", "group": "gv:"}[kind]
    stem = {"avatar": "u", "cover": "b", "group": "g"}[kind]
    os.makedirs(folder, exist_ok=True)
    name = "%s%d-%s.%s" % (stem, int(user_id), secrets.token_hex(5), fmt)
    with open(os.path.join(folder, name), "wb") as fh:
        fh.write(data)
    return tag + name


@route("POST", "/api/avatar")
def api_avatar(c):
    """接收前端裁好的方图（尽量 webp），落盘后把头像指过去。"""
    user = c.need_login()
    stored = _save_upload(c.arg("data"), user["id"], "avatar")
    old = str(user["avatar"] or "")
    db.run("UPDATE users SET avatar = ? WHERE id = ?", (stored, user["id"]))
    if old != stored:
        _drop_upload_file(old, AVATAR_DIR)
    fresh = db.qone("SELECT * FROM users WHERE id = ?", (user["id"],))
    return ok(user=_full_user(c, fresh), url=stored)


@route("POST", "/api/cover")
def api_cover(c):
    """资料卡封面：比头像宽，默认 3:2 左右。"""
    user = c.need_login()
    data = c.arg("data")
    if not data:
        # 传空 = 恢复默认渐变
        old = str(user["cover"] or "")
        db.run("UPDATE users SET cover = '' WHERE id = ?", (user["id"],))
        _drop_upload_file(old, COVER_DIR)
    else:
        stored = _save_upload(data, user["id"], "cover")
        old = str(user["cover"] or "")
        db.run("UPDATE users SET cover = ? WHERE id = ?", (stored, user["id"]))
        if old != stored:
            _drop_upload_file(old, COVER_DIR)
    fresh = db.qone("SELECT * FROM users WHERE id = ?", (user["id"],))
    return ok(user=_full_user(c, fresh))


@route("POST", "/api/password")
def api_password(c):
    user = c.need_login()
    old = str(c.arg("old_password"))
    new = str(c.arg("new_password"))
    if not auth.verify_password(old, user["password_hash"]):
        raise ApiError("原密码不正确")
    if len(new) < 6:
        raise ApiError("新密码至少 6 位")
    db.run("UPDATE users SET password_hash = ? WHERE id = ?", (auth.hash_password(new), user["id"]))
    return ok()


# ==================================================================== 注册 / 找回

@route("POST", "/api/send_code")
def api_send_code(c):
    email = str(c.arg("email")).strip().lower()
    purpose = str(c.arg("purpose") or "register")
    if purpose not in ("register", "reset_password", "find_username"):
        raise ApiError("未知的验证类型")
    if not re.match(r"^[^@\s]+@[^@\s]+\.[^@\s]+$", email):
        raise ApiError("邮箱格式不正确")

    if purpose == "register":
        if db.qone("SELECT 1 FROM users WHERE lower(email) = ?", (email,)) is not None:
            raise ApiError("这个邮箱已经注册过了")
    else:
        if db.qone("SELECT 1 FROM users WHERE lower(email) = ?", (email,)) is None:
            raise ApiError("没有找到使用这个邮箱的账号")

    code, wait = auth.issue_code(email, purpose)
    if code is None:
        raise ApiError("%d 秒后才能重新获取" % int(wait), 429)

    sent, error, _code = mailer.send_code(email, code, purpose)
    payload = {"sent": bool(sent)}
    if not sent:
        # 没配 SMTP 时把验证码直接给前端，保证流程可用；配好 SMTP 后自然只发邮件
        if not mailer.configured():
            payload["dev_code"] = code
            payload["hint"] = "服务器还没配置发信通道，验证码直接显示在这里"
        else:
            low = str(error or "")
            if "535" in low or "authentication" in low.lower():
                payload["hint"] = "邮件服务认证失败，请联系管理员检查发信授权码"
            else:
                payload["hint"] = "邮件发送失败，请稍后再试或联系管理员"
    return ok(**payload)


@route("POST", "/api/register")
def api_register(c):
    username = str(c.arg("username")).strip()
    password = str(c.arg("password"))
    email = str(c.arg("email")).strip().lower()
    code = str(c.arg("code")).strip()

    if not re.match(r"^[A-Za-z0-9_\u4e00-\u9fa5-]{2,20}$", username):
        raise ApiError("用户名 2-20 位，只能用字母、数字、下划线、中文")
    if len(password) < 6:
        raise ApiError("密码至少 6 位")
    if not email:
        raise ApiError("请填写邮箱")
    if db.qone("SELECT 1 FROM users WHERE username = ?", (username,)) is not None:
        raise ApiError("这个用户名已被占用")
    if db.qone("SELECT 1 FROM users WHERE lower(email) = ?", (email,)) is not None:
        raise ApiError("这个邮箱已经注册过了")
    if not auth.verify_code(email, "register", code):
        raise ApiError("验证码不正确或已过期")

    uid = auth.create_user(username, password, email=email, role="user", display_name=username)
    token = auth.create_session(uid)
    c.h.set_cookie(token)
    user = db.qone("SELECT * FROM users WHERE id = ?", (uid,))
    return ok(user=store.user_brief(user), token=token)


@route("POST", "/api/recover/username")
def api_recover_username(c):
    email = str(c.arg("email")).strip().lower()
    code = str(c.arg("code")).strip()
    if not auth.verify_code(email, "find_username", code):
        raise ApiError("验证码不正确或已过期")
    user = auth.find_by_email(email)
    if user is None:
        raise ApiError("没有找到账号")
    return ok(username=user["username"])


@route("POST", "/api/recover/password")
def api_recover_password(c):
    email = str(c.arg("email")).strip().lower()
    code = str(c.arg("code")).strip()
    password = str(c.arg("new_password"))
    if len(password) < 6:
        raise ApiError("新密码至少 6 位")
    if not auth.verify_code(email, "reset_password", code):
        raise ApiError("验证码不正确或已过期")
    user = auth.find_by_email(email)
    if user is None:
        raise ApiError("没有找到账号")
    db.run("UPDATE users SET password_hash = ? WHERE id = ?", (auth.hash_password(password), user["id"]))
    db.run("DELETE FROM sessions WHERE user_id = ?", (user["id"],))
    return ok(username=user["username"])


# ==================================================================== 会话

@route("GET", "/api/conversations")
def api_conversations(c):
    user = c.need_login()
    items = store.list_conversations(user["id"])
    if store.is_admin(user):
        # 管理员额外看到 legacy 频道（已在成员里，这里去掉重复）
        pass
    return ok(conversations=items)


@route("POST", "/api/conversations")
def api_create_conversation(c):
    user = c.need_login()
    kind = str(c.arg("kind") or "direct")

    if kind == "direct":
        peer_id = int(c.arg("peer_id") or 0)
        allowed, why = store.can_direct_message(user, peer_id)
        if not allowed:
            raise ApiError(why)
        cid = store.get_or_create_dm(user["id"], peer_id)
        c.notify_conv(cid, {"type": "conversation", "conv_id": cid})
        return ok(conv_id=cid)

    if kind == "group":
        title = str(c.arg("title") or "新群聊")
        ids = [int(x) for x in (c.arg("member_ids") or []) if str(x).isdigit()]
        if store.is_sub(user):
            raise ApiError("子账号不能建群")
        # 只能拉好友进群
        safe = []
        for pid in ids:
            if store.are_friends(user["id"], pid) and pid != user["id"]:
                safe.append(pid)
        cid = store.create_group(user["id"], title, safe)
        c.notify_conv(cid, {"type": "conversation", "conv_id": cid})
        return ok(conv_id=cid)

    if kind == "legacy":
        # 只有管理员能开 legacy 频道
        if not store.is_admin(user):
            raise ApiError("只有管理员能使用旧频道", 403)
        cid = int(c.arg("channel") or 1)
        if str(cid) not in config.LEGACY_CHANNELS:
            raise ApiError("频道不存在")
        return ok(conv_id=cid)

    raise ApiError("不支持的会话类型")


@route("GET", "/api/conversations/<cid>")
def api_conversation(c):
    user = c.need_login()
    cid = int(c.params["cid"])
    if not store.is_member(cid, user["id"]):
        raise ApiError("你不在这个会话里", 403)
    conv = store.conv_row(cid)
    if conv is None:
        raise ApiError("会话不存在", 404)
    mem = [store.user_brief(m) | {"alias": m["alias"] or "",
                                  "member_role": m["member_role"] or "member"}
           for m in store.members(cid)]
    peer = None
    if conv["kind"] == "direct":
        peer_id = store._peer_of_direct(conv, user["id"])
        peer = store.user_brief(db.qone("SELECT * FROM users WHERE id = ?", (peer_id,)))
    return ok(
        conversation={
            "id": conv["id"], "kind": conv["kind"], "title": conv["title"],
            "avatar": conv["avatar"] or "",
            "notice": conv["notice"] or "",
            "history_max": store.history_limit(conv),
            "my_role": store.member_role(cid, user["id"]),
            "created_by": conv["created_by"], "peer": peer,
        },
        members=mem,
        messages=store.recent_messages(cid, None, user["id"]),
    )


@route("GET", "/api/conversations/<cid>/messages")
def api_messages(c):
    user = c.need_login()
    cid = int(c.params["cid"])
    if not store.is_member(cid, user["id"]):
        raise ApiError("你不在这个会话里", 403)
    since = int(c.q("since", "0") or 0)
    items = store.recent_messages(cid, None, user["id"])
    if since:
        items = [m for m in items if int(m["id"]) > since]
    return ok(messages=items)


@route("POST", "/api/conversations/<cid>/messages")
def api_send(c):
    user = c.need_login()
    cid = int(c.params["cid"])
    if not store.is_member(cid, user["id"]):
        raise ApiError("你不在这个会话里", 403)
    body = str(c.arg("body") or "").strip()
    media_id = int(c.arg("media_id") or 0)
    quote_id = int(c.arg("quote_id") or 0)
    if not body and not media_id:
        raise ApiError("消息不能为空")
    conv = store.conv_row(cid)
    if conv["kind"] == "direct":
        peer_id = store._peer_of_direct(conv, user["id"])
        if peer_id is not None and store.blocked_by(peer_id, user["id"]):
            raise ApiError("对方已把你加入黑名单，消息没有发出去")
    if media_id and db.qone("SELECT 1 FROM media WHERE id = ?", (media_id,)) is None:
        raise ApiError("图片不存在", 404)
    msg = store.append_message(cid, user["id"], body,
                               "image" if media_id else "text", media_id or None, quote_id or None)
    if msg is None:
        raise ApiError("消息不能为空")
    store.mark_read(cid, user["id"], msg["id"])
    c.notify_conv(cid, {"type": "message", "conv_id": cid, "message": msg})
    push_notify(cid, msg)
    return ok(message=msg)


@route("POST", "/api/conversations/<cid>/read")
def api_read(c):
    user = c.need_login()
    cid = int(c.params["cid"])
    if not store.is_member(cid, user["id"]):
        raise ApiError("你不在这个会话里", 403)
    store.mark_read(cid, user["id"])
    return ok()


@route("POST", "/api/conversations/<cid>/rename")
def api_rename(c):
    user = c.need_login()
    cid = int(c.params["cid"])
    if not store.is_member(cid, user["id"]):
        raise ApiError("你不在这个会话里", 403)
    conv = store.conv_row(cid)
    if conv["kind"] == "group" and not store.can_edit_group(conv, user["id"]):
        raise ApiError("只有群主或群管理员能改群名", 403)
    if conv["kind"] != "group" and not store.is_admin(user):
        raise ApiError("只有群聊可以改名")
    title = str(c.arg("title")).strip()
    if not title:
        raise ApiError("群名不能为空")
    store.rename_conv(cid, title)
    c.notify_conv(cid, {"type": "conversation", "conv_id": cid})
    return ok(title=title)


@route("POST", "/api/conversations/<cid>/alias")
def api_alias(c):
    user = c.need_login()
    cid = int(c.params["cid"])
    if not store.is_member(cid, user["id"]):
        raise ApiError("你不在这个会话里", 403)
    store.set_alias(cid, user["id"], str(c.arg("alias")))
    return ok()


@route("POST", "/api/conversations/<cid>/members")
def api_members(c):
    user = c.need_login()
    cid = int(c.params["cid"])
    if not store.is_member(cid, user["id"]):
        raise ApiError("你不在这个会话里", 403)
    conv = store.conv_row(cid)
    if conv["kind"] != "group":
        raise ApiError("只有群聊可以管理成员")
    if not store.can_edit_group(conv, user["id"]):
        raise ApiError("只有群主或群管理员能管理成员", 403)
    for pid in c.arg("add") or []:
        pid = int(pid)
        if store.are_friends(user["id"], pid):
            store.add_member(cid, pid)
    for pid in c.arg("remove") or []:
        store.remove_member(cid, int(pid))
    c.notify_conv(cid, {"type": "conversation", "conv_id": cid})
    return ok(members=[store.user_brief(m) for m in store.members(cid)])


@route("POST", "/api/conversations/<cid>/leave")
def api_leave(c):
    user = c.need_login()
    cid = int(c.params["cid"])
    if not store.is_member(cid, user["id"]):
        raise ApiError("你不在这个会话里", 403)
    conv = store.conv_row(cid)
    if conv["kind"] == "legacy":
        raise ApiError("旧频道不能退出")
    store.remove_member(cid, user["id"])
    HUB.push_user(user["id"], {"type": "conversation_removed", "conv_id": cid})
    c.notify_conv(cid, {"type": "conversation", "conv_id": cid})
    return ok()


@route("POST", "/api/conversations/<cid>/delete")
def api_delete_conv(c):
    """私聊：从自己列表里移除（对别人无感）。群聊：仅群主可解散。"""
    user = c.need_login()
    cid = int(c.params["cid"])
    if not store.is_member(cid, user["id"]):
        raise ApiError("你不在这个会话里", 403)
    conv = store.conv_row(cid)
    if conv["kind"] == "legacy":
        raise ApiError("旧频道不能删除")
    if conv["kind"] == "group" and int(conv["created_by"] or 0) != int(user["id"]):
        raise ApiError("只有群主能解散群", 403)
    ids = store.member_ids(cid)
    if conv["kind"] == "group":
        db.run("DELETE FROM messages WHERE conv_id = ?", (cid,))
        db.run("DELETE FROM conversation_members WHERE conv_id = ?", (cid,))
        db.run("DELETE FROM conversations WHERE id = ?", (cid,))
        for uid in ids:
            HUB.push_user(uid, {"type": "conversation_removed", "conv_id": cid})
    else:
        store.remove_member(cid, user["id"])
        HUB.push_user(user["id"], {"type": "conversation_removed", "conv_id": cid})
    return ok()


# ==================================================================== 好友 / 黑名单 / 搜索

@route("GET", "/api/friends")
def api_friends(c):
    user = c.need_login()
    return ok(friends=store.friends_of(user["id"]), blocks=store.blocks_of(user["id"]))


@route("POST", "/api/friends")
def api_add_friend(c):
    user = c.need_login()
    if store.is_sub(user):
        raise ApiError("子账号不能加好友")
    peer = int(c.arg("peer_id") or 0)
    if peer == int(user["id"]):
        raise ApiError("不能加自己")
    row = db.qone("SELECT * FROM users WHERE id = ?", (peer,))
    if row is None:
        raise ApiError("用户不存在", 404)
    if store.is_sub(row):
        raise ApiError("不能添加子账号为好友")
    store.add_friend(user["id"], peer)
    HUB.push_user(peer, {"type": "friend", "peer": store.user_brief(user)})
    return ok(peer=store.user_brief(row))


@route("DELETE", "/api/friends/<peer>")
def api_del_friend(c):
    user = c.need_login()
    store.remove_friend(user["id"], int(c.params["peer"]))
    return ok()


@route("POST", "/api/blocks")
def api_block(c):
    user = c.need_login()
    store.block(user["id"], int(c.arg("peer_id") or 0))
    return ok()


@route("DELETE", "/api/blocks/<peer>")
def api_unblock(c):
    user = c.need_login()
    store.unblock(user["id"], int(c.params["peer"]))
    return ok()


@route("GET", "/api/search")
def api_search(c):
    user = c.need_login()
    kw = str(c.q("q") or "").strip()
    if len(kw) < 1:
        return ok(users=[])
    rows = db.qall(
        "SELECT * FROM users WHERE (username LIKE ? OR display_name LIKE ?) "
        "AND is_sub = 0 AND status = 'active' ORDER BY (id = ?) DESC, username LIMIT 20",
        ("%" + kw + "%", "%" + kw + "%", user["id"]),
    )
    out = []
    for r in rows:
        item = store.user_brief(r)
        item["is_friend"] = store.are_friends(user["id"], r["id"])
        item["is_self"] = int(r["id"]) == int(user["id"])
        out.append(item)
    return ok(users=out)


# ==================================================================== 群头像 / 推送

def _icon_url(stored):
    """把 "av:x" / "gv:x" 换成通知里能直接加载的绝对地址。"""
    val = str(stored or "")
    if val.startswith("av:"):
        return config.SITE_URL + "/avatar/" + val[3:]
    if val.startswith("gv:"):
        return config.SITE_URL + "/gavatar/" + val[3:]
    return config.SITE_URL + "/static/icon.png"


def webp_size(data):
    """从 webp 头里读宽高，读不出来就返回 0。"""
    try:
        if data[:4] != b"RIFF" or data[8:12] != b"WEBP":
            return 0, 0
        chunk = data[12:16]
        if chunk == b"VP8X":
            return (1 + int.from_bytes(data[24:27], "little"),
                    1 + int.from_bytes(data[27:30], "little"))
        if chunk == b"VP8 ":
            i = data.index(b"\x9d\x01\x2a", 20, 40)
            w = int.from_bytes(data[i + 3:i + 5], "little") & 0x3FFF
            h = int.from_bytes(data[i + 5:i + 7], "little") & 0x3FFF
            return w, h
        if chunk == b"VP8L":
            bits = int.from_bytes(data[21:25], "little")
            return (bits & 0x3FFF) + 1, ((bits >> 14) & 0x3FFF) + 1
    except Exception:  # noqa: BLE001
        pass
    return 0, 0


def push_notify(cid, msg):
    """新消息 → 给其他成员排队发一条通知。任何异常都不该影响发消息。"""
    try:
        if msg is None or not push.HAVE_CRYPTO:
            return
        conv = store.conv_row(cid)
        if conv is None or conv["kind"] == "legacy":
            return
        sender_id = int(msg.get("sender_id") or 0)
        if msg.get("kind") == "image":
            mid = (msg.get("media") or {}).get("id")
            body = "[表情]" if mid and store.is_sticker_media(mid) else "[图片]"
        else:
            body = str(msg.get("body") or "")
        mentioned = {int(x) for x in (msg.get("mentions") or [])}
        body = body[:120]
        for uid in store.member_ids(cid):
            if uid == sender_id:
                continue
            if sender_id and store.blocked_by(uid, sender_id):
                continue
            title, icon = store.conv_notify_view(conv, uid)
            text = ("@你 " + body) if uid in mentioned else body
            push.queue(uid, cid, title, text, _icon_url(icon),
                       config.SITE_URL + "/?conv=%d" % int(cid), "conv-%d" % int(cid))
    except Exception:  # noqa: BLE001
        pass


@route("POST", "/api/conversations/<cid>/avatar")
def api_conv_avatar(c):
    """群头像：只有创建者能换。"""
    user = c.need_login()
    cid = int(c.params["cid"])
    conv = store.conv_row(cid)
    if conv is None or not store.is_member(cid, user["id"]):
        raise ApiError("会话不存在", 404)
    if conv["kind"] != "group":
        raise ApiError("只有群聊能换头像")
    if not store.can_edit_group(conv, user["id"]):
        raise ApiError("只有群主或群管理员能换群头像", 403)
    stored = _save_upload(c.arg("data"), cid, "group")
    old = str(conv["avatar"] or "")
    db.run("UPDATE conversations SET avatar = ? WHERE id = ?", (stored, cid))
    if old and old != stored:
        _drop_upload_file(old, GROUP_DIR)
    c.notify_conv(cid, {"type": "conversation", "conv_id": cid})
    return ok(conv_id=cid, avatar=stored)


@route("GET", "/api/push/key")
def api_push_key(c):
    c.need_login()
    key = push.public_key()
    return ok(key=key, enabled=bool(key))


@route("POST", "/api/diag")
def api_diag(c):
    """前端诊断日志：按天追加到 data/diag/，只留最近两份。"""
    user = c.need_login()
    events = c.arg("events") or []
    if not isinstance(events, list) or not events:
        return ok()
    sid = str(c.arg("sid") or "")[:12]
    os.makedirs(DIAG_DIR, exist_ok=True)
    path = os.path.join(DIAG_DIR, time.strftime("%Y%m%d") + ".jsonl")
    try:
        if os.path.getsize(path) > 8 * 1024 * 1024:
            os.replace(path, path + ".1")
    except OSError:
        pass
    uid = int(user["id"])
    try:
        with open(path, "a", encoding="utf-8") as fh:
            for ev in events[:200]:
                line = json.dumps({"uid": uid, "sid": sid, "ev": ev}, ensure_ascii=False)
                fh.write(line[:2000] + chr(10))
    except OSError:
        pass
    return ok()


@route("GET", "/api/diag/read")
def api_diag_read(c):
    """管理员看最近日志，方便直接贴给我。"""
    c.need_admin()
    n = max(1, min(2000, int(c.q("n", "200") or 200)))
    path = os.path.join(DIAG_DIR, time.strftime("%Y%m%d") + ".jsonl")
    try:
        with open(path, "r", encoding="utf-8") as fh:
            lines = fh.readlines()[-n:]
    except OSError:
        lines = []
    return ok(lines=[x.rstrip(chr(10)) for x in lines])


@route("POST", "/api/push/subscribe")
def api_push_subscribe(c):
    user = c.need_login()
    sub = c.arg("subscription") or {}
    endpoint = str(sub.get("endpoint") or "").strip()
    keys = sub.get("keys") or {}
    p256dh = str(keys.get("p256dh") or "").strip()
    auth_key = str(keys.get("auth") or "").strip()
    if not endpoint.startswith("https://") or not p256dh or not auth_key:
        raise ApiError("订阅信息不完整")
    db.run(
        "INSERT INTO push_subs (user_id, endpoint, p256dh, auth, created_at) VALUES (?, ?, ?, ?, ?) "
        "ON CONFLICT(endpoint) DO UPDATE SET user_id = excluded.user_id, "
        "p256dh = excluded.p256dh, auth = excluded.auth",
        (int(user["id"]), endpoint[:600], p256dh[:200], auth_key[:100], db.now()),
    )
    return ok(count=db.qone("SELECT COUNT(*) AS n FROM push_subs WHERE user_id = ?", (user["id"],))["n"])


@route("POST", "/api/push/unsubscribe")
def api_push_unsubscribe(c):
    user = c.need_login()
    endpoint = str(c.arg("endpoint") or "").strip()
    if endpoint:
        db.run("DELETE FROM push_subs WHERE user_id = ? AND endpoint = ?", (int(user["id"]), endpoint))
    else:
        db.run("DELETE FROM push_subs WHERE user_id = ?", (int(user["id"]),))
    return ok()


@route("POST", "/api/media")
def api_media(c):
    """图片先传到这里：按 sha1 去重，同一张图全服只存一份。"""
    c.need_login()
    hit = re.match(r"^data:image/webp;base64,(.+)$", str(c.arg("data") or ""), re.S)
    if not hit:
        raise ApiError("只接受 webp 图片")
    try:
        data = base64.b64decode(hit.group(1), validate=True)
    except Exception:  # noqa: BLE001
        raise ApiError("图片数据损坏")
    if len(data) < 64:
        raise ApiError("图片太小")
    if len(data) > MAX_MEDIA_BYTES:
        raise ApiError("图片太大（上限 %dKB）" % (MAX_MEDIA_BYTES // 1024))
    if data[:4] != b"RIFF" or data[8:12] != b"WEBP":
        raise ApiError("不是有效的 webp")
    digest = hashlib.sha1(data).hexdigest()
    width, height = webp_size(data)
    row = store.upsert_media(digest, len(data), width, height)
    os.makedirs(MEDIA_DIR, exist_ok=True)
    path = os.path.join(MEDIA_DIR, digest + ".webp")
    if not os.path.isfile(path):
        with open(path, "wb") as fh:
            fh.write(data)
    return ok(media=store.media_brief(row))


@route("POST", "/api/conversations/<cid>/typing")
def api_typing(c):
    """正在输入：只在私聊转发，群聊直接忽略。"""
    user = c.need_login()
    cid = int(c.params["cid"])
    conv = store.conv_row(cid)
    if conv is None or not store.is_member(cid, user["id"]):
        return ok()
    if conv["kind"] not in ("direct", "pkn"):
        return ok()
    active = bool(c.arg("active", True))
    HUB.push_conversation(
        [u for u in store.member_ids(cid) if u != int(user["id"])],
        {"type": "typing", "conv_id": cid, "user_id": int(user["id"]), "active": active},
    )
    return ok()


@route("POST", "/api/messages/<mid>/recall")
def api_recall(c):
    user = c.need_login()
    fine, err, event = store.recall_message(int(c.params["mid"]), user)
    if not fine:
        raise ApiError(err, 403)
    if event:
        payload = {"type": "message_recalled"}
        payload.update(event)
        c.notify_conv(event["conv_id"], payload)
    return ok(event=event)


@route("POST", "/api/messages/<mid>/hide")
def api_hide_message(c):
    """本地删除：只对自己隐藏，不广播。"""
    user = c.need_login()
    if not store.hide_message(user["id"], int(c.params["mid"])):
        raise ApiError("消息不存在", 404)
    return ok()


@route("GET", "/api/stickers")
def api_stickers(c):
    user = c.need_login()
    items = store.stickers_of(user["id"])
    return ok(stickers=items, used=len(items),
              limit=0 if store.is_admin(user) else store.STICKER_LIMIT)


@route("POST", "/api/stickers")
def api_add_sticker(c):
    user = c.need_login()
    media_id = int(c.arg("media_id") or 0)
    if db.qone("SELECT 1 FROM media WHERE id = ?", (media_id,)) is None:
        raise ApiError("图片不存在", 404)
    used = len(store.stickers_of(user["id"]))
    if not store.is_admin(user) and used >= store.STICKER_LIMIT:
        raise ApiError("表情包最多 %d 个" % store.STICKER_LIMIT)
    total = store.add_sticker(user["id"], media_id)
    return ok(used=total)


@route("DELETE", "/api/stickers/<sid>")
def api_del_sticker(c):
    user = c.need_login()
    store.del_sticker(user["id"], int(c.params["sid"]))
    return ok()


@route("POST", "/api/conversations/<cid>/notice")
def api_notice(c):
    user = c.need_login()
    cid = int(c.params["cid"])
    conv = store.conv_row(cid)
    if conv is None or not store.is_member(cid, user["id"]):
        raise ApiError("会话不存在", 404)
    if not store.can_edit_group(conv, user["id"]):
        raise ApiError("只有群主或群管理员能改群公告", 403)
    text = str(c.arg("notice") or "").strip()[:1000]
    store.set_notice(cid, text)
    c.notify_conv(cid, {"type": "conversation", "conv_id": cid})
    return ok(notice=text)


@route("POST", "/api/conversations/<cid>/history")
def api_history_max(c):
    """只有网站管理员能改群的消息留存条数。"""
    user = c.need_login()
    if not store.is_admin(user):
        raise ApiError("只有网站管理员能扩容", 403)
    cid = int(c.params["cid"])
    conv = store.conv_row(cid)
    if conv is None or conv["kind"] != "group":
        raise ApiError("只有群聊可以扩容", 404)
    keep = int(c.arg("history_max") or 0)
    if keep not in HISTORY_CHOICES:
        raise ApiError("只能是 %s" % " / ".join(str(x) for x in HISTORY_CHOICES))
    store.set_history_max(cid, keep)
    c.notify_conv(cid, {"type": "conversation", "conv_id": cid})
    return ok(history_max=keep)


@route("POST", "/api/conversations/<cid>/members/<uid>/role")
def api_member_role(c):
    """群主任免群管理员。这里说的是群内角色，跟网站 admin 无关。"""
    user = c.need_login()
    cid = int(c.params["cid"])
    conv = store.conv_row(cid)
    if conv is None or conv["kind"] != "group":
        raise ApiError("只有群聊有管理员", 404)
    if not store.is_owner(conv, user["id"]):
        raise ApiError("只有群主能设置群管理员", 403)
    target = int(c.params["uid"])
    if target == int(user["id"]):
        raise ApiError("群主不能改自己的角色")
    if not store.is_member(cid, target):
        raise ApiError("他不在这个群里", 404)
    role = str(c.arg("role") or "member")
    if role not in ("admin", "member"):
        raise ApiError("只能是 admin 或 member")
    store.set_member_role(cid, target, role)
    c.notify_conv(cid, {"type": "conversation", "conv_id": cid})
    return ok(user_id=target, role=role)


@route("POST", "/api/push/test")
def api_push_test(c):
    user = c.need_login()
    push.queue(int(user["id"]), 0, config.MAIL_NAME, "测试通知，看到就说明推送通了。",
               _icon_url(""), config.SITE_URL + "/", "kokona-test")
    return ok()


# ==================================================================== 子账号

@route("GET", "/api/subs")
def api_subs(c):
    """WSS 账号：用户名跟主账号共用，只对外暴露显示名。"""
    user = c.need_login()
    rows = db.qall(
        "SELECT * FROM users WHERE parent_id = ? AND is_sub = 1 ORDER BY id",
        (user["id"],),
    )
    subs = [
        {
            "id": int(r["id"]),
            "display_name": r["display_name"] or "WSS 账号",
            "username": user["username"],           # 共用主账号用户名
            "created_at": int(r["created_at"] or 0),
        }
        for r in rows
    ]
    return ok(
        subs=subs,
        can_create=(not store.is_sub(user)) and len(subs) == 0,
        login_user=user["username"],
    )


@route("POST", "/api/subs")
def api_create_sub(c):
    user = c.need_login()
    if store.is_sub(user):
        raise ApiError("子账号不能再建子账号")
    if db.qone("SELECT 1 FROM users WHERE parent_id = ? AND is_sub = 1", (user["id"],)):
        raise ApiError("已经有 WSS 账号了，在设置里改密码就行")
    password = str(c.arg("password") or "")
    display = str(c.arg("display_name") or "WSS 账号").strip()[:30]
    if len(password) < 6:
        raise ApiError("密码至少 6 位")

    # 用户名不对外暴露也不参与登录：登录用「主账号用户名 + 这个密码」
    hidden = "~sub:%d-%s" % (user["id"], secrets.token_hex(3))
    uid = auth.create_user(hidden, password, role="user", is_sub=1,
                           parent_id=user["id"], display_name=display)
    cid = store.get_or_create_dm(user["id"], uid)
    HUB.push_user(user["id"], {"type": "conversation", "conv_id": cid})
    return ok(
        sub={"id": uid, "display_name": display, "username": user["username"]},
        conv_id=cid,
    )


@route("POST", "/api/subs/<sid>")
def api_update_sub(c):
    user = c.need_login()
    sid = int(c.params["sid"])
    row = db.qone(
        "SELECT * FROM users WHERE id = ? AND parent_id = ? AND is_sub = 1",
        (sid, user["id"]),
    )
    if row is None:
        raise ApiError("子账号不存在", 404)

    if c.arg("display_name") is not None:
        name = str(c.arg("display_name") or "").strip()[:30]
        if not name:
            raise ApiError("显示名不能为空")
        db.run("UPDATE users SET display_name = ? WHERE id = ?", (name, sid))

    pw = str(c.arg("password") or "")
    if pw:
        if len(pw) < 6:
            raise ApiError("密码至少 6 位")
        db.run("UPDATE users SET password_hash = ? WHERE id = ?", (auth.hash_password(pw), sid))
        db.run("DELETE FROM sessions WHERE user_id = ?", (sid,))

    fresh = db.qone("SELECT * FROM users WHERE id = ?", (sid,))
    return ok(sub={
        "id": sid,
        "display_name": fresh["display_name"] or "WSS 账号",
        "username": user["username"],
    })


@route("DELETE", "/api/subs/<sid>")
def api_del_sub(c):
    user = c.need_login()
    sid = int(c.params["sid"])
    row = db.qone("SELECT * FROM users WHERE id = ? AND parent_id = ?", (sid, user["id"]))
    if row is None:
        raise ApiError("子账号不存在", 404)
    db.run("DELETE FROM sessions WHERE user_id = ?", (sid,))
    db.run("DELETE FROM users WHERE id = ?", (sid,))
    return ok()


# ==================================================================== 公告

@route("GET", "/api/announcements")
def api_announcements(c):
    user = c.need_login()
    return ok(announcements=store.list_announcements(user["id"]))


@route("POST", "/api/announcements/<aid>/read")
def api_ann_read(c):
    user = c.need_login()
    store.mark_announcement_read(int(c.params["aid"]), user["id"])
    return ok()


# ==================================================================== 管理后台

@route("GET", "/api/admin/stats")
def api_admin_stats(c):
    c.need_admin()
    users = db.qone("SELECT COUNT(*) AS n FROM users WHERE is_sub = 0")["n"]
    subs = db.qone("SELECT COUNT(*) AS n FROM users WHERE is_sub = 1")["n"]
    convs = db.qone("SELECT COUNT(*) AS n FROM conversations")["n"]
    msgs = db.qone("SELECT COUNT(*) AS n FROM messages")["n"]
    banned = db.qone("SELECT COUNT(*) AS n FROM users WHERE status='banned'")["n"]
    today = db.now() - 86400
    active = db.qone("SELECT COUNT(*) AS n FROM sessions WHERE expires_at > ?", (db.now(),))["n"]
    mails = db.qone("SELECT COUNT(*) AS n FROM mail_log WHERE created_at > ?", (today,))["n"]
    return ok(stats={
        "users": int(users), "subs": int(subs), "conversations": int(convs),
        "messages": int(msgs), "banned": int(banned), "sessions": int(active),
        "mails_24h": int(mails), "online": len(HUB.online_users()),
        "smtp": "已配置" if mailer.configured() else "未配置",
        "history_max": config.HISTORY_MAX,
        "uptime_hint": "单进程 · 标准库 · SQLite",
    })


@route("GET", "/api/admin/users")
def api_admin_users(c):
    c.need_admin()
    kw = str(c.q("q") or "").strip()
    if kw:
        rows = db.qall(
            "SELECT * FROM users WHERE username LIKE ? OR email LIKE ? OR display_name LIKE ? "
            "ORDER BY id DESC LIMIT 200",
            ("%" + kw + "%", "%" + kw + "%", "%" + kw + "%"),
        )
    else:
        rows = db.qall("SELECT * FROM users ORDER BY id DESC LIMIT 200")
    out = []
    for r in rows:
        item = store.user_brief(r)
        item["email"] = r["email"] or ""
        item["status"] = r["status"]
        item["created_at"] = r["created_at"]
        item["parent_id"] = r["parent_id"]
        out.append(item)
    return ok(users=out)


@route("POST", "/api/admin/users")
def api_admin_create_user(c):
    c.need_admin()
    username = str(c.arg("username")).strip()
    password = str(c.arg("password"))
    email = str(c.arg("email")).strip().lower() or None
    role = str(c.arg("role") or "user")
    if not username or len(password) < 6:
        raise ApiError("用户名必填，密码至少 6 位")
    if db.qone("SELECT 1 FROM users WHERE username = ?", (username,)) is not None:
        raise ApiError("用户名已存在")
    uid = auth.create_user(username, password, email=email,
                           role="admin" if role == "admin" else "user")
    return ok(id=uid)


@route("POST", "/api/admin/users/<uid>/status")
def api_admin_set_status(c):
    c.need_admin()
    uid = int(c.params["uid"])
    status = str(c.arg("status") or "active")
    target = db.qone("SELECT * FROM users WHERE id = ?", (uid,))
    if target is None:
        raise ApiError("用户不存在", 404)
    if target["role"] == "admin" and target["username"] == config.ADMIN_USERNAME:
        raise ApiError("不能封禁主管理员")
    db.run("UPDATE users SET status = ? WHERE id = ?", ("banned" if status == "banned" else "active", uid))
    if status == "banned":
        db.run("DELETE FROM sessions WHERE user_id = ?", (uid,))
    return ok(status=status)


@route("POST", "/api/admin/announcements")
def api_admin_announce(c):
    user = c.need_admin()
    title = str(c.arg("title")).strip() or "公告"
    body = str(c.arg("body")).strip()
    if not body:
        raise ApiError("公告内容不能为空")
    aid = store.create_announcement(user["id"], title, body)
    for uid in HUB.online_users():
        HUB.push_user(uid, {"type": "announcement", "id": aid, "title": title})
    return ok(id=aid)


@route("GET", "/api/admin/mails")
def api_admin_mails(c):
    c.need_admin()
    rows = db.qall("SELECT * FROM mail_log ORDER BY id DESC LIMIT 100")
    return ok(mails=[{
        "id": r["id"], "to": r["to_addr"], "subject": r["subject"],
        "status": r["status"], "error": r["error"], "created_at": r["created_at"],
    } for r in rows])


@route("GET", "/api/admin/codes")
def api_admin_codes(c):
    """没配 SMTP 时，管理员可以在这里看最近发出的验证码。"""
    c.need_admin()
    rows = db.qall(
        "SELECT email, code, purpose, expires_at FROM email_codes "
        "WHERE used = 0 AND expires_at > ? ORDER BY id DESC LIMIT 50",
        (db.now(),),
    )
    return ok(codes=[dict(r) for r in rows])


# ==================================================================== SSE

@route("GET", "/api/stream")
def api_stream(c):
    user = c.need_login()
    h = c.h
    q = HUB.sse_attach(user["id"])
    try:
        h.send_response(200)
        h.send_header("Content-Type", "text/event-stream; charset=utf-8")
        h.send_header("Cache-Control", "no-cache, no-store")
        h.send_header("X-Accel-Buffering", "no")
        h.send_header("Connection", "keep-alive")
        h.end_headers()
        h.wfile.write(b"retry: 3000\n\n")
        h.wfile.flush()
        h.close_connection = True
        last = time.time()
        while not h._stop:
            try:
                text = q.get(timeout=20)
                h.wfile.write(("data: " + text + "\n\n").encode("utf-8"))
                h.wfile.flush()
                last = time.time()
            except Exception:
                if time.time() - last > 15:
                    h.wfile.write(b": ping\n\n")
                    h.wfile.flush()
                    last = time.time()
    except (BrokenPipeError, ConnectionResetError):
        pass
    finally:
        HUB.sse_detach(user["id"], q)
    return None


# ==================================================================== HTTP Handler

class Handler(BaseHTTPRequestHandler):
    server_version = "KokonaChat/2.0"
    protocol_version = "HTTP/1.1"

    def log_message(self, fmt, *args):  # 静音，避免刷日志
        pass

    _stop = False

    # ---------------- 基础工具 ----------------

    def _prefix(self):
        """本次请求的挂载前缀：优先用 nginx 传的 X-Forwarded-Prefix，
        这样同一个服务既能挂在 /chat/ 下，也能挂在 chat 子域的根路径。"""
        raw = self.headers.get("X-Forwarded-Prefix")
        if raw is None:
            return config.BASE
        raw = raw.strip()
        if not raw or raw == "/":
            return ""
        return "/" + raw.strip("/")

    def _path(self):
        raw = urlparse(self.path)
        path = unquote(raw.path or "/")
        prefix = self._prefix()
        if prefix and path.startswith(prefix):
            path = path[len(prefix):] or "/"
        return path.rstrip("/") or "/", parse_qs(raw.query)

    def session_token(self):
        cookie = self.headers.get("Cookie") or ""
        for part in cookie.split(";"):
            part = part.strip()
            if part.startswith(config.SESSION_COOKIE + "="):
                return part.split("=", 1)[1]
        authz = self.headers.get("Authorization") or ""
        if authz.lower().startswith("bearer "):
            return authz[7:].strip()
        return ""

    def set_cookie(self, token):
        self._pending_cookie = "%s=%s; Path=%s; Max-Age=%d; HttpOnly; SameSite=Lax" % (
            config.SESSION_COOKIE, token, self._prefix() or "/", config.SESSION_TTL
        )

    def clear_cookie(self):
        self._pending_cookie = "%s=; Path=%s; Max-Age=0; HttpOnly; SameSite=Lax" % (
            config.SESSION_COOKIE, self._prefix() or "/"
        )

    def _send_headers(self, code, ctype, length=0, extra=None):
        self.send_response(code)
        self.send_header("Content-Type", ctype)
        if length:
            self.send_header("Content-Length", str(length))
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("Referrer-Policy", "same-origin")
        if getattr(self, "_pending_cookie", None):
            self.send_header("Set-Cookie", self._pending_cookie)
            self._pending_cookie = None
        for k, v in (extra or []):
            self.send_header(k, v)
        self.end_headers()

    def _json(self, code, obj):
        payload = json.dumps(obj, ensure_ascii=False).encode("utf-8")
        self._send_headers(code, "application/json; charset=utf-8", len(payload))
        try:
            self.wfile.write(payload)
        except Exception:
            pass

    def _html(self, code, text):
        payload = text.encode("utf-8")
        self._send_headers(code, "text/html; charset=utf-8", len(payload),
                           [("Cache-Control", "no-store")])
        try:
            self.wfile.write(payload)
        except Exception:
            pass

    def _static(self, path):
        name = path[len("/static/"):]
        if "/" in name or ".." in name or name == "":
            self._send_headers(404, "text/plain; charset=utf-8", 0)
            return
        full = os.path.join(STATIC_DIR, name)
        if not os.path.isfile(full):
            self._send_headers(404, "text/plain; charset=utf-8", 0)
            return
        try:
            with open(full, "rb") as fh:
                data = fh.read()
        except OSError:
            self._send_headers(500, "text/plain; charset=utf-8", 0)
            return
        ext = os.path.splitext(name)[1].lower()
        self._send_headers(
            200, STATIC_MIME.get(ext, "application/octet-stream"), len(data),
            [("Cache-Control", "public, max-age=604800")],
        )
        try:
            self.wfile.write(data)
        except Exception:
            pass

    def _media_file(self, name):
        if not re.match(r"^[0-9a-f]{8,64}\.webp$", name or ""):
            self._send_headers(404, "text/plain; charset=utf-8", 0)
            return
        full = os.path.join(MEDIA_DIR, name)
        if not os.path.isfile(full):
            self._send_headers(404, "text/plain; charset=utf-8", 0)
            return
        try:
            with open(full, "rb") as fh:
                data = fh.read()
        except OSError:
            self._send_headers(500, "text/plain; charset=utf-8", 0)
            return
        self._send_headers(
            200, "image/webp", len(data),
            [("Cache-Control", "public, max-age=31536000, immutable")],
        )
        try:
            self.wfile.write(data)
        except Exception:
            pass

    def _service_worker(self):
        full = os.path.join(STATIC_DIR, "sw.js")
        try:
            with open(full, "rb") as fh:
                data = fh.read()
        except OSError:
            self._send_headers(404, "text/plain; charset=utf-8", 0)
            return
        self._send_headers(
            200, "application/javascript; charset=utf-8", len(data),
            [("Cache-Control", "no-cache"), ("Service-Worker-Allowed", "/")],
        )
        try:
            self.wfile.write(data)
        except Exception:
            pass

    def _avatar(self, name, folder=None):
        if "/" in name or ".." in name or name == "":
            self._send_headers(404, "text/plain; charset=utf-8", 0)
            return
        full = os.path.join(folder or AVATAR_DIR, name)
        if not os.path.isfile(full):
            self._send_headers(404, "text/plain; charset=utf-8", 0)
            return
        try:
            with open(full, "rb") as fh:
                data = fh.read()
        except OSError:
            self._send_headers(500, "text/plain; charset=utf-8", 0)
            return
        ext = os.path.splitext(name)[1].lower()
        self._send_headers(
            200, STATIC_MIME.get(ext, "application/octet-stream"), len(data),
            [("Cache-Control", "public, max-age=86400")],
        )
        try:
            self.wfile.write(data)
        except Exception:
            pass

    def _redirect(self, location, code=302):
        self.send_response(code)
        self.send_header("Location", location)
        if getattr(self, "_pending_cookie", None):
            self.send_header("Set-Cookie", self._pending_cookie)
            self._pending_cookie = None
        self.send_header("Content-Length", "0")
        self.end_headers()

    def _read_body(self, content_type):
        try:
            length = int(self.headers.get("Content-Length") or 0)
        except ValueError:
            length = 0
        if length <= 0 or length > 2 << 20:
            return {}
        raw = self.rfile.read(length)
        text = raw.decode("utf-8", "replace")
        if "application/json" in (content_type or ""):
            try:
                data = json.loads(text)
                return data if isinstance(data, dict) else {}
            except Exception:
                return {}
        parsed = parse_qs(text)
        return {k: (v[0] if len(v) == 1 else v) for k, v in parsed.items()}

    def current_user(self):
        token = self.session_token()
        if not token:
            return None
        row = auth.user_by_session(token)
        if row is not None and row["status"] == "banned":
            return None
        return row

    # ---------------- 入口 ----------------

    def do_GET(self):
        self._dispatch("GET")

    def do_POST(self):
        self._dispatch("POST")

    def do_DELETE(self):
        self._dispatch("DELETE")

    def do_OPTIONS(self):
        self._send_headers(204, "text/plain", 0, [("Allow", "GET, POST, DELETE, OPTIONS")])

    def _dispatch(self, method):
        try:
            path, query = self._path()
            user = self.current_user()

            # WebSocket 升级
            if path == "/ws":
                self._ws(path, query, user)
                return

            # 静态资源
            if path.startswith("/static/"):
                self._static(path)
                return

            # 用户头像（运行时写入数据目录）
            if path.startswith("/avatar/"):
                self._avatar(path[len("/avatar/"):])
                return

            # 资料卡封面
            if path.startswith("/cover/"):
                self._avatar(path[len("/cover/"):], folder=COVER_DIR)
                return

            # 群头像
            if path.startswith("/gavatar/"):
                self._avatar(path[len("/gavatar/"):], folder=GROUP_DIR)
                return

            # 图片消息（按内容哈希，永久缓存）
            if path.startswith("/m/"):
                self._media_file(path[len("/m/"):])
                return

            # Service Worker 必须在根路径，才能接管整站
            if path == "/sw.js":
                self._service_worker()
                return

            # API
            if path.startswith("/api/"):
                body = self._read_body(self.headers.get("Content-Type"))
                for m, regex, fn in _ROUTES:
                    if m != method:
                        continue
                    hit = regex.match(path)
                    if not hit:
                        continue
                    c = Ctx(self, user, path, query, body, hit.groupdict())
                    result = fn(c)
                    if result is None:
                        return
                    code, obj = result
                    self._json(code, obj)
                    return
                self._json(404, {"ok": False, "error": "接口不存在"})
                return

            # 页面
            self._page(path, query, user)
        except ApiError as e:
            self._json(e.code, {"ok": False, "error": e.message})
        except BrokenPipeError:
            pass
        except Exception:
            traceback.print_exc()
            try:
                self._json(500, {"ok": False, "error": "服务器内部错误"})
            except Exception:
                pass

    def _page(self, path, query, user):
        if path == "/login":
            if user is not None:
                self._redirect(self._prefix() + "/")
            else:
                self._html(200, pages.login_page(base=self._prefix()))
            return
        if path == "/register":
            if user is not None:
                self._redirect(self._prefix() + "/")
            else:
                self._html(200, pages.register_page(base=self._prefix()))
            return
        if path == "/recover":
            self._html(200, pages.recover_page(base=self._prefix()))
            return
        if path == "/favicon.ico":
            self._static("/static/icon.ico")
            return
        if path == "/health":
            self._json(200, {"ok": True, "t": int(time.time())})
            return

        # 以下需要登录
        if user is None:
            self._redirect(self._prefix() + "/login?next=" + path)
            return

        if path == "/":
            self._html(200, pages.app_page(user, store, HUB, base=self._prefix()))
            return
        if path == "/admin":
            if not store.is_admin(user):
                self._redirect(self._prefix() + "/")
                return
            self._html(200, pages.admin_page(user, store, HUB, base=self._prefix()))
            return
        # 其它路径都交给前端路由
        self._html(200, pages.app_page(user, store, HUB, base=self._prefix()))

    # ---------------- WebSocket ----------------

    def _ws(self, path, query, user):
        key = self.headers.get("Sec-WebSocket-Key")
        if not key:
            self._json(400, {"ok": False, "error": "缺少 WebSocket key"})
            return

        # 鉴权：?user=&pass= 或已登录的 cookie
        qs_user = (query.get("user") or [""])[0]
        qs_pass = (query.get("pass") or [""])[0]
        if qs_user or qs_pass:
            row, msg = auth.authenticate(qs_user, qs_pass)
            if row is None:
                self._json(401, {"ok": False, "error": msg or "鉴权失败"})
                return
            user = row

        if user is None:
            self._json(401, {"ok": False, "error": "需要账号密码"})
            return

        accept = wskit.accept_key(key)
        self.send_response(101, "Switching Protocols")
        self.send_header("Upgrade", "websocket")
        self.send_header("Connection", "Upgrade")
        self.send_header("Sec-WebSocket-Accept", accept)
        self.end_headers()
        try:
            self.wfile.flush()
        except Exception:
            return

        conn = wskit.WSConn(self.connection, user)
        HUB.ws_attach(user["id"], conn)
        try:
            conn.send_json(json.dumps({
                "type": "hello",
                "user": store.user_brief(user),
                "conversations": store.list_conversations(user["id"]),
            }, ensure_ascii=False))
            while conn.alive:
                fin, opcode, payload = wskit.read_frame(self.rfile)
                if opcode == wskit.OP_CLOSE:
                    break
                if opcode == wskit.OP_PING:
                    conn.send(wskit.OP_PONG, payload)
                    continue
                if opcode == wskit.OP_PONG:
                    continue
                if opcode != wskit.OP_TEXT:
                    continue
                text = payload.decode("utf-8", "replace")
                replies = _handle_ws_message(user, text, conn)
                for item in replies:
                    conn.send_json(json.dumps(item, ensure_ascii=False))
        except Exception:
            pass
        finally:
            conn.alive = False
            HUB.ws_detach(user["id"], conn)
            self.close_connection = True


def _handle_ws_message(user, text, conn=None):
    """程序端发来的帧：{"action": "...", ...}。返回要回给它的消息列表。"""
    try:
        msg = json.loads(text)
    except Exception:
        msg = {"action": "send", "text": text}
    if not isinstance(msg, dict):
        msg = {"action": "send", "text": str(msg)}

    action = str(msg.get("action") or "send")

    # ---------------- PKN：账号专属 WSS 聊天 ----------------
    if action == "pkn.hello":
        cid = store.get_or_create_pkn(user["id"])
        if cid is None:
            return [{"type": "error", "error": "这个账号没有可用的 WSS 聊天"}]
        if conn is not None:
            conn.pkn_conv = cid
        conv = store.conv_row(cid)
        peer = None
        if conv is not None and conv["kind"] == "direct":
            pid = store._peer_of_direct(conv, user["id"])
            peer = store.user_brief(db.qone("SELECT * FROM users WHERE id = ?", (pid,)))
        title = (conv["title"] if conv is not None else "") or ""
        if not title:
            title = ("与 %s 的聊天" % (peer["display_name"] if peer else "主账号"))
        return [{
            "type": "pkn.welcome",
            "version": 1,
            "chat": {"conv_id": cid, "kind": conv["kind"] if conv else "pkn", "title": title},
            "user": store.user_brief(user),
            "peer": peer,
            "messages": store.recent_messages(cid, 200, user["id"]),
        }]

    if action == "pkn.send":
        cid = getattr(conn, "pkn_conv", None) if conn is not None else None
        if cid is None:
            return [{"type": "error", "error": "先发 pkn.hello 绑定专属聊天"}]
        body = str(msg.get("text") or "").strip()
        media_id = int(msg.get("media_id") or 0)
        quote_id = int(msg.get("quote_id") or 0)
        if not body and not media_id:
            return [{"type": "error", "error": "消息为空"}]
        if media_id and db.qone("SELECT 1 FROM media WHERE id = ?", (media_id,)) is None:
            return [{"type": "error", "error": "图片不存在"}]
        m = store.append_message(cid, user["id"], body,
                                 "image" if media_id else "text", media_id or None,
                                 quote_id or None)
        if m is None:
            return [{"type": "error", "error": "消息为空"}]
        store.mark_read(cid, user["id"], m["id"])
        # 广播会把这条包成 pkn.message 推回自己，所以不再单独回执
        HUB.push_conversation(store.member_ids(cid), {"type": "message", "conv_id": cid, "message": m})
        push_notify(cid, m)
        return []

    if action == "pkn.history":
        cid = getattr(conn, "pkn_conv", None) if conn is not None else None
        if cid is None:
            return [{"type": "error", "error": "先发 pkn.hello 绑定专属聊天"}]
        try:
            limit = int(msg.get("limit") or 100)
        except Exception:
            limit = 100
        limit = max(1, min(200, limit))
        return [{"type": "pkn.history", "messages": store.recent_messages(cid, limit, user["id"])}]

    if action == "pkn.bye":
        if conn is not None:
            conn.pkn_conv = None
        return [{"type": "pkn.bye"}]

    if action == "ping":
        return [{"type": "pong", "t": int(time.time())}]

    if action == "list":
        return [{"type": "conversations", "conversations": store.list_conversations(user["id"])}]

    if action == "history":
        cid = int(msg.get("conv_id") or 0)
        if not store.is_member(cid, user["id"]):
            return [{"type": "error", "error": "你不在这个会话里"}]
        return [{"type": "history", "conv_id": cid,
                 "messages": store.recent_messages(cid, None, user["id"])}]

    if action == "send":
        cid = int(msg.get("conv_id") or 0)
        body = str(msg.get("text") or "").strip()
        media_id = int(msg.get("media_id") or 0)
        quote_id = int(msg.get("quote_id") or 0)
        if not body and not media_id:
            return [{"type": "error", "error": "消息为空"}]
        if not store.is_member(cid, user["id"]):
            return [{"type": "error", "error": "你不在这个会话里"}]
        conv = store.conv_row(cid)
        if conv["kind"] == "direct":
            peer_id = store._peer_of_direct(conv, user["id"])
            if peer_id is not None and store.blocked_by(peer_id, user["id"]):
                return [{"type": "error", "error": "对方已把你加入黑名单"}]
        if media_id and db.qone("SELECT 1 FROM media WHERE id = ?", (media_id,)) is None:
            return [{"type": "error", "error": "图片不存在"}]
        m = store.append_message(cid, user["id"], body,
                                 "image" if media_id else "text", media_id or None,
                                 quote_id or None)
        if m is None:
            return [{"type": "error", "error": "消息为空"}]
        store.mark_read(cid, user["id"], m["id"])
        # 广播会把这一帧推回给自己，所以不再额外回 sent，避免客户端收到两帧
        HUB.push_conversation(store.member_ids(cid), {"type": "message", "conv_id": cid, "message": m})
        push_notify(cid, m)
        return []

    if action in ("typing", "pkn.typing"):
        if action == "pkn.typing":
            cid = getattr(conn, "pkn_conv", None) if conn is not None else None
        else:
            cid = int(msg.get("conv_id") or 0)
        if cid is None or not store.is_member(cid, user["id"]):
            return []
        conv = store.conv_row(cid)
        if conv is None or conv["kind"] not in ("direct", "pkn"):
            return []
        HUB.push_conversation(
            [u for u in store.member_ids(cid) if u != int(user["id"])],
            {"type": "typing", "conv_id": int(cid), "user_id": int(user["id"]),
             "active": bool(msg.get("active", True))},
        )
        return []

    if action in ("recall", "pkn.recall"):
        mid = int(msg.get("message_id") or 0)
        if not mid:
            return [{"type": "error", "error": "缺少 message_id"}]
        fine, err, event = store.recall_message(mid, user)
        if not fine:
            return [{"type": "error", "error": err}]
        if event:
            payload = {"type": "message_recalled"}
            payload.update(event)
            HUB.push_conversation(store.member_ids(event["conv_id"]), payload)
        return []

    if action == "open_dm":
        peer = int(msg.get("peer_id") or 0)
        allowed, why = store.can_direct_message(user, peer)
        if not allowed:
            return [{"type": "error", "error": why}]
        cid = store.get_or_create_dm(user["id"], peer)
        return [{"type": "conversation", "conv_id": cid}]

    return [{"type": "error", "error": "未知的 action: %s" % action}]


class Server(ThreadingHTTPServer):
    daemon_threads = True
    allow_reuse_address = True


def serve():
    db.init_db()
    srv = Server((config.HOST, config.PORT), Handler)
    print("kokona-chat listening on http://%s:%d%s" % (config.HOST, config.PORT, config.BASE or "/"), flush=True)
    try:
        srv.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        srv.server_close()
