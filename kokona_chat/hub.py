"""连接中心：SSE（网页）与 WebSocket（子账号/程序）共用一套广播。"""

import json
import queue
import threading


class Hub:
    def __init__(self):
        self._lock = threading.Lock()
        self._sse = {}      # user_id -> set[Queue]
        self._ws = {}       # user_id -> set[WSConn]

    # ---------------- SSE ----------------

    def sse_attach(self, user_id):
        q = queue.Queue(maxsize=200)
        with self._lock:
            self._sse.setdefault(int(user_id), set()).add(q)
        return q

    def sse_detach(self, user_id, q):
        with self._lock:
            bucket = self._sse.get(int(user_id))
            if bucket is not None:
                bucket.discard(q)
                if not bucket:
                    self._sse.pop(int(user_id), None)

    # ---------------- WebSocket ----------------

    def ws_attach(self, user_id, conn):
        with self._lock:
            self._ws.setdefault(int(user_id), set()).add(conn)

    def ws_detach(self, user_id, conn):
        with self._lock:
            bucket = self._ws.get(int(user_id))
            if bucket is not None:
                bucket.discard(conn)
                if not bucket:
                    self._ws.pop(int(user_id), None)

    def online_users(self):
        with self._lock:
            return sorted(set(self._sse) | set(self._ws))

    # ---------------- 广播 ----------------

    def _deliver(self, user_ids, payload):
        text = json.dumps(payload, ensure_ascii=False)
        dead_sse = []
        dead_ws = []
        with self._lock:
            for uid in user_ids:
                for q in self._sse.get(int(uid), set()):
                    try:
                        q.put_nowait(text)
                    except queue.Full:
                        dead_sse.append((uid, q))
                for conn in self._ws.get(int(uid), set()):
                    dead_ws.append((uid, conn))
        for uid, q in dead_sse:
            self.sse_detach(uid, q)
        for uid, conn in dead_ws:
            try:
                pkn = getattr(conn, "pkn_conv", None)
                if pkn is None:
                    conn.send_json(text)
                else:
                    # PKN 连接只关心自己那条专属聊天，帧名换成 pkn.*
                    frame = _pkn_frame(payload, int(pkn))
                    if frame is not None:
                        conn.send_json(json.dumps(frame, ensure_ascii=False))
            except Exception:
                conn.alive = False
            if not conn.alive:
                self.ws_detach(uid, conn)
        return len(dead_ws)

    def push_conversation(self, user_ids, payload):
        """把一条事件推给这些用户。"""
        return self._deliver(user_ids, payload)

    def push_user(self, user_id, payload):
        return self._deliver([int(user_id)], payload)


def _pkn_frame(payload, conv_id):
    """把通用事件翻译成 PKN 连接能收的帧；与它无关的返回 None。"""
    kind = payload.get("type")
    cid = int(payload.get("conv_id") or 0)
    if kind == "message" and cid == conv_id:
        return {"type": "pkn.message", "message": payload.get("message")}
    if kind == "typing" and cid == conv_id:
        return {"type": "pkn.typing", "user_id": payload.get("user_id"),
                "active": bool(payload.get("active"))}
    if kind == "message_recalled" and cid == conv_id:
        return {
            "type": "pkn.message_recalled",
            "message_id": payload.get("message_id"),
            "by": payload.get("by"),
            "sender_id": payload.get("sender_id"),
            "scope": payload.get("scope"),
        }
    if kind == "conversation_removed" and cid == conv_id:
        return {"type": "pkn.closed"}
    return None
