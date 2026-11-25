"""业务数据操作：会话、消息、好友、黑名单、公告。

约定：
- 云端每个会话只保留最近 config.HISTORY_MAX 条（默认 100），更早的直接删。
- 私聊会话靠 conversations.dm_key（"小id:大id"）保证唯一。
- 子账号（is_sub=1）只能跟自己的主账号私聊。
"""

from . import config, db


# ---------------------------------------------------------------- 权限

# 云端留存条数：私聊/PKN 200，管理员建的群 300，可在建群时写进 history_max
HISTORY_DEFAULT = 200
HISTORY_ADMIN_GROUP = 300
RECALL_WINDOW = 5 * 60          # 本人撤回时限（秒）


def _row(row):
    return dict(row) if row is not None else None


def _opt(row, key):
    """sqlite3.Row 缺列会抛 IndexError；老库/老查询里没有的字段统一当空串。"""
    try:
        return row[key] or ""
    except (IndexError, KeyError):
        return ""


def user_brief(row):
    if row is None:
        return None
    return {
        "id": row["id"],
        "username": row["username"],
        "display_name": row["display_name"] or row["username"],
        "avatar": row["avatar"] or "",
        "cover": _opt(row, "cover"),
        "is_sub": int(row["is_sub"] or 0),
        "role": row["role"],
    }


def is_admin(user):
    return user is not None and user["role"] == "admin"


def is_sub(user):
    return user is not None and int(user["is_sub"] or 0) == 1


# ---------------------------------------------------------------- 会话

def dm_key(a, b):
    lo, hi = sorted((int(a), int(b)))
    return "%d:%d" % (lo, hi)


def get_or_create_dm(a, b):
    key = dm_key(a, b)
    row = db.qone("SELECT id FROM conversations WHERE dm_key = ?", (key,))
    if row is not None:
        return int(row["id"])
    t = db.now()
    cur = db.run(
        "INSERT INTO conversations (kind, title, dm_key, created_by, history_max, created_at, last_at) "
        "VALUES ('direct', '', ?, ?, ?, ?, ?)",
        (key, int(a), HISTORY_DEFAULT, t, t),
    )
    cid = int(cur.lastrowid)
    for uid in (int(a), int(b)):
        db.run(
            "INSERT OR IGNORE INTO conversation_members (conv_id, user_id, joined_at) VALUES (?, ?, ?)",
            (cid, uid, t),
        )
    return cid


def create_group(owner_id, title, member_ids):
    t = db.now()
    owner = db.qone("SELECT role FROM users WHERE id = ?", (int(owner_id),))
    limit = HISTORY_ADMIN_GROUP if (owner is not None and owner["role"] == "admin") else HISTORY_DEFAULT
    cur = db.run(
        "INSERT INTO conversations (kind, title, created_by, history_max, created_at, last_at) "
        "VALUES ('group', ?, ?, ?, ?, ?)",
        (str(title or "新群聊").strip()[:60] or "新群聊", int(owner_id), limit, t, t),
    )
    cid = int(cur.lastrowid)
    ids = {int(owner_id)} | {int(x) for x in (member_ids or [])}
    for uid in ids:
        role = "owner" if uid == int(owner_id) else "member"
        db.run(
            "INSERT OR IGNORE INTO conversation_members (conv_id, user_id, role, joined_at) VALUES (?, ?, ?, ?)",
            (cid, uid, role, t),
        )
    return cid


def conv_row(conv_id):
    return db.qone("SELECT * FROM conversations WHERE id = ?", (int(conv_id),))


def is_member(conv_id, user_id):
    if user_id is None:
        return False
    row = db.qone(
        "SELECT 1 FROM conversation_members WHERE conv_id = ? AND user_id = ?",
        (int(conv_id), int(user_id)),
    )
    return row is not None


def history_limit(conv):
    """这个会话云端留多少条。0 或缺失时按默认。"""
    if conv is None:
        return HISTORY_DEFAULT
    try:
        keep = int(conv["history_max"] or 0)
    except (IndexError, KeyError, TypeError):
        keep = 0
    return keep if keep > 0 else HISTORY_DEFAULT


