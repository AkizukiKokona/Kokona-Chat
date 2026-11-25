"""极轻量发信：配置了 SMTP 就真发，没配置就落库排队（管理后台可见）。"""

import os
import smtplib
import ssl
from datetime import datetime, timedelta, timezone
from email.message import EmailMessage
from email.utils import formataddr

from . import config, db

ICON_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "static", "icon.png")
ICON_CID = "kokona-icon"

# 和网页同一套配色：棕金 + 米色底
BRAND = "#9a6c3c"
BRAND_DEEP = "#83582c"
CREAM = "#efe4d2"
CARD = "#fffdf9"
CODE_BG = "#f4e3c4"
INK = "#3a2d1e"
INK_SOFT = "#5a4a38"
INK_MUTE = "#8a7862"
LINE = "#efe3d0"

FONT = "-apple-system,BlinkMacSystemFont,'Segoe UI','PingFang SC','Hiragino Sans GB','Microsoft YaHei',sans-serif"
MONO = "ui-monospace,SFMono-Regular,Menlo,Consolas,'Courier New',monospace"


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
        part = msg.add_alternative(html, subtype="html")
        if part is None:  # 老版本 Python 的 add_alternative 不返回新建的 part
            part = msg.get_payload()[-1]
        _attach_icon(part)

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


def _attach_icon(html_part):
    """图标内嵌成 cid，不依赖外链——大部分客户端默认不加载远程图片。"""
    try:
        with open(ICON_PATH, "rb") as fh:
            data = fh.read()
    except OSError:
        return
    try:
        html_part.add_related(
            data, maintype="image", subtype="png",
            cid="<%s>" % ICON_CID, filename="icon.png",
        )
    except Exception:  # noqa: BLE001
        pass


# ---------------------------------------------------------------- 模板

def _beijing_now():
    return datetime.now(timezone.utc) + timedelta(hours=8)


def _wrap(title, lead, code, note, when):
    name = config.MAIL_NAME
    site = config.SITE_URL
    host = site.replace("https://", "").replace("http://", "")
    return """<!DOCTYPE html>
<html lang="zh-CN" style="background:__CREAM__;"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<meta name="x-apple-disable-message-reformatting">
<title>__NAME__</title></head>
<body style="margin:0;padding:0;background:__CREAM__;">
<div style="display:none;max-height:0;overflow:hidden;opacity:0;color:transparent;">__NAME__ 验证码 __CODE__，10 分钟内有效。</div>
<table role="presentation" width="100%" cellpadding="0" cellspacing="0" border="0" style="background:__CREAM__;">
<tr><td align="center" style="padding:32px 14px;">

  <table role="presentation" width="100%" cellpadding="0" cellspacing="0" border="0"
         style="max-width:520px;background:__CARD__;border-radius:16px;overflow:hidden;
                box-shadow:0 8px 28px rgba(90,58,22,.12);">

    <tr><td style="background:__BRAND__;padding:22px 26px;">
      <table role="presentation" cellpadding="0" cellspacing="0" border="0"><tr>
        <td style="padding-right:13px;">
          <img src="cid:__CID__" width="44" height="44" alt="__NAME__"
               style="display:block;width:44px;height:44px;border:0;border-radius:12px;background:#ffffff;">
        </td>
        <td>
          <div style="font-family:__FONT__;font-size:17px;font-weight:700;color:#ffffff;letter-spacing:.3px;">__NAME__</div>
          <div style="font-family:__FONT__;font-size:12px;color:#f0dcc0;margin-top:4px;letter-spacing:.6px;">__SLOGAN__</div>
        </td>
      </tr></table>
    </td></tr>

    <tr><td style="padding:28px 26px 4px;">
      <div style="font-family:__FONT__;font-size:15px;font-weight:600;color:__INK__;">您好，</div>
      <div style="font-family:__FONT__;font-size:14px;line-height:1.85;color:__INK_SOFT__;margin-top:10px;">__LEAD__，验证码是：</div>

      <div style="margin:20px 0 4px;padding:17px 0;text-align:center;background:__CODE_BG__;border-radius:12px;">
        <span style="font-family:__MONO__;font-size:30px;font-weight:700;letter-spacing:9px;color:__BRAND_DEEP__;text-indent:9px;">__CODE__</span>
      </div>

      <div style="font-family:__FONT__;font-size:12.5px;line-height:1.8;color:__INK_MUTE__;margin-top:12px;">__NOTE__</div>
    </td></tr>

    <tr><td style="padding:20px 26px 26px;">
      <div style="height:1px;background:__LINE__;margin-bottom:14px;"></div>
      <div style="font-family:__FONT__;font-size:12px;line-height:1.9;color:#a08e78;">
        发送于 __WHEN__（北京时间）<br>
        <a href="__SITE__" style="color:__BRAND__;text-decoration:none;">__HOST__</a>
      </div>
    </td></tr>
  </table>

  <div style="font-family:__FONT__;font-size:11px;color:#b3a08a;margin-top:16px;letter-spacing:.3px;">此邮件由系统自动发出</div>
</td></tr></table>
</body></html>""".replace("__NAME__", name).replace("__SLOGAN__", config.SLOGAN) \
        .replace("__CREAM__", CREAM).replace("__CARD__", CARD).replace("__BRAND__", BRAND) \
        .replace("__BRAND_DEEP__", BRAND_DEEP).replace("__CODE_BG__", CODE_BG).replace("__INK_SOFT__", INK_SOFT) \
        .replace("__INK__", INK).replace("__INK_MUTE__", INK_MUTE).replace("__LINE__", LINE) \
        .replace("__FONT__", FONT).replace("__MONO__", MONO).replace("__CID__", ICON_CID) \
        .replace("__LEAD__", lead).replace("__CODE__", code).replace("__NOTE__", note) \
        .replace("__WHEN__", when).replace("__SITE__", site).replace("__HOST__", host)


def send_code(to_addr, code, purpose):
    acts = {
        "register": "注册新账号",
        "reset_password": "重置登录密码",
        "find_username": "找回账号",
    }
    titles = {
        "register": "注册验证码",
        "reset_password": "重置密码验证码",
        "find_username": "找回账号验证码",
    }
    act = acts.get(purpose, "验证身份")
    title = titles.get(purpose, "验证码")
    when = _beijing_now().strftime("%Y-%m-%d %H:%M")
    site = config.SITE_URL

    lead = "您正在%s" % act
    note = ("10 分钟内有效。如果不是您本人操作，忽略这封邮件就行，账号不会有任何变化。")
    body = "\n".join([
        "您好：",
        "",
        "%s，验证码是：" % lead,
        "",
        "    %s" % code,
        "",
        note,
        "",
        "发送于 %s（北京时间）" % when,
        "%s  %s" % (config.MAIL_NAME, site),
    ])
    html = _wrap(title, lead, code, note, when)
    ok, err = send(to_addr, "%s · %s" % (config.MAIL_NAME, title), body, html)
    return ok, err, code


def _log(to_addr, subject, body, status, error):
    try:
        db.run(
            "INSERT INTO mail_log (to_addr, subject, body, status, error, created_at) VALUES (?, ?, ?, ?, ?, ?)",
            (to_addr, subject, body, status, error, db.now()),
        )
    except Exception:
        pass
