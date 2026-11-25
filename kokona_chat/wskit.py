"""最小 WebSocket（RFC 6455）服务端实现，零依赖，给子账号/程序端用。"""

import base64
import hashlib
import struct

WS_GUID = "258EAFA5-E914-47DA-95CA-C5AB0DC85B11"

OP_TEXT = 0x1
OP_BIN = 0x2
OP_CLOSE = 0x8
OP_PING = 0x9
OP_PONG = 0xA


def accept_key(key):
    """算 Sec-WebSocket-Accept。"""
    digest = hashlib.sha1((str(key) + WS_GUID).encode("ascii")).digest()
    return base64.b64encode(digest).decode("ascii")


def recv_exact(rfile, n):
    buf = b""
    while len(buf) < n:
        chunk = rfile.read(n - len(buf))
        if not chunk:
            raise ConnectionError("连接已断开")
        buf += chunk
    return buf


def read_frame(rfile, max_size=4 << 20):
    """读一帧，返回 (fin, opcode, payload)。"""
    b1, b2 = recv_exact(rfile, 2)
    fin = bool(b1 & 0x80)
    opcode = b1 & 0x0F
    masked = bool(b2 & 0x80)
    length = b2 & 0x7F
    if length == 126:
        length = struct.unpack(">H", recv_exact(rfile, 2))[0]
    elif length == 127:
        length = struct.unpack(">Q", recv_exact(rfile, 8))[0]
    if length > max_size:
        raise ConnectionError("帧太大")
    mask = recv_exact(rfile, 4) if masked else b""
    payload = recv_exact(rfile, length) if length else b""
    if mask:
        payload = bytes(payload[i] ^ mask[i % 4] for i in range(len(payload)))
    return fin, opcode, payload


def encode_frame(opcode, payload):
    """服务端发出的帧不加掩码。"""
    if isinstance(payload, str):
        payload = payload.encode("utf-8")
    header = bytearray([0x80 | opcode])
    n = len(payload)
    if n < 126:
        header.append(n)
    elif n < 65536:
        header.append(126)
        header += struct.pack(">H", n)
    else:
        header.append(127)
        header += struct.pack(">Q", n)
    return bytes(header) + payload


class WSConn:
    """一条已升级的连接；发送加锁，避免多线程字节交错。"""

    def __init__(self, sock, user):
        import threading

        self.sock = sock
        self.user = user
        self.lock = threading.Lock()
        self.alive = True
        # 非 None 表示这条连接已经通过 pkn.hello 绑定到专属聊天，
        # 之后只收这个会话的消息，帧类型统一包成 pkn.*
        self.pkn_conv = None

    def send(self, opcode, payload):
        if not self.alive:
            return
        try:
            with self.lock:
                self.sock.sendall(encode_frame(opcode, payload))
        except Exception:
            self.alive = False

    def send_json(self, text):
        self.send(OP_TEXT, text)

    def close(self):
        self.alive = False
        try:
            self.send(OP_CLOSE, b"")
        except Exception:
            pass