def member_role(conv_id, user_id):
    row = db.qone(
        "SELECT role FROM conversation_members WHERE conv_id = ? AND user_id = ?",
        (int(conv_id), int(user_id)),
    )
    return (row["role"] if row is not None else "") or "member"


def is_owner(conv, user_id):
    return conv is not None and int(conv["created_by"] or 0) == int(user_id)


def can_moderate(conv, user_id):
    """群主 / 群管理员。只对群有效，跟网站 admin 无关。"""
    if conv is None or conv["kind"] != "group":
        return False
    return member_role(conv["id"], user_id) in ("owner", "admin")


def can_edit_group(conv, user_id):
    if conv is None or conv["kind"] != "group":
        return False
    return member_role(conv["id"], user_id) in ("owner", "admin")


def set_member_role(conv_id, user_id, role):
    if role not in ("owner", "admin", "member"):
        return False
    db.run(
        "UPDATE conversation_members SET role = ? WHERE conv_id = ? AND user_id = ?",
        (role, int(conv_id), int(user_id)),
    )
    return True


def set_notice(conv_id, text):
    db.run("UPDATE conversations SET notice = ? WHERE id = ?", (str(text or "")[:1000], int(conv_id)))


def set_history_max(conv_id, keep):
    db.run("UPDATE conversations SET history_max = ? WHERE id = ?", (int(keep), int(conv_id)))


def members(conv_id):
    return db.qall(
        "SELECT u.*, m.alias AS alias, m.role AS member_role FROM conversation_members m "
        "JOIN users u ON u.id = m.user_id WHERE m.conv_id = ? ORDER BY u.id",
        (int(conv_id),),
    )


def member_ids(conv_id):
    return [int(r["user_id"]) for r in db.qall(
        "SELECT user_id FROM conversation_members WHERE conv_id = ?", (int(conv_id),)
    )]


def add_member(conv_id, user_id):
    db.run(
        "INSERT OR IGNORE INTO conversation_members (conv_id, user_id, joined_at) VALUES (?, ?, ?)",
        (int(conv_id), int(user_id), db.now()),
    )


def remove_member(conv_id, user_id):
    db.run(
        "DELETE FROM conversation_members WHERE conv_id = ? AND user_id = ?",
        (int(conv_id), int(user_id)),
    )


def set_conv_avatar(conv_id, stored):
    db.run("UPDATE conversations SET avatar = ? WHERE id = ?", (stored, int(conv_id)))


def rename_conv(conv_id, title):
    db.run(
        "UPDATE conversations SET title = ? WHERE id = ?",
        (str(title or "").strip()[:60], int(conv_id)),
    )


def set_alias(conv_id, user_id, alias):
    db.run(
        "UPDATE conversation_members SET alias = ? WHERE conv_id = ? AND user_id = ?",
        (str(alias or "").strip()[:40], int(conv_id), int(user_id)),
    )


def _peer_of_direct(conv, user_id):
    """私聊里的对方 user id。"""
    for uid in member_ids(conv["id"]):
        if uid != int(user_id):
            return uid
    return None


def list_conversations(user_id):
    """返回这个用户看到的会话列表，按最近活跃倒序。"""
    rows = db.qall(
        "SELECT c.*, m.alias AS alias FROM conversations c "
        "JOIN conversation_members m ON m.conv_id = c.id "
        "WHERE m.user_id = ? ORDER BY c.last_at DESC, c.id DESC",
        (int(user_id),),
    )
    out = []
    for conv in rows:
        item = {
            "id": conv["id"],
            "kind": conv["kind"],
            "title": conv["title"],
            "alias": conv["alias"] or "",
            "avatar": conv["avatar"] or "",
            "notice": _opt(conv, "notice"),
            "history_max": history_limit(conv),
            "my_role": member_role(conv["id"], user_id),
            "created_by": conv["created_by"],
            "last_at": conv["last_at"],
        }
        last = db.qone(
            "SELECT id, sender_id, body, created_at FROM messages "
            "WHERE conv_id = ? ORDER BY id DESC LIMIT 1",
            (conv["id"],),
        )
        item["last"] = _row(last)
        # 空的旧频道只是占位，别在列表里占位子
        if conv["kind"] == "legacy" and last is None:
            continue
        if conv["kind"] == "direct":
            peer_id = _peer_of_direct(conv, user_id)
            peer = db.qone("SELECT * FROM users WHERE id = ?", (peer_id,)) if peer_id else None
            item["peer"] = user_brief(peer)
            item["title"] = (conv["alias"] or "").strip() or (
                (peer["display_name"] or peer["username"]) if peer else "未知用户"
            )
        else:
            names = [r["display_name"] or r["username"] for r in members(conv["id"])]
            item["member_count"] = len(names)
            item["member_names"] = names[:4]
        item["unread"] = _unread_count(conv["id"], user_id, item["last"])
        out.append(item)
    return out


