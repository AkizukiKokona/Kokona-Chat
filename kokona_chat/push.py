"""浏览器 Web Push：VAPID 签名 + aes128gcm 加密，只用标准库和 cryptography。

为什么要自己写：pywebpush 会拖进一堆依赖，服务器上的 cryptography 3.3 已经够用，
协议本身也就两百行。密钥首次运行时生成，落在 data/vapid.json（600）。
"""

import base64
import json
import os
import struct
import threading
import time
from urllib import request as urlrequest
from urllib.parse import urlparse

from . import config, db

try:  # 没装 cryptography 就优雅降级，页面上的开关会自动隐藏
    from cryptography.hazmat.primitives import hashes, serialization
    from cryptography.hazmat.primitives.asymmetric import ec
    from cryptography.hazmat.primitives.asymmetric.utils import decode_dss_signature
    from cryptography.hazmat.primitives.ciphers.aead import AESGCM
    from cryptography.hazmat.primitives.kdf.hkdf import HKDF
    HAVE_CRYPTO = True
except Exception:  # noqa: BLE001
    HAVE_CRYPTO = False

# 同一会话 2 秒内的多条消息合成一条通知，避免连珠炮
MERGE_SECONDS = 2.0

_lock = threading.Lock()
_vapid = None
_pending = {}
_pend_lock = threading.Lock()


def _b64u(raw):
    return base64.urlsafe_b64encode(raw).rstrip(b"=").decode("ascii")


def _b64d(text):
    if isinstance(text, str):
        text = text.encode("ascii")
    return base64.urlsafe_b64decode(text + b"=" * (-len(text) % 4))


def _key_path():
    return os.path.join(config.DATA_DIR, "vapid.json")


def vapid():
    """返回 (私钥对象, 公钥原始字节, 公钥 base64url)。"""
    global _vapid
    if _vapid is not None:
        return _vapid
    with _lock:
        if _vapid is not None:
            return _vapid
        path = _key_path()
        priv = None
        pub_raw = b""
        try:
            with open(path, "r", encoding="utf-8") as fh:
                saved = json.load(fh)
            priv = ec.derive_private_key(
                int.from_bytes(_b64d(saved["private"]), "big"), ec.SECP256R1()
            )
            pub_raw = _b64d(saved["public"])
        except Exception:  # noqa: BLE001
            priv = None

        if priv is None:
            priv = ec.generate_private_key(ec.SECP256R1())
            pub_raw = priv.public_key().public_bytes(
                serialization.Encoding.X962, serialization.PublicFormat.UncompressedPoint
            )
            os.makedirs(os.path.dirname(path), exist_ok=True)
            tmp = path + ".tmp"
            with open(tmp, "w", encoding="utf-8") as fh:
                json.dump({
                    "private": _b64u(priv.private_numbers().private_value.to_bytes(32, "big")),
                    "public": _b64u(pub_raw),
                }, fh)
            os.chmod(tmp, 0o600)
            os.replace(tmp, path)

        _vapid = (priv, pub_raw, _b64u(pub_raw))
        return _vapid


def public_key():
    if not HAVE_CRYPTO:
        return ""
    try:
        return vapid()[2]
    except Exception:  # noqa: BLE001
        return ""


def _jwt(endpoint):
    priv, _pub, pub_b64 = vapid()
    parsed = urlparse(endpoint)
    header = _b64u(json.dumps({"typ": "JWT", "alg": "ES256"}, separators=(",", ":")).encode())
    claims = _b64u(json.dumps({
        "aud": "%s://%s" % (parsed.scheme, parsed.netloc),
        "exp": int(time.time()) + 12 * 3600,
        "sub": config.PUSH_SUBJECT,
    }, separators=(",", ":")).encode())
    signing_input = ("%s.%s" % (header, claims)).encode("ascii")
    der = priv.sign(signing_input, ec.ECDSA(hashes.SHA256()))
    r, s = decode_dss_signature(der)
    sig = r.to_bytes(32, "big") + s.to_bytes(32, "big")
    return "%s.%s" % (signing_input.decode("ascii"), _b64u(sig))


