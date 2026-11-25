"""业务数据操作：会话、消息、好友、黑名单、公告。

约定：
- 云端每个会话只保留最近 config.HISTORY_MAX 条（默认 100），更早的直接删。
- 私聊会话靠 conversations.dm_key（"小id:大id"）保证唯一。
- 子账号（is_sub=1）只能跟自己的主账号私聊。
"""

from . import config, db


# ---------------------------------------------------------------- 权限

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
        "INSERT INTO conversations (kind, title, dm_key, created_by, created_at, last_at) "
        "VALUES ('direct', '', ?, ?, ?, ?)",
        (key, int(a), t, t),
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
    cur = db.run(
        "INSERT INTO conversations (kind, title, created_by, created_at, last_at) "
        "VALUES ('group', ?, ?, ?, ?)",
        (str(title or "新群聊").strip()[:60] or "新群聊", int(owner_id), t, t),
    )
    cid = int(cur.lastrowid)
    ids = {int(owner_id)} | {int(x) for x in (member_ids or [])}
    for uid in ids:
        db.run(
            "INSERT OR IGNORE INTO conversation_members (conv_id, user_id, joined_at) VALUES (?, ?, ?)",
            (cid, uid, t),
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


def members(conv_id):
    return db.qall(
        "SELECT u.*, m.alias AS alias FROM conversation_members m "
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

def append_message(conv_id, sender_id, body):
    body = str(body or "").strip()
    if not body:
        return None
    body = body[:4000]
    t = db.now()
    cur = db.run(
        "INSERT INTO messages (conv_id, sender_id, body, created_at) VALUES (?, ?, ?, ?)",
        (int(conv_id), None if sender_id is None else int(sender_id), body, t),
    )
    mid = int(cur.lastrowid)
    db.run("UPDATE conversations SET last_at = ? WHERE id = ?", (t, int(conv_id)))
    _trim(conv_id)
    sender = db.qone("SELECT * FROM users WHERE id = ?", (int(sender_id),)) if sender_id else None
    return {
        "id": mid,
        "conv_id": int(conv_id),
        "sender_id": int(sender_id) if sender_id else 0,
        "sender": user_brief(sender),
        "body": body,
        "created_at": t,
    }


def _trim(conv_id):
    """云端只留最近 N 条；更早的直接删。"""
    cut = db.qone(
        "SELECT id FROM messages WHERE conv_id = ? ORDER BY id DESC LIMIT 1 OFFSET ?",
        (int(conv_id), int(config.HISTORY_MAX)),
    )
    if cut is not None:
        db.run("DELETE FROM messages WHERE conv_id = ? AND id <= ?", (int(conv_id), int(cut["id"])))


def recent_messages(conv_id, limit=None):
    limit = int(limit or config.HISTORY_MAX)
    rows = db.qall(
        "SELECT m.*, u.username, u.display_name, u.avatar, u.cover, u.is_sub, u.role "
        "FROM messages m LEFT JOIN users u ON u.id = m.sender_id "
        "WHERE m.conv_id = ? ORDER BY m.id DESC LIMIT ?",
        (int(conv_id), limit),
    )
    items = []
    for r in reversed(rows):
        items.append({
            "id": r["id"],
            "conv_id": r["conv_id"],
            "sender_id": r["sender_id"] or 0,
            "body": r["body"],
            "created_at": r["created_at"],
            "sender": user_brief(r) if r["username"] else None,
        })
    return items


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

PKN_TITLE = "我的 WSS 聊天"


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
        "INSERT INTO conversations (kind, title, dm_key, created_by, created_at, last_at) "
        "VALUES ('pkn', ?, ?, ?, ?, ?)",
        (PKN_TITLE, key, int(user_id), t, t),
    )
    cid = int(cur.lastrowid)
    db.run(
        "INSERT OR IGNORE INTO conversation_members (conv_id, user_id, joined_at) VALUES (?, ?, ?)",
        (cid, int(user_id), t),
    )
    return cid