def conv_notify_view(conv, user_id):
    """通知用的标题和头像：私聊取对方（带备注），群聊取群名/群头像。"""
    if conv["kind"] == "direct":
        peer_id = _peer_of_direct(conv, user_id)
        peer = db.qone("SELECT * FROM users WHERE id = ?", (peer_id,)) if peer_id else None
        row = db.qone(
            "SELECT alias FROM conversation_members WHERE conv_id = ? AND user_id = ?",
            (int(conv["id"]), int(user_id)),
        )
        alias = (row["alias"] if row is not None else "") or ""
        title = alias.strip() or ((peer["display_name"] or peer["username"]) if peer else "新消息")
        return title, (peer["avatar"] if peer is not None else "") or ""
    return (conv["title"] or "新消息"), (conv["avatar"] or "")


def _unread_count(conv_id, user_id, last):
    if not last:
        return 0
    st = db.qone(
        "SELECT last_read_id FROM read_state WHERE conv_id = ? AND user_id = ?",
        (int(conv_id), int(user_id)),
    )
    last_read = int(st["last_read_id"]) if st else 0
    if int(last["id"]) <= last_read:
        return 0
    row = db.qone(
        "SELECT COUNT(*) AS n FROM messages WHERE conv_id = ? AND id > ? AND sender_id != ?",
        (int(conv_id), last_read, int(user_id)),
    )
    return int(row["n"]) if row else 0


def mark_read(conv_id, user_id, last_id=None):
    if last_id is None:
        row = db.qone("SELECT MAX(id) AS m FROM messages WHERE conv_id = ?", (int(conv_id),))
        last_id = int(row["m"] or 0) if row else 0
    db.run(
        "INSERT INTO read_state (conv_id, user_id, last_read_id) VALUES (?, ?, ?) "
        "ON CONFLICT(conv_id, user_id) DO UPDATE SET last_read_id = MAX(last_read_id, excluded.last_read_id)",
        (int(conv_id), int(user_id), int(last_id)),
    )


# ---------------------------------------------------------------- 消息

def media_url(hash_value):
    return "%s/m/%s.webp" % (config.SITE_URL, hash_value)


def media_brief(row):
    if row is None:
        return None
    return {
        "id": row["id"],
        "url": media_url(row["hash"]),
        "w": row["w"],
        "h": row["h"],
        "bytes": row["bytes"],
    }


def upsert_media(hash_value, size, width, height):
    """按内容哈希去重：同一张图全服只存一份。"""
    row = db.qone("SELECT * FROM media WHERE hash = ?", (hash_value,))
    if row is not None:
        return row
    cur = db.run(
        "INSERT INTO media (hash, bytes, w, h, created_at) VALUES (?, ?, ?, ?, ?)",
        (hash_value, int(size), int(width or 0), int(height or 0), db.now()),
    )
    return db.qone("SELECT * FROM media WHERE id = ?", (int(cur.lastrowid),))


def message_item(r):
    """统一的消息形状：撤回后只留占位，不带正文和图片。"""
    recalled = int(_opt(r, "recalled") or 0) == 1
    item = {
        "id": r["id"],
        "conv_id": r["conv_id"],
        "sender_id": r["sender_id"] or 0,
        "kind": "text" if recalled else (_opt(r, "kind") or "text"),
        "body": "" if recalled else (r["body"] or ""),
        "media": None,
        "recalled": 1 if recalled else 0,
        "recall_by": int(_opt(r, "recall_by") or 0),
        "created_at": r["created_at"],
        "sender": user_brief(r) if "username" in r.keys() and r["username"] else None,
    }
    if not recalled and _opt(r, "media_id"):
        item["media"] = media_brief(db.qone("SELECT * FROM media WHERE id = ?", (int(r["media_id"]),)))
    return item