def _encrypt(payload, p256dh, auth):
    ua_pub = _b64d(p256dh)
    auth_secret = _b64d(auth)
    as_priv = ec.generate_private_key(ec.SECP256R1())
    as_pub = as_priv.public_key().public_bytes(
        serialization.Encoding.X962, serialization.PublicFormat.UncompressedPoint
    )
    ua_key = ec.EllipticCurvePublicKey.from_encoded_point(ec.SECP256R1(), ua_pub)
    shared = as_priv.exchange(ec.ECDH(), ua_key)

    salt = os.urandom(16)
    ikm = HKDF(
        algorithm=hashes.SHA256(), length=32, salt=auth_secret,
        info=b"WebPush: info\x00" + ua_pub + as_pub,
    ).derive(shared)
    cek = HKDF(
        algorithm=hashes.SHA256(), length=16, salt=salt,
        info=b"Content-Encoding: aes128gcm\x00",
    ).derive(ikm)
    nonce = HKDF(
        algorithm=hashes.SHA256(), length=12, salt=salt,
        info=b"Content-Encoding: nonce\x00",
    ).derive(ikm)

    # 单条记录，用 0x02 当最后一块的分隔符（RFC 8188）
    body = AESGCM(cek).encrypt(nonce, payload + b"\x02", None)
    return salt + struct.pack(">I", 4096) + bytes([len(as_pub)]) + as_pub + body


def send(sub, payload):
    """发给一个订阅。返回 (ok, error)；410/404 由调用方决定删除。"""
    if not HAVE_CRYPTO:
        return False, "服务器缺少 cryptography"
    try:
        data = _encrypt(json.dumps(payload, ensure_ascii=False).encode("utf-8"),
                        sub["p256dh"], sub["auth"])
        req = urlrequest.Request(sub["endpoint"], data=data, method="POST")
        req.add_header("Content-Type", "application/octet-stream")
        req.add_header("Content-Encoding", "aes128gcm")
        req.add_header("TTL", "86400")
        req.add_header("Authorization", "vapid t=%s, k=%s" % (_jwt(sub["endpoint"]), vapid()[2]))
        with urlrequest.urlopen(req, timeout=10) as resp:
            resp.read()
        return True, ""
    except Exception as exc:  # noqa: BLE001
        return False, str(exc)


# ---------------------------------------------------------------- 合并与派发

def queue(user_id, conv_id, title, body, icon, url, tag):
    """把一条新消息排进合并队列；2 秒后统一发。"""
    if not HAVE_CRYPTO:
        return
    key = (int(user_id), int(conv_id))
    with _pend_lock:
        item = _pending.get(key)
        if item is None:
            item = {"count": 0, "body": "", "title": title, "icon": icon, "url": url, "tag": tag}
            _pending[key] = item
            timer = threading.Timer(MERGE_SECONDS, _flush, args=(key,))
            timer.daemon = True
            timer.start()
        item["count"] += 1
        item["body"] = body
        item["title"] = title
        item["icon"] = icon
        item["url"] = url
        item["tag"] = tag


def _flush(key):
    with _pend_lock:
        item = _pending.pop(key, None)
    if not item:
        return
    user_id = key[0]
    text = item["body"]
    if item["count"] > 1:
        text = "[%d条新消息]%s" % (item["count"], item["body"])
    payload = {
        "title": item["title"],
        "body": text,
        "icon": item["icon"],
        "url": item["url"],
        "tag": item["tag"],
        "count": item["count"],
    }
    rows = db.qall("SELECT * FROM push_subs WHERE user_id = ?", (user_id,))
    for sub in rows:
        ok, err = send(sub, payload)
        if not ok and any(code in err for code in ("410", "404", "403")):
            db.run("DELETE FROM push_subs WHERE id = ?", (sub["id"],))
