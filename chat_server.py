#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Kokona Chat —— 多频道极简聊天

约定：
  * WebSocket 连 /chat/ws?ch=<频道>  = 用户 A（程序/脚本）
  * 浏览器开 /chat/ 或 /chat/2/      = 用户 B（人）
  * 频道 1 为默认（/chat/ 即频道 1），频道 2 预置
  * 零第三方依赖，只用标准库；不做撤回、删除、编辑

鉴权：token 默认 sukikokona1212，可用环境变量 CHAT_TOKEN 覆盖。
      页面免 token（直接打开即用），接口与 WS 需要 token。
"""

import base64
import collections
import hashlib
import json
import os
import queue
import struct
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import parse_qs, urlparse

TOKEN = os.environ.get("CHAT_TOKEN", "sukikokona1212")
PORT = int(os.environ.get("CHAT_PORT", "8299"))
HISTORY_MAX = int(os.environ.get("CHAT_HISTORY", "300"))
CHANNELS_FILE = os.environ.get("CHAT_CHANNELS_FILE", "/opt/kokona-chat/channels.json")
WS_GUID = "258EAFA5-E914-47DA-95CA-C5AB0DC85B11"
MAX_TEXT = 4000
RESERVED = {"ws", "stream", "send", "channels", "history", "health"}

_lock = threading.Lock()
_seq = [0]


# --------------------------------------------------------------------------
# 频道
# --------------------------------------------------------------------------
class Channel(object):
    __slots__ = ("cid", "name", "ws", "sse", "history")

    def __init__(self, cid, name):
        self.cid = cid
        self.name = name
        self.ws = []
        self.sse = []
        self.history = collections.deque(maxlen=HISTORY_MAX)


_channels = {}


def _read_meta():
    try:
        with open(CHANNELS_FILE, "r", encoding="utf-8") as fh:
            data = json.load(fh)
        if isinstance(data, dict):
            return {str(k): str(v) for k, v in data.items()}
    except Exception:
        pass
    return {}


def _write_meta():
    try:
        meta = {cid: ch.name for cid, ch in _channels.items()}
        tmp = CHANNELS_FILE + ".tmp"
        with open(tmp, "w", encoding="utf-8") as fh:
            json.dump(meta, fh, ensure_ascii=False, indent=2)
        os.replace(tmp, CHANNELS_FILE)
    except Exception:
        pass


def get_channel(cid, create=False):
    cid = str(cid).strip() or "1"
    with _lock:
        ch = _channels.get(cid)
        if ch is None and create:
            ch = Channel(cid, "频道 %s" % cid)
            _channels[cid] = ch
            _write_meta()
        return ch


def init_channels():
    meta = _read_meta()
    for cid in ["1", "2"]:
        meta.setdefault(cid, "频道 %s" % cid)
    with _lock:
        for cid, name in meta.items():
            _channels[cid] = Channel(cid, name)
    _write_meta()


def publish(ch, sender, text):
    """sender: "A" | "B"。A 的消息只推给 B；B 的消息推给 A 并回显给 B 自己。"""
    with _lock:
        _seq[0] += 1
        msg = {
            "id": _seq[0],
            "ch": ch.cid,
            "from": sender,
            "text": text,
            "ts": int(time.time() * 1000),
        }
        ch.history.append(msg)
        ws_targets = list(ch.ws) if sender == "B" else []
        sse_targets = list(ch.sse)

    payload = json.dumps(msg, ensure_ascii=False)
    for q in sse_targets:
        try:
            q.put_nowait(payload)
        except queue.Full:
            pass
    for c in ws_targets:
        try:
            c["h"].ws_send_json(c, payload)
        except Exception:
            pass
    return msg


# --------------------------------------------------------------------------
# 页面
# --------------------------------------------------------------------------
PAGE = r"""<!doctype html>
<html lang="zh-CN">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
<meta name="theme-color" content="#11131a">
<title>Kokona Chat</title>
<style>
  :root{
    --bg:#11131a; --panel:#191b23; --ink:#f4f2ef; --muted:#8d8f9c;
    --accent:#f2b6bb; --accent-soft:#f8d7d2; --line:#2a2d38;
  }
  *{box-sizing:border-box}
  html,body{margin:0;height:100%}
  body{
    background:var(--bg); color:var(--ink); display:flex; flex-direction:column;
    height:100vh; height:100dvh;
    font:14px/1.6 "Noto Sans SC","PingFang SC","Microsoft YaHei",system-ui,sans-serif;
  }
  header{
    display:flex; align-items:center; justify-content:space-between; gap:10px;
    padding:11px 16px; border-bottom:1px solid var(--line);
    background:rgba(17,19,26,.94); position:sticky; top:0; z-index:30;
  }
  .h-left{display:flex; align-items:center; gap:9px; min-width:0}
  header b{font-weight:600; letter-spacing:.02em; white-space:nowrap}
  .tag{
    flex:none; font-size:10px; letter-spacing:.12em; color:var(--accent);
    border:1px solid rgba(242,182,187,.35); border-radius:999px; padding:2px 8px;
  }
  .h-right{display:flex; align-items:center; gap:8px; min-width:0}
  #status{font-size:11px; color:var(--muted); white-space:nowrap; overflow:hidden; text-overflow:ellipsis}
  #status.on{color:#8ed49a}
  .ch-btn{
    display:inline-flex; align-items:center; gap:7px; height:30px; padding:0 12px;
    border-radius:999px; border:1px solid rgba(242,182,187,.45);
    background:rgba(242,182,187,.12); color:var(--ink); font:inherit; font-size:12.5px;
    cursor:pointer; white-space:nowrap; max-width:42vw; flex:none;
  }
  .ch-btn:hover{background:rgba(242,182,187,.2)}
  .ch-btn .dot{width:6px;height:6px;border-radius:50%;background:var(--accent);flex:none}
  .ch-btn .nm{overflow:hidden; text-overflow:ellipsis}
  main{
    flex:1; overflow-y:auto; padding:16px; display:flex; flex-direction:column; gap:10px;
    -webkit-overflow-scrolling:touch;
  }
  .msg{
    max-width:78%; padding:9px 13px; border-radius:12px;
    background:var(--panel); border:1px solid var(--line);
    overflow-wrap:anywhere; white-space:pre-wrap;
  }
  .msg.a{align-self:flex-start; border-bottom-left-radius:4px}
  .msg.b{
    align-self:flex-end; border-bottom-right-radius:4px;
    background:rgba(242,182,187,.13); border-color:rgba(242,182,187,.32);
  }
  .meta{display:block; font-size:10px; color:var(--muted); margin-bottom:3px; letter-spacing:.06em}
  .empty{color:var(--muted); text-align:center; margin:auto 0; font-size:12.5px; line-height:1.9}
  form{
    display:flex; gap:8px; padding:12px 16px; border-top:1px solid var(--line);
    background:rgba(17,19,26,.96); align-items:flex-end;
  }
  textarea{
    flex:1; min-width:0; padding:11px 14px; border-radius:10px;
    border:1px solid var(--line); background:#0e1016; color:var(--ink);
    font:inherit; line-height:1.55; outline:none; resize:none; display:block;
    overflow-y:hidden; max-height:132px;   /* 五行封顶，超出内部滚动 */
  }
  textarea:focus{border-color:rgba(242,182,187,.6)}
  button.send{
    height:44px; flex:none;
    padding:0 18px; border-radius:10px; cursor:pointer; font:inherit;
    border:1px solid rgba(242,182,187,.55); background:rgba(242,182,187,.18); color:var(--ink);
  }
  button.send:active{background:rgba(242,182,187,.34)}

  /* 频道面板 */
  .mask{position:fixed; inset:0; z-index:40; display:none}
  .mask.open{display:block}
  #panel{
    position:fixed; z-index:50; width:min(92vw,360px); padding:8px;
    background:#161821; border:1px solid var(--line); border-radius:12px;
    box-shadow:0 18px 44px rgba(0,0,0,.55); display:none;
  }
  #panel.open{display:block}
  .panel-hd{
    display:flex; align-items:center; justify-content:space-between; gap:8px;
    font-size:10px; letter-spacing:.14em; color:var(--muted); padding:6px 8px 8px;
  }
  .panel-hd .mini{letter-spacing:0; height:24px; font-size:11px; padding:0 9px}
  .ch-item{
    display:flex; align-items:center; justify-content:space-between; gap:10px;
    padding:9px 10px; border-radius:8px; cursor:pointer; font-size:13px;
  }
  .ch-item:hover{background:rgba(255,255,255,.05)}
  .ch-item.active{background:rgba(242,182,187,.14); color:var(--accent-soft)}
  .ch-item small{color:var(--muted); font-size:10.5px; white-space:nowrap}
  .sep{height:1px; background:var(--line); margin:7px 4px}
  .new-ch{
    width:100%; height:34px; border-radius:8px; cursor:pointer;
    border:1px dashed rgba(242,182,187,.45); background:transparent; color:var(--accent-soft);
    font:inherit; font-size:12.5px;
  }
  .new-ch:hover{background:rgba(242,182,187,.1)}
  .new-ch:disabled{opacity:.55; cursor:default}
  .wsbox{
    margin-top:8px; padding:10px 11px; border-radius:8px;
    background:#0d0f15; border:1px solid var(--line); font-size:11px; line-height:1.65;
  }
  .wsbox .lbl{color:var(--accent-soft); font-size:11px; margin-bottom:5px}
  .wsbox code{
    display:block; color:var(--accent-soft);
    font-family:ui-monospace,SFMono-Regular,Menlo,Consolas,monospace;
    font-size:10.5px; word-break:break-all; line-height:1.6;
  }
  .wsbox .row{display:flex; gap:7px; align-items:center; justify-content:space-between; margin-top:6px}
  .wsbox .hint{color:var(--muted); font-size:10.5px}
  .mini{
    height:26px; padding:0 10px; border-radius:6px; cursor:pointer; font:inherit; font-size:11px;
    border:1px solid var(--line); background:#151821; color:var(--ink); white-space:nowrap;
  }
  .mini:hover{border-color:rgba(242,182,187,.5)}
  .mini.wide{flex:1; height:30px; font-size:12px; border-color:rgba(242,182,187,.4); background:rgba(242,182,187,.12)}
  @media (max-width:520px){
    .msg{max-width:86%}
    header{padding:9px 12px}
    main{padding:13px}
    form{padding:10px 12px}
    .tag{display:none}
    #status{display:none}
  }