def append_message(conv_id, sender_id, body, kind="text", media_id=None):
    body = str(body or "").strip()[:4000]
    if kind == "text" and not body:
        return None
    if kind == "image" and not media_id:
        return None
    t = db.now()
    cur = db.run(
        "INSERT INTO messages (conv_id, sender_id, body, kind, media_id, created_at) "
        "VALUES (?, ?, ?, ?, ?, ?)",
        (int(conv_id), None if sender_id is None else int(sender_id), body,
         "image" if kind == "image" else "text",
         int(media_id) if media_id else None, t),
    )
    mid = int(cur.lastrowid)
    db.run("UPDATE conversations SET last_at = ? WHERE id = ?", (t, int(conv_id)))
    _trim(conv_id)
    row = db.qone(
        "SELECT m.*, u.username, u.display_name, u.avatar, u.cover, u.is_sub, u.role "
        "FROM messages m LEFT JOIN users u ON u.id = m.sender_id WHERE m.id = ?",
        (mid,),
    )
    return message_item(row) if row is not None else None


def recall_message(msg_id, user):
    """撤回：本人 5 分钟内；群主/群管理员对本群不限时。返回 (ok, error, event)。"""
    row = db.qone("SELECT * FROM messages WHERE id = ?", (int(msg_id),))
    if row is None:
        return False, "消息不存在", None
    if int(_opt(row, "recalled") or 0) == 1:
        return True, "", None
    conv = conv_row(row["conv_id"])
    mine = int(row["sender_id"] or 0) == int(user["id"])
    mod = can_moderate(conv, user["id"])
    if mine:
        if not mod and db.now() - int(row["created_at"]) > RECALL_WINDOW:
            return False, "超过 5 分钟，不能撤回", None
        scope = "self"
    elif mod:
        scope = "admin"
    else:
        return False, "没有权限撤回这条消息", None
    db.run("UPDATE messages SET recalled = 1, recall_by = ? WHERE id = ?", (int(user["id"]), int(msg_id)))
    return True, "", {
        "message_id": int(msg_id),
        "conv_id": int(row["conv_id"]),
        "by": int(user["id"]),
        "sender_id": int(row["sender_id"] or 0),
        "scope": scope,
    }


def _trim(conv_id):
    """云端只留这个会话的 N 条；更早的直接删。"""
    keep = history_limit(conv_row(conv_id))
    cut = db.qone(
        "SELECT id FROM messages WHERE conv_id = ? ORDER BY id DESC LIMIT 1 OFFSET ?",
        (int(conv_id), int(keep)),
    )
    if cut is not None:
        db.run("DELETE FROM messages WHERE conv_id = ? AND id <= ?", (int(conv_id), int(cut["id"])))


def recent_messages(conv_id, limit=None, viewer_id=None):
    conv = conv_row(conv_id)
    limit = int(limit or history_limit(conv))
    if viewer_id:
        rows = db.qall(
            "SELECT m.*, u.username, u.display_name, u.avatar, u.cover, u.is_sub, u.role "
            "FROM messages m LEFT JOIN users u ON u.id = m.sender_id "
            "WHERE m.conv_id = ? AND NOT EXISTS "
            "  (SELECT 1 FROM msg_hidden h WHERE h.msg_id = m.id AND h.user_id = ?) "
            "ORDER BY m.id DESC LIMIT ?",
            (int(conv_id), int(viewer_id), limit),
        )
    else:
        rows = db.qall(
            "SELECT m.*, u.username, u.display_name, u.avatar, u.cover, u.is_sub, u.role "
            "FROM messages m LEFT JOIN users u ON u.id = m.sender_id "
            "WHERE m.conv_id = ? ORDER BY m.id DESC LIMIT ?",
            (int(conv_id), limit),
        )
    return [message_item(r) for r in reversed(rows)]


def hide_message(user_id, msg_id):
    """本地删除：只对这个人隐藏。"""
    row = db.qone("SELECT conv_id FROM messages WHERE id = ?", (int(msg_id),))
    if row is None:
        return False
    if not is_member(row["conv_id"], user_id):
        return False
    db.run("INSERT OR IGNORE INTO msg_hidden (user_id, msg_id) VALUES (?, ?)", (int(user_id), int(msg_id)))
    return True


