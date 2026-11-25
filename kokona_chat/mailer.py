"""极轻量发信：配置了 SMTP 就真发，没配置就落库排队（管理后台可见）。"""

import smtplib
import ssl
from email.message import EmailMessage
from email.utils import formataddr

from . import config, db


def configured():
    return bool(config.SMTP_HOST)


def send(to_addr, subject, body, html=None):
    """返回 (ok, error)。无论成败都写 mail_log，管理后台能看到。"""
    to_addr = str(to_addr or "").strip()
    if not to_addr:
        return False, "收件人为空"

    msg = EmailMessage()
    msg["From"] = formataddr((config.MAIL_NAME, config.MAIL_FROM))
    msg["To"] = to_addr
    msg["Subject"] = subject
    msg.set_content(body)
    if html:
        msg.add_alternative(html, subtype="html")

    if not configured():
        _log(to_addr, subject, body, "queued", "SMTP 未配置")
        return False, "SMTP 未配置"

    try:
        if config.SMTP_MODE == "ssl":
            server = smtplib.SMTP_SSL(
                config.SMTP_HOST, config.SMTP_PORT, timeout=15,
                context=ssl.create_default_context(),
            )
        else:
            server = smtplib.SMTP(config.SMTP_HOST, config.SMTP_PORT, timeout=15)
            server.ehlo()
            if config.SMTP_MODE == "starttls":
                server.starttls(context=ssl.create_default_context())
                server.ehlo()
        if config.SMTP_USER:
            server.login(config.SMTP_USER, config.SMTP_PASS)
        server.send_message(msg)
        try:
            server.quit()
        except Exception:
            pass
        _log(to_addr, subject, body, "sent", "")
        return True, ""
    except Exception as exc:  # noqa: BLE001
        _log(to_addr, subject, body, "failed", str(exc))
        return False, str(exc)


def send_code(to_addr, code, purpose):
    titles = {
        "register": "注册验证码",
        "reset_password": "重置密码验证码",
        "find_username": "找回账号验证码",
    }
    title = titles.get(purpose, "验证码")
    body = (
        "你好：\n\n"
        "你正在%s，验证码是：\n\n    %s\n\n"
        "10 分钟内有效。如果不是你本人操作，忽略这封邮件即可。\n\n"
        "—— %s"
    ) % (title.replace("验证码", ""), code, config.MAIL_NAME)
    ok, err = send(to_addr, "%s · %s" % (config.MAIL_NAME, title), body)
    return ok, err, code


def _log(to_addr, subject, body, status, error):
    try:
        db.run(
            "INSERT INTO mail_log (to_addr, subject, body, status, error, created_at) VALUES (?, ?, ?, ?, ?, ?)",
            (to_addr, subject, body, status, error, db.now()),
        )
    except Exception:
        pass