</style>
</head>
<body>
<header>
  <div class="h-left">
    <b>Kokona Chat</b>
    <span class="tag">秋月不会解梦</span>
  </div>
  <div class="h-right">
    <span id="status">连接中…</span>
    <button class="ch-btn" id="chBtn" type="button" aria-haspopup="true" aria-expanded="false">
      <span class="dot"></span><span class="nm" id="chName">频道 1</span><span style="opacity:.55">▾</span>
    </button>
  </div>
</header>

<main id="log"><p class="empty" id="empty">这个频道还没有消息<br>把 WS 地址交给心夏就能开聊</p></main>

<form id="form">
  <textarea id="input" rows="1" autocomplete="off" placeholder="说点什么…（Enter 发送 · Shift+Enter 换行）" enterkeyhint="send"></textarea>
  <button class="send" type="submit">发送</button>
</form>

<div class="mask" id="mask"></div>
<div id="panel" role="dialog" aria-label="频道">
  <div class="panel-hd"><span>频道</span><button class="mini" id="renameCh" type="button">✎ 改名</button></div>
  <div id="chList"></div>
  <div class="sep"></div>
  <button class="new-ch" id="newCh" type="button">＋ 新建频道</button>
</div>

<script>
(function(){
  var qs = new URLSearchParams(location.search);
  var TOKEN = qs.get('token') || 'sukikokona1212';
  var RESERVED = ['ws','stream','send','channels','history','health'];

  // 两个角色在界面上的显示名
  var NAME_A = '心夏';           // WebSocket 那一侧
  var NAME_B = '秋月不会解梦';     // 浏览器这一侧
  var SHORT_B = '秋月';          // 面板等窄处用的简称
  var MAX_INPUT_H = 132;         // 输入框最多撑到五行

  var ch = qs.get('ch') || '1';
  var m = location.pathname.match(/^\/chat\/([^\/]+)\/?$/);
  if (m && RESERVED.indexOf(m[1]) < 0) ch = decodeURIComponent(m[1]);

  var log = document.getElementById('log');
  var empty = document.getElementById('empty');
  var statusEl = document.getElementById('status');
  var input = document.getElementById('input');
  var chBtn = document.getElementById('chBtn');
  var chName = document.getElementById('chName');
  var panel = document.getElementById('panel');
  var mask = document.getElementById('mask');
  var chList = document.getElementById('chList');

  function esc(s){
    return String(s).replace(/[&<>"]/g, function(c){
      return {'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c];
    });
  }

  function add(msg){
    if (empty && empty.parentNode) empty.parentNode.removeChild(empty);
    var d = document.createElement('div');
    d.className = 'msg ' + (msg.from === 'B' ? 'b' : 'a');
    var meta = document.createElement('span');
    meta.className = 'meta';
    var t = new Date(msg.ts);
    meta.textContent = (msg.from === 'B' ? NAME_B : NAME_A) + ' · ' + t.toLocaleTimeString('zh-CN', {hour12:false});
    var body = document.createElement('span');
    body.textContent = msg.text;
    d.appendChild(meta); d.appendChild(body); log.appendChild(d);
    log.scrollTop = log.scrollHeight;
  }

  var es = new EventSource('/chat/stream?token=' + encodeURIComponent(TOKEN) + '&ch=' + encodeURIComponent(ch));
  es.onopen = function(){ statusEl.textContent = '已连接 · ' + NAME_B; statusEl.classList.add('on'); };
  es.onerror = function(){ statusEl.textContent = '重连中…'; statusEl.classList.remove('on'); };
  es.onmessage = function(e){ try { add(JSON.parse(e.data)); } catch(_){} };

  // ---- 输入框：随内容长高，最多五行，之后内部滚动 ----
  function autoGrow(){
    input.style.height = 'auto';
    var need = input.scrollHeight;
    input.style.height = Math.min(need, MAX_INPUT_H) + 'px';
    input.style.overflowY = need > MAX_INPUT_H ? 'auto' : 'hidden';
  }
  input.addEventListener('input', autoGrow);

  // Enter 发送，Shift+Enter 换行；中文输入法选词的回车不算
  input.addEventListener('keydown', function(e){
    if (e.key === 'Enter' && !e.shiftKey && !e.isComposing) {
      e.preventDefault();
      document.getElementById('form').requestSubmit();
    }
  });

  // ---- 发送 ----
  document.getElementById('form').addEventListener('submit', function(e){
    e.preventDefault();
    var text = input.value.trim();
    if (!text) return;
    input.value = '';
    autoGrow();
    fetch('/chat/send?token=' + encodeURIComponent(TOKEN) + '&ch=' + encodeURIComponent(ch), {
      method: 'POST',
      headers: {'Content-Type': 'application/json'},
      body: JSON.stringify({text: text})
    }).catch(function(){ statusEl.textContent = '发送失败'; });
    input.focus();
  });

  function placePanel(){
    var r = chBtn.getBoundingClientRect();
    var w = panel.offsetWidth || 340;
    var left = Math.min(Math.max(8, r.right - w), window.innerWidth - w - 8);
    panel.style.left = left + 'px';
    panel.style.top = (r.bottom + 8) + 'px';
  }
  function openPanel(){
    panel.classList.add('open'); mask.classList.add('open');
    chBtn.setAttribute('aria-expanded','true');
    placePanel(); loadChannels();
  }
  function closePanel(){
    panel.classList.remove('open'); mask.classList.remove('open');
    chBtn.setAttribute('aria-expanded','false');
  }
  chBtn.addEventListener('click', function(e){
    e.stopPropagation();
    if (panel.classList.contains('open')) closePanel(); else openPanel();
  });
  mask.addEventListener('click', closePanel);
  document.addEventListener('keydown', function(e){ if (e.key === 'Escape') closePanel(); });
  window.addEventListener('resize', placePanel);

  function loadChannels(){
    fetch('/chat/channels?token=' + encodeURIComponent(TOKEN))
      .then(function(r){ return r.json(); })
      .then(function(d){
        for (var i = 0; i < d.channels.length; i++) {
          if (d.channels[i].id === ch) {
            chName.textContent = d.channels[i].name;
            document.title = 'Kokona Chat · ' + d.channels[i].name;
          }
        }
        chList.innerHTML = d.channels.map(function(c){
          var path = c.id === '1' ? '/chat/' : '/chat/' + esc(c.id) + '/';
          return '<div class="ch-item' + (c.id === ch ? ' active' : '') + '" data-id="' + esc(c.id) + '">'
            + '<span>' + esc(c.name) + '</span>'
            + '<small>' + path + ' · ' + NAME_A + c.ws + ' ' + SHORT_B + c.sse + '</small>'
            + '</div>';
        }).join('');
        var items = chList.querySelectorAll('.ch-item');
        for (var k = 0; k < items.length; k++) {
          items[k].addEventListener('click', function(){
            var id = this.getAttribute('data-id');
            if (id === ch) { closePanel(); return; }
            location.href = (id === '1' ? '/chat/' : '/chat/' + encodeURIComponent(id) + '/');
          });
        }
      })
      .catch(function(){ chList.innerHTML = '<div class="ch-item"><small>频道列表加载失败</small></div>'; });
  }

  document.getElementById('renameCh').addEventListener('click', function(){
    var cur = chName.textContent;
    var name = window.prompt('频道名（1–20 字）', cur);
    if (name === null) return;
    name = String(name).trim().slice(0, 20);
    if (!name || name === cur) return;
    fetch('/chat/channels/rename?token=' + encodeURIComponent(TOKEN) + '&ch=' + encodeURIComponent(ch), {
      method: 'POST',
      headers: {'Content-Type': 'application/json'},
      body: JSON.stringify({name: name})
    }).then(function(r){ return r.json(); })
      .then(function(d){
        if (!d.ok) throw new Error(d.error || 'fail');
        chName.textContent = d.name;
        document.title = 'Kokona Chat · ' + d.name;
        loadChannels();
      })
      .catch(function(){ statusEl.textContent = '改名失败'; });
  });

  document.getElementById('newCh').addEventListener('click', function(){
    var btn = this;
    btn.disabled = true; btn.textContent = '创建中…';
    fetch('/chat/channels/new?token=' + encodeURIComponent(TOKEN), {method:'POST'})
      .then(function(r){ return r.json(); })
      .then(function(d){
        btn.disabled = false; btn.textContent = '＋ 新建频道';
        if (!d.ok) throw new Error(d.error || 'fail');
        var old = panel.querySelector('.wsbox');
        if (old) old.remove();
        var box = document.createElement('div');
        box.className = 'wsbox';
        box.innerHTML = '<div class="lbl">新频道 · ' + esc(d.name) + '</div>'
          + '<code>' + esc(d.ws_url) + '</code>'
          + '<div class="row"><span class="hint">A 端用它连接 · 端口 ' + d.port + '</span>'
          + '<button class="mini" data-act="copy" type="button">复制</button></div>'
          + '<div class="row"><button class="mini wide" data-act="go" type="button">进入 ' + esc(d.name) + '</button></div>';
        panel.appendChild(box);
        box.querySelector('[data-act="copy"]').addEventListener('click', function(){
          var self = this;
          if (navigator.clipboard) {
            navigator.clipboard.writeText(d.ws_url).catch(function(){});
          } else {
            var ta = document.createElement('textarea');
            ta.value = d.ws_url; document.body.appendChild(ta); ta.select();
            try { document.execCommand('copy'); } catch(_) {}
            document.body.removeChild(ta);
          }
          self.textContent = '已复制';
          setTimeout(function(){ self.textContent = '复制'; }, 1400);
        });
        box.querySelector('[data-act="go"]').addEventListener('click', function(){
          location.href = '/chat/' + encodeURIComponent(d.id) + '/';
        });
        loadChannels();
      })
      .catch(function(){
        btn.disabled = false; btn.textContent = '＋ 新建频道';
        statusEl.textContent = '创建失败';
      });
  });

  window.addEventListener('pageshow', function(){ input.focus(); autoGrow(); });

  // 首屏就拉一次频道信息，让按钮和标题立刻显示真实频道名
  loadChannels();
  autoGrow();
})();
</script>
</body>
</html>
"""


# --------------------------------------------------------------------------
# HTTP / WS
# --------------------------------------------------------------------------
class Handler(BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.1"
    server_version = "KokonaChat/1.1"

    def log_message(self, fmt, *args):
        pass

    # ---------- 工具 ----------
    def _qs(self):
        return parse_qs(urlparse(self.path).query)

    def _path(self):
        return urlparse(self.path).path.rstrip("/") or "/"

    def _ch_param(self):
        q = self._qs()
        if q.get("ch"):
            return str(q["ch"][0]).strip() or "1"
        p = urlparse(self.path).path.rstrip("/")
        if p.startswith("/chat/"):
            seg = p.rsplit("/", 1)[-1]
            if seg and seg not in RESERVED:
                return seg
        return "1"

    def _token_ok(self):
        q = self._qs()
        if q.get("token", [""])[0] == TOKEN:
            return True
        if self.headers.get("X-Token") == TOKEN:
            return True
        auth = self.headers.get("Authorization", "")
        return auth.lower().startswith("bearer ") and auth[7:].strip() == TOKEN

    def _json(self, code, obj):
        body = json.dumps(obj, ensure_ascii=False).encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)

    def _text(self, code, body, ctype="text/plain; charset=utf-8"):
        raw = body.encode("utf-8") if isinstance(body, str) else body
        self.send_response(code)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(raw)))
        # 页面不缓存：改完刷新就是新的，避免拿到旧 JS
        self.send_header("Cache-Control", "no-store, must-revalidate")
        self.end_headers()
        self.wfile.write(raw)

    # ---------- GET ----------
    def do_GET(self):
        p = self._path()

        if p in ("/", "/chat"):
            return self._text(200, PAGE, "text/html; charset=utf-8")

        if p.startswith("/chat/") and p.count("/") == 2 and p.split("/")[2] not in RESERVED:
            return self._text(200, PAGE, "text/html; charset=utf-8")

        if p in ("/chat/health", "/health"):
            with _lock:
                info = {c.cid: {"ws": len(c.ws), "sse": len(c.sse), "msgs": len(c.history)}
                        for c in _channels.values()}
            return self._json(200, {"ok": True, "channels": info})

        if p in ("/chat/ws", "/ws"):
            if not self._token_ok():
                return self._json(401, {"error": "bad token"})
            return self._ws_handshake(get_channel(self._ch_param(), create=True))

        if p in ("/chat/stream", "/stream"):
            if not self._token_ok():
                return self._json(401, {"error": "bad token"})
            return self._sse_stream(get_channel(self._ch_param(), create=True))

        if p in ("/chat/history", "/history"):
            if not self._token_ok():
                return self._json(401, {"error": "bad token"})
            ch = get_channel(self._ch_param(), create=True)
            with _lock:
                msgs = list(ch.history)
            return self._json(200, {"channel": ch.cid, "name": ch.name, "messages": msgs})

        if p in ("/chat/channels", "/channels"):
            if not self._token_ok():
                return self._json(401, {"error": "bad token"})
            with _lock:
                items = [
                    {"id": c.cid, "name": c.name,
                     "ws": len(c.ws), "sse": len(c.sse), "msgs": len(c.history)}
                    for c in sorted(_channels.values(), key=lambda x: (len(x.cid), x.cid))
                ]
            return self._json(200, {"channels": items})

        return self._json(404, {"error": "not found"})

    # ---------- HEAD（部分监控/预取会发，别回 501） ----------
    def do_HEAD(self):
        p = self._path()
        if p in ("/", "/chat") or (
            p.startswith("/chat/") and p.count("/") == 2 and p.split("/")[2] not in RESERVED
        ):
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(PAGE.encode("utf-8"))))
            self.send_header("Cache-Control", "no-store, must-revalidate")
            self.end_headers()
            return
        self.send_response(404)
        self.send_header("Content-Length", "0")
        self.end_headers()

    # ---------- POST ----------
    def do_POST(self):
        p = self._path()

        if p in ("/chat/channels/new", "/channels/new"):
            if not self._token_ok():
                return self._json(401, {"error": "bad token"})
            with _lock:
                nums = [int(c) for c in _channels.keys() if c.isdigit()]
                nxt = str(max(nums) + 1) if nums else "1"
                while nxt in _channels:
                    nxt = str(int(nxt) + 1)
            ch = get_channel(nxt, create=True)
            host = self.headers.get("Host", "localhost")
            return self._json(200, {
                "ok": True, "id": ch.cid, "name": ch.name,
                "ws_url": "wss://%s/chat/ws?token=%s&ch=%s" % (host, TOKEN, ch.cid),
                "port": 443,
                "page": "/chat/%s/" % ch.cid,
            })

        if p in ("/chat/channels/rename", "/channels/rename"):
            if not self._token_ok():
                return self._json(401, {"error": "bad token"})
            ch = get_channel(self._ch_param(), create=False)
            if ch is None:
                return self._json(404, {"error": "no such channel"})
            try:
                length = int(self.headers.get("Content-Length") or 0)
            except ValueError:
                length = 0
            raw = self.rfile.read(length) if length > 0 else b""
            name = ""
            try:
                data = json.loads(raw.decode("utf-8", "replace"))
                if isinstance(data, dict):
                    name = str(data.get("name", ""))
            except Exception:
                form = parse_qs(raw.decode("utf-8", "replace"))
                name = (form.get("name") or [""])[0]
            name = name.strip()[:20]
            if not name:
                return self._json(400, {"error": "empty name"})
            with _lock:
                ch.name = name
                _write_meta()
            return self._json(200, {"ok": True, "id": ch.cid, "name": ch.name})

        if p not in ("/chat/send", "/send"):
            return self._json(404, {"error": "not found"})
        if not self._token_ok():
            return self._json(401, {"error": "bad token"})

        try:
            length = int(self.headers.get("Content-Length") or 0)
        except ValueError:
            length = 0
        raw = self.rfile.read(length) if length > 0 else b""

        text = ""
        try:
            data = json.loads(raw.decode("utf-8", "replace"))
            if isinstance(data, dict):
                text = str(data.get("text", ""))
        except Exception:
            form = parse_qs(raw.decode("utf-8", "replace"))
            text = (form.get("text") or [""])[0]

        text = text.strip()[:MAX_TEXT]
        if not text:
            return self._json(400, {"error": "empty"})

        ch = get_channel(self._ch_param(), create=True)
        msg = publish(ch, "B", text)
        return self._json(200, {"ok": True, "id": msg["id"], "ch": ch.cid})

    # ---------- SSE ----------
    def _sse_stream(self, ch):
        q = queue.Queue(maxsize=1000)
        with _lock:
            ch.sse.append(q)
            hist = list(ch.history)
        try:
            self.send_response(200)
            self.send_header("Content-Type", "text/event-stream; charset=utf-8")
            self.send_header("Cache-Control", "no-cache, no-transform")
            self.send_header("Connection", "keep-alive")
            self.send_header("X-Accel-Buffering", "no")
            self.end_headers()

            for m in hist:
                self.wfile.write(("data: " + json.dumps(m, ensure_ascii=False) + "\n\n").encode("utf-8"))
            self.wfile.write(b"retry: 2000\n\n")
            self.wfile.flush()

            while True:
                try:
                    payload = q.get(timeout=15)
                    self.wfile.write(("data: " + payload + "\n\n").encode("utf-8"))
                    self.wfile.flush()
                except queue.Empty:
                    self.wfile.write(b": ping\n\n")
                    self.wfile.flush()
        except Exception:
            pass
        finally:
            with _lock:
                if q in ch.sse:
                    ch.sse.remove(q)

    # ---------- WebSocket ----------
    def _ws_handshake(self, ch):
        key = self.headers.get("Sec-WebSocket-Key")
        if not key:
            return self._json(400, {"error": "no key"})
        accept = base64.b64encode(
            hashlib.sha1((key + WS_GUID).encode("ascii")).digest()
        ).decode("ascii")
        self.send_response(101, "Switching Protocols")
        self.send_header("Upgrade", "websocket")
        self.send_header("Connection", "Upgrade")
        self.send_header("Sec-WebSocket-Accept", accept)
        self.end_headers()
        try:
            self.wfile.flush()
        except Exception:
            return
        self._ws_loop(ch)

    def _recv_exact(self, n):
        buf = b""
        while len(buf) < n:
            chunk = self.rfile.read(n - len(buf))
            if not chunk:
                raise ConnectionError("eof")
            buf += chunk
        return buf

    def _read_frame(self):
        b1, b2 = self._recv_exact(2)
        fin = bool(b1 & 0x80)
        opcode = b1 & 0x0F
        masked = bool(b2 & 0x80)
        length = b2 & 0x7F
        if length == 126:
            length = struct.unpack(">H", self._recv_exact(2))[0]
        elif length == 127:
            length = struct.unpack(">Q", self._recv_exact(8))[0]
        if length > 1 << 20:
            raise ConnectionError("frame too large")
        mask = self._recv_exact(4) if masked else b""
        payload = self._recv_exact(length) if length else b""
        if mask:
            payload = bytes(payload[i] ^ mask[i % 4] for i in range(len(payload)))
        return fin, opcode, payload

    def ws_send_raw(self, conn, opcode, payload):
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
        with conn["lock"]:
            self.connection.sendall(bytes(header) + payload)

    def ws_send_json(self, conn, payload):
        self.ws_send_raw(conn, 0x1, payload.encode("utf-8"))

    def _ws_loop(self, ch):
        conn = {"h": self, "lock": threading.Lock()}
        with _lock:
            ch.ws.append(conn)
            hist = list(ch.history)
        try:
            for m in hist:
                self.ws_send_json(conn, json.dumps(m, ensure_ascii=False))

            buf = b""
            buf_op = 0
            while True:
                fin, opcode, payload = self._read_frame()
                if opcode == 0x8:
                    break
                if opcode == 0x9:
                    self.ws_send_raw(conn, 0xA, payload)
                    continue
                if opcode == 0xA:
                    continue
                if opcode in (0x1, 0x2, 0x0):
                    buf += payload
                    if opcode in (0x1, 0x2):
                        buf_op = opcode
                    if not fin:
                        continue
                    data, buf = buf, b""
                    if buf_op == 0x2:
                        continue
                    text = ""
                    try:
                        obj = json.loads(data.decode("utf-8", "replace"))
                        if isinstance(obj, dict):
                            text = str(obj.get("text", ""))
                        else:
                            text = str(obj)
                    except Exception:
                        text = data.decode("utf-8", "replace")
                    text = text.strip()[:MAX_TEXT]
                    if text:
                        publish(ch, "A", text)
        except Exception:
            pass
        finally:
            with _lock:
                if conn in ch.ws:
                    ch.ws.remove(conn)
            try:
                self.close_connection = True
            except Exception:
                pass


class Server(ThreadingHTTPServer):
    daemon_threads = True
    allow_reuse_address = True


def main():
    init_channels()
    srv = Server(("127.0.0.1", PORT), Handler)
    print("kokona-chat on 127.0.0.1:%d channels=%s token=%s"
          % (PORT, ",".join(sorted(_channels)), TOKEN), flush=True)
    srv.serve_forever()


if __name__ == "__main__":
    main()