# ---------------------------------------------------------------- 表情包

STICKER_LIMIT = 122


def stickers_of(user_id):
    rows = db.qall(
        "SELECT s.id AS sid, m.* FROM stickers s JOIN media m ON m.id = s.media_id "
        "WHERE s.user_id = ? ORDER BY s.id DESC",
        (int(user_id),),
    )
    out = []
    for r in rows:
        item = media_brief(r)
        item["sticker_id"] = r["sid"]
        out.append(item)
    return out


def add_sticker(user_id, media_id):
    db.run(
        "INSERT OR IGNORE INTO stickers (user_id, media_id, created_at) VALUES (?, ?, ?)",
        (int(user_id), int(media_id), db.now()),
    )
    row = db.qone("SELECT COUNT(*) AS n FROM stickers WHERE user_id = ?", (int(user_id),))
    return int(row["n"]) if row else 0


def del_sticker(user_id, sticker_id):
    db.run("DELETE FROM stickers WHERE user_id = ? AND id = ?", (int(user_id), int(sticker_id)))
    return True


# ---------------------------------------------------------------- 好友 / 黑名单

def friends_of(user_id):
    rows = db.qall(
        "SELECT u.* FROM friends f JOIN users u ON u.id = f.peer_id "
        "WHERE f.user_id = ? ORDER BY u.username",
        (int(user_id),),
    )
    return [user_brief(r) for r in rows]


def are_friends(a, b):
    row = db.qone(
        "SELECT 1 FROM friends WHERE user_id = ? AND peer_id = ?",
        (int(a), int(b)),
    )
    return row is not None


def add_friend(a, b):
    if int(a) == int(b):
        return
    t = db.now()
    db.run("INSERT OR IGNORE INTO friends (user_id, peer_id, created_at) VALUES (?, ?, ?)", (int(a), int(b), t))
    db.run("INSERT OR IGNORE INTO friends (user_id, peer_id, created_at) VALUES (?, ?, ?)", (int(b), int(a), t))


def remove_friend(a, b):
    db.run("DELETE FROM friends WHERE user_id = ? AND peer_id = ?", (int(a), int(b)))
    db.run("DELETE FROM friends WHERE user_id = ? AND peer_id = ?", (int(b), int(a)))


def blocked_by(owner, peer):
    """owner 是否拉黑了 peer。"""
    row = db.qone(
        "SELECT 1 FROM blocks WHERE user_id = ? AND peer_id = ?", (int(owner), int(peer))
    )
    return row is not None


def block(user_id, peer_id):
    db.run(
        "INSERT OR IGNORE INTO blocks (user_id, peer_id, created_at) VALUES (?, ?, ?)",
        (int(user_id), int(peer_id), db.now()),
    )


def unblock(user_id, peer_id):
    db.run("DELETE FROM blocks WHERE user_id = ? AND peer_id = ?", (int(user_id), int(peer_id)))


def blocks_of(user_id):
    rows = db.qall(
        "SELECT u.* FROM blocks b JOIN users u ON u.id = b.peer_id WHERE b.user_id = ?",
        (int(user_id),),
    )
    return [user_brief(r) for r in rows]


def can_direct_message(sender, peer_id):
    """能不能给这个人发私聊。返回 (ok, 原因)。"""
    if sender is None or peer_id is None:
        return False, "用户不存在"
    if int(sender["id"]) == int(peer_id):
        return False, "不能和自己聊天"
    peer = db.qone("SELECT * FROM users WHERE id = ?", (int(peer_id),))
    if peer is None:
        return False, "用户不存在"
    if peer["status"] == "banned":
        return False, "对方账号已被封禁"
    # 子账号：只能和主账号对话
    if is_sub(sender):
        if int(peer["id"]) != int(sender["parent_id"] or 0):
            return False, "子账号只能和主账号对话"
        return True, ""
    if is_sub(peer):
        if int(peer["parent_id"] or 0) != int(sender["id"]):
            return False, "那是别人的子账号"
        return True, ""
    if blocked_by(peer["id"], sender["id"]):
        return False, "对方已把你加入黑名单"
    if blocked_by(sender["id"], peer["id"]):
        return False, "你已把对方加入黑名单，先解除"
    if not are_friends(sender["id"], peer["id"]):
        return False, "先加对方为好友才能聊天"
    return True, ""


# ---------------------------------------------------------------- 公告

def create_announcement(author_id, title, body):
    cur = db.run(
        "INSERT INTO announcements (author_id, title, body, created_at) VALUES (?, ?, ?, ?)",
        (int(author_id), str(title or "").strip()[:80], str(body or "").strip()[:4000], db.now()),
    )
    return int(cur.lastrowid)


def list_announcements(user_id, limit=30):
    rows = db.qall(
        "SELECT a.*, u.username, u.display_name FROM announcements a "
        "LEFT JOIN users u ON u.id = a.author_id ORDER BY a.id DESC LIMIT ?",
        (int(limit),),
    )
    out = []
    for r in rows:
        read = db.qone(
            "SELECT read_at FROM announcement_reads WHERE announcement_id = ? AND user_id = ?",
            (r["id"], int(user_id)),
        )
        out.append({
            "id": r["id"],
            "title": r["title"],
            "body": r["body"],
            "created_at": r["created_at"],
            "author": r["display_name"] or r["username"] or "管理员",
            "read": read is not None,
        })
    return out


def mark_announcement_read(aid, user_id):
    db.run(
        "INSERT OR IGNORE INTO announcement_reads (announcement_id, user_id, read_at) VALUES (?, ?, ?)",
        (int(aid), int(user_id), db.now()),
    )


def unread_announcements(user_id):
    rows = db.qall(
        "SELECT a.* FROM announcements a "
        "WHERE NOT EXISTS (SELECT 1 FROM announcement_reads r "
        "                  WHERE r.announcement_id = a.id AND r.user_id = ?) "
        "ORDER BY a.id DESC LIMIT 5",
        (int(user_id),),
    )
    return [dict(r) for r in rows]


# ---------------------------------------------------------------- PKN 专属聊天

PKN_TITLE = "心夏"


def get_or_create_pkn(user_id):
    """每个账号一个专属 WSS 聊天。

    - 主账号：单人会话（kind=pkn），程序端和网页端都在这里说话。
    - 子账号：直接复用它与主账号的那条私聊，规则不变（子账号只能和主账号聊）。

    dm_key 复用为 "pkn:<uid>"，靠唯一索引保证只建一次。
    """
    row = db.qone("SELECT * FROM users WHERE id = ?", (int(user_id),))
    if row is None:
        return None

    if int(row["is_sub"] or 0) == 1:
        parent = int(row["parent_id"] or 0)
        if parent == 0:
            return None
        return get_or_create_dm(parent, row["id"])

    key = "pkn:%d" % int(user_id)
    hit = db.qone("SELECT id FROM conversations WHERE dm_key = ?", (key,))
    if hit is not None:
        return int(hit["id"])

    # 老账号可能已经有一条「只有自己」的旧频道（频道一）。
    # 那本来就是他的专属聊天，直接接管，别再新建一条让人看到两个。
    adopt = db.qone(
        "SELECT c.id FROM conversations c "
        "JOIN conversation_members m ON m.conv_id = c.id "
        "WHERE m.user_id = ? AND c.kind = 'legacy' AND c.dm_key IS NULL "
        "  AND (SELECT COUNT(*) FROM conversation_members x WHERE x.conv_id = c.id) = 1 "
        "ORDER BY c.id LIMIT 1",
        (int(user_id),),
    )
    if adopt is not None:
        cid = int(adopt["id"])
        db.run(
            "UPDATE conversations SET kind = 'pkn', dm_key = ?, title = ? WHERE id = ?",
            (key, PKN_TITLE, cid),
        )
        return cid

    t = db.now()
    cur = db.run(
        "INSERT INTO conversations (kind, title, dm_key, created_by, history_max, created_at, last_at) "
        "VALUES ('pkn', ?, ?, ?, ?, ?, ?)",
        (PKN_TITLE, key, int(user_id), HISTORY_DEFAULT, t, t),
    )
    cid = int(cur.lastrowid)
    db.run(
        "INSERT OR IGNORE INTO conversation_members (conv_id, user_id, joined_at) VALUES (?, ?, ?)",
        (cid, int(user_id), t),
    )
    return cid
