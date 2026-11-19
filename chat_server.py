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
import re
import struct
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import parse_qs, urlparse

TOKEN = os.environ.get("CHAT_TOKEN", "sukikokona1212")
PORT = int(os.environ.get("CHAT_PORT", "8299"))
HISTORY_MAX = int(os.environ.get("CHAT_HISTORY", "300"))
CHANNELS_FILE = os.environ.get("CHAT_CHANNELS_FILE", "/opt/kokona-chat/channels.json")
DATA_DIR = os.environ.get("CHAT_DATA_DIR", "/opt/kokona-chat/data")
FSYNC = os.environ.get("CHAT_FSYNC", "1") not in ("0", "false", "no")
WS_GUID = "258EAFA5-E914-47DA-95CA-C5AB0DC85B11"
MAX_TEXT = 4000
RESERVED = {"ws", "stream", "send", "channels", "history", "health"}

_lock = threading.Lock()
_seq = [0]


# --------------------------------------------------------------------------
# 存储：每频道一个追加日志（JSONL）
#
# 为什么不用 SQLite：这里的数据只有「按时间追加」和「读最近 N 条」两种访问，
# 用不上关系查询、索引、事务。日志结构顺序写、追加 O(1)、崩溃最多坏最后一行
# （读取时直接跳过），文件本身 `tail -f` 就能看。每频道一个文件天然隔离，
# 以后上多用户只是再多几个文件；真要换引擎，只替换这一层。
# --------------------------------------------------------------------------
def tail_lines(path, n, block=16384):
    """只从文件尾部读最后 n 行，避免把整个文件载入内存"""
    try:
        with open(path, "rb") as fh:
            fh.seek(0, os.SEEK_END)
            pos = fh.tell()
            if pos == 0:
                return []
            data = b""
            while pos > 0 and data.count(b"\n") <= n:
                step = min(block, pos)
                pos -= step
                fh.seek(pos)
                data = fh.read(step) + data
        lines = data.split(b"\n")
        if pos > 0:
            lines = lines[1:]                 # 首行可能是半截，丢掉
        lines = [l for l in lines if l.strip()]
        return [l.decode("utf-8", "replace") for l in lines[-n:]]
    except OSError:
        return []


class MessageStore(object):
    """追加写 + 尾部读。单进程使用，写操作自带锁。"""

    MAX_BYTES = 4 * 1024 * 1024      # 单文件超 4MB 触发压缩
    KEEP_LINES = 2000                # 压缩后保留最后多少条

    def __init__(self, root):
        self.root = root
        os.makedirs(root, exist_ok=True)
        self._lock = threading.Lock()
        self.max_id = 0              # 重启后用于恢复自增 id

    def _path(self, cid):
        safe = re.sub(r"[^0-9A-Za-z_-]", "_", str(cid))[:40] or "1"
        return os.path.join(self.root, "ch-%s.jsonl" % safe)

    def append(self, msg):
        line = json.dumps(msg, ensure_ascii=False, separators=(",", ":")) + "\n"
        path = self._path(msg["ch"])
        with self._lock:
            try:
                with open(path, "a", encoding="utf-8") as fh:
                    fh.write(line)
                    fh.flush()
                    if FSYNC:
                        os.fsync(fh.fileno())
                try:
                    self.max_id = max(self.max_id, int(msg.get("id") or 0))
                except (TypeError, ValueError):
                    pass
                if os.path.getsize(path) > self.MAX_BYTES:
                    self._compact(path)
            except OSError:
                pass

    def tail(self, cid, n):
        out = []
        for line in tail_lines(self._path(cid), n):
            try:
                msg = json.loads(line)
            except ValueError:
                continue                  # 崩溃残留的半行，跳过即可
            if isinstance(msg, dict):
                out.append(msg)
        for m in out:
            try:
                self.max_id = max(self.max_id, int(m.get("id") or 0))
            except (TypeError, ValueError):
                pass
        return out

    def clear(self, cid):
        with self._lock:
            try:
                os.remove(self._path(cid))
            except OSError:
                pass

    def _compact(self, path):
        keep = tail_lines(path, self.KEEP_LINES)
        tmp = path + ".tmp"
        try:
            with open(tmp, "w", encoding="utf-8") as fh:
                fh.writelines(l + "\n" for l in keep)
            os.replace(tmp, path)
        except OSError:
            try:
                os.remove(tmp)
            except OSError:
                pass


_store = None


# --------------------------------------------------------------------------
# 频道
# --------------------------------------------------------------------------
class Channel(object):
    __slots__ = ("cid", "name", "ws", "sse", "history")

    def __init__(self, cid, name, store=None):
        self.cid = cid
        self.name = name
        self.ws = []
        self.sse = []
        self.history = collections.deque(maxlen=HISTORY_MAX)
        if store is not None:
            for msg in store.tail(cid, HISTORY_MAX):
                self.history.append(msg)


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
            ch = Channel(cid, "频道 %s" % cid, _store)
            _channels[cid] = ch
            _write_meta()
        return ch


def init_channels():
    global _store
    _store = MessageStore(DATA_DIR)
    meta = _read_meta()
    for cid in ["1", "2"]:
        meta.setdefault(cid, "频道 %s" % cid)
    with _lock:
        for cid, name in meta.items():
            _channels[cid] = Channel(cid, name, _store)
    _write_meta()
    _seq[0] = _store.max_id          # 重启后 id 接着历史走，不会撞号


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
    if _store is not None:
        try:
            _store.append(msg)       # 先落盘再广播：发出去的一定留得住
        except Exception:
            pass
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
    overflow-wrap:anywhere;
  }
  .msg.a{align-self:flex-start; border-bottom-left-radius:4px}
  .msg.b{
    align-self:flex-end; border-bottom-right-radius:4px;
    background:rgba(242,182,187,.13); border-color:rgba(242,182,187,.32);
  }
  .meta{display:block; font-size:10px; color:var(--muted); margin-bottom:3px; letter-spacing:.06em}
  .empty{color:var(--muted); text-align:center; margin:auto 0; font-size:12.5px; line-height:1.9}

  /* --- 顶部提示 --- */
  .toast{
    position:fixed; left:50%; top:14px; z-index:60;
    transform:translate(-50%, -10px);
    max-width:min(92vw,420px); padding:8px 15px; border-radius:999px;
    background:rgba(22,24,33,.96); border:1px solid var(--line);
    color:var(--ink); font-size:12px; text-align:center; letter-spacing:.02em;
    box-shadow:0 10px 30px rgba(0,0,0,.45);
    opacity:0; pointer-events:none;
    transition:opacity .2s ease, transform .2s ease;
  }
  .toast.show{opacity:1; transform:translate(-50%, 0)}
  .toast.ok{border-color:rgba(242,182,187,.55)}

  /* --- 回到未读 / 我的最后一条 --- */
  .jumps{
    position:fixed; right:14px; z-index:55;
    display:flex; flex-direction:column; gap:8px; align-items:flex-end;
    opacity:0; pointer-events:none; transition:opacity .18s ease;
  }
  .jumps.show{opacity:1; pointer-events:auto}
  .jumps button{
    display:inline-flex; align-items:center; height:34px; padding:0 13px;
    border-radius:999px; cursor:pointer; font:inherit; font-size:12px;
    border:1px solid rgba(242,182,187,.45); background:rgba(25,27,35,.97);
    color:var(--ink); box-shadow:0 8px 24px rgba(0,0,0,.45);
  }
  .jumps button.accent{
    border-color:rgba(242,182,187,.8); background:rgba(242,182,187,.2);
  }
  .jumps button[hidden]{display:none}

  /* --- 轮次结束分隔 --- */
  .md-turn{
    display:flex; align-items:center; gap:10px;
    margin:12px 2px; color:rgba(248,247,245,.42);
    font-size:11px; letter-spacing:.14em; align-self:stretch;
  }
  .md-turn::before,.md-turn::after{
    content:""; flex:1; height:1px; background:rgba(255,255,255,.12);
  }

  /* --- Markdown 渲染结果 --- */
  .md-p{margin:0}
  .md-p + .md-p{margin-top:5px}
  .md-h{font-weight:640; font-size:14.5px; margin:7px 0 4px; letter-spacing:.01em}
  .md-h:first-child{margin-top:0}
  .md-ul,.md-ol{margin:5px 0; padding-left:19px}
  .md-ul li,.md-ol li{margin:2px 0}
  .md-quote{
    margin:5px 0; padding:1px 0 1px 9px;
    border-left:2px solid rgba(242,182,187,.45); color:rgba(248,247,245,.72);
  }
  .md-code{
    margin:6px 0; padding:9px 11px; border-radius:7px;
    background:rgba(0,0,0,.42); border:1px solid rgba(255,255,255,.07);
    overflow-x:auto; white-space:pre;
    font-family:ui-monospace,SFMono-Regular,Menlo,Consolas,monospace;
    font-size:12px; line-height:1.6; -webkit-overflow-scrolling:touch;
  }
  .md-ic{
    padding:1px 5px; border-radius:4px; background:rgba(0,0,0,.42);
    font-family:ui-monospace,SFMono-Regular,Menlo,Consolas,monospace; font-size:.92em;
  }
  .md-h1{font-size:16px}
  .md-h2{font-size:15px}
  .msg hr{border:0; border-top:1px solid var(--line); margin:9px 0}
  .msg a{color:var(--accent); text-decoration:underline; text-underline-offset:2px}
  .msg strong{font-weight:650; color:var(--ink)}
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

<div id="toast" class="toast" role="status" aria-live="polite"></div>

<div id="jumps" class="jumps">
  <button id="jumpMine" type="button" hidden>↑ 我的最后一条</button>
  <button id="jumpUnread" type="button" class="accent" hidden>↓ 条新消息</button>
</div>

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
/* ---------------------------------------------------------------
   极简 Markdown 渲染（零依赖）
   安全前提：先转义 HTML，再替换标记；链接只放行 http(s)/mailto。
   --------------------------------------------------------------- */
function mdEsc(s){
  return String(s).replace(/[&<>"']/g, function(c){
    return {'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c];
  });
}

function mdInline(s){
  s = mdEsc(s);

  // 行内代码先抽出来占位，免得里面的符号被后面的规则吃掉
  var codes = [];
  s = s.replace(/`([^`]+)`/g, function(_, c){
    codes.push(c);
    return '\u0000C' + (codes.length - 1) + '\u0000';
  });

  // 链接：只认 http/https/mailto，javascript: 之类原样留着不变成链接
  s = s.replace(/\[([^\]]+)\]\(([^)\s]+)\)/g, function(m, text, url){
    if (!/^(https?:\/\/|mailto:)/i.test(url)) return m;
    return '<a href="' + url + '" target="_blank" rel="noreferrer noopener">' + text + '</a>';
  });

  s = s.replace(/\*\*([^*]+)\*\*/g, '<strong>$1</strong>');
  s = s.replace(/__([^_]+)__/g, '<strong>$1</strong>');
  s = s.replace(/(^|[^*])\*([^*\n]+)\*/g, '$1<em>$2</em>');
  s = s.replace(/(^|[^_])_([^_\n]+)_/g, '$1<em>$2</em>');
  s = s.replace(/~~([^~]+)~~/g, '<del>$1</del>');

  s = s.replace(/\u0000C(\d+)\u0000/g, function(_, i){
    return '<code class="md-ic">' + codes[+i] + '</code>';
  });
  return s;
}

function mdBlock(text){
  var lines = text.split('\n');
  var html = [];
  var list = '';

  function closeList(){
    if (list) { html.push('</' + list + '>'); list = ''; }
  }

  for (var i = 0; i < lines.length; i++) {
    var line = lines[i];

    if (/^\s*$/.test(line)) { closeList(); continue; }

    var h = line.match(/^\s{0,3}(#{1,6})\s+(.*)$/);
    if (h) {
      closeList();
      var n = h[1].length;
      var cls = n === 1 ? 'md-h md-h1' : (n === 2 ? 'md-h md-h2' : 'md-h');
      html.push('<div class="' + cls + '">' + mdInline(h[2]) + '</div>');
      continue;
    }

    if (/^\s{0,3}(-{3,}|\*{3,}|_{3,})\s*$/.test(line)) {
      closeList(); html.push('<hr>'); continue;
    }

    var q = line.match(/^\s{0,3}>\s?(.*)$/);
    if (q) {
      closeList();
      html.push('<div class="md-quote">' + mdInline(q[1]) + '</div>');
      continue;
    }

    var ul = line.match(/^\s*[-*+]\s+(.*)$/);
    if (ul) {
      if (list !== 'ul') { closeList(); html.push('<ul class="md-ul">'); list = 'ul'; }
      html.push('<li>' + mdInline(ul[1]) + '</li>');
      continue;
    }

    var ol = line.match(/^\s*\d{1,3}[.)]\s+(.*)$/);
    if (ol) {
      if (list !== 'ol') { closeList(); html.push('<ol class="md-ol">'); list = 'ol'; }
      html.push('<li>' + mdInline(ol[1]) + '</li>');
      continue;
    }

    closeList();
    html.push('<div class="md-p">' + mdInline(line) + '</div>');
  }

  closeList();
  return html.join('');
}

function renderMd(src){
  var text = String(src == null ? '' : src).replace(/\r\n?/g, '\n');
  if (!text) return '';
  var chunks = text.split('```');
  var out = [];

  for (var i = 0; i < chunks.length; i++) {
    var part = chunks[i];
    if (i % 2 === 1) {
      // 代码块；首行若是语言标识就丢掉（不做高亮）
      part = part.replace(/^\n/, '');
      var nl = part.indexOf('\n');
      if (nl > -1 && /^[A-Za-z0-9_+-]{1,15}$/.test(part.slice(0, nl).trim())) {
        part = part.slice(nl + 1);
      }
      out.push('<pre class="md-code">' + mdEsc(part.replace(/\n$/, '')) + '</pre>');
    } else {
      out.push(mdBlock(part));
    }
  }
  return out.join('');
}
</script>
<script>
(function(){
  var qs = new URLSearchParams(location.search);
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

  // ---------- 本地缓存 ----------
  var CACHE_KEY = 'kokona_chat_' + ch;
  var CACHE_MAX = 200;
  var seen = {};            // msg.id -> 1，用于去重（缓存 + SSE 重发）
  var cacheMsgs = [];
  var saveTimer = null;

  function saveCache(){
    clearTimeout(saveTimer);
    saveTimer = setTimeout(function(){
      try { localStorage.setItem(CACHE_KEY, JSON.stringify(cacheMsgs)); } catch(_) {}
    }, 350);
  }

  // ---------- 顶部提示 ----------
  var toastEl = document.getElementById('toast');
  var toastTimer = null;
  function showToast(text, ok, ms){
    toastEl.textContent = text;
    toastEl.classList.toggle('ok', !!ok);
    toastEl.classList.add('show');
    clearTimeout(toastTimer);
    toastTimer = setTimeout(function(){ toastEl.classList.remove('show'); }, ms || 1800);
  }

  // ---------- 滚动与跳转按钮 ----------
  var jumps = document.getElementById('jumps');
  var jumpMine = document.getElementById('jumpMine');
  var jumpUnread = document.getElementById('jumpUnread');
  var atBottom = true;
  var unread = 0;
  var firstUnreadEl = null;
  var mineEls = [];

  function nearBottom(){
    return log.scrollHeight - log.scrollTop - log.clientHeight < 90;
  }
  function scrollBottom(smooth){
    if (smooth) log.scrollTo({top: log.scrollHeight, behavior: 'smooth'});
    else log.scrollTop = log.scrollHeight;
  }
  function syncJumpPos(){
    var f = document.getElementById('form');
    jumps.style.bottom = (f.offsetHeight + 14) + 'px';
  }
  function updateJumps(){
    jumpMine.hidden = mineEls.length === 0;
    jumpUnread.hidden = unread === 0;
    jumpUnread.textContent = '↓ ' + unread + ' 条新消息';
    jumps.classList.toggle('show', unread > 0 || mineEls.length > 0);
  }

  log.addEventListener('scroll', function(){
    atBottom = nearBottom();
    if (atBottom && unread) { unread = 0; firstUnreadEl = null; }
    updateJumps();
  });

  jumpUnread.addEventListener('click', function(){
    if (firstUnreadEl && firstUnreadEl.isConnected) {
      firstUnreadEl.scrollIntoView({behavior: 'smooth', block: 'center'});
    } else {
      scrollBottom(true);
    }
    unread = 0; firstUnreadEl = null; updateJumps();
  });

  jumpMine.addEventListener('click', function(){
    var el = mineEls[mineEls.length - 1];
    if (el && el.isConnected) el.scrollIntoView({behavior: 'smooth', block: 'center'});
    unread = 0; firstUnreadEl = null; updateJumps();
  });

  // ---------- 渲染 ----------
  // 轮次结束标记：短句且同时含「本轮/这轮」和「结束/完成」→ 显示成一条分隔
  function isTurnEnd(text){
    var t = String(text || '').trim();
    if (!t || t.length > 30) return false;
    return /(本轮|轮次|这一轮|这轮)/.test(t) && /(结束|完成|收尾)/.test(t);
  }

  function appendMsg(msg, live){
    if (empty && empty.parentNode) empty.parentNode.removeChild(empty);

    var el = document.createElement('div');

    if (isTurnEnd(msg.text)) {
      el.className = 'md-turn';
      el.textContent = '本轮对话结束';
    } else {
      el.className = 'msg ' + (msg.from === 'B' ? 'b' : 'a');
      var meta = document.createElement('span');
      meta.className = 'meta';
      var t = new Date(msg.ts);
      meta.textContent = (msg.from === 'B' ? NAME_B : NAME_A) + ' · ' +
        t.toLocaleTimeString('zh-CN', {hour12: false});
      var body = document.createElement('span');
      body.innerHTML = renderMd(msg.text);
      el.appendChild(meta);
      el.appendChild(body);
      if (msg.from === 'B') mineEls.push(el);
    }

    el.setAttribute('data-id', msg.id);
    log.appendChild(el);

    if (live) {
      if (atBottom) {
        scrollBottom(false);
      } else {
        unread++;
        if (!firstUnreadEl) firstUnreadEl = el;
        updateJumps();
      }
    }
    return el;
  }

  // ---------- 从缓存恢复 ----------
  function loadCache(){
    try {
      var raw = localStorage.getItem(CACHE_KEY);
      if (!raw) return 0;
      var arr = JSON.parse(raw);
      if (!Array.isArray(arr)) return 0;
      var n = 0;
      for (var i = 0; i < arr.length; i++) {
        var mm = arr[i];
        if (!mm || mm.id == null || seen[mm.id]) continue;
        seen[mm.id] = 1;
        cacheMsgs.push(mm);
        appendMsg(mm, false);
        n++;
      }
      return n;
    } catch (_) { return 0; }
  }

  // 先用本地缓存铺底，SSE 只补增量
  var cachedCount = loadCache();
  if (cachedCount) {
    showToast('已加载 ' + cachedCount + ' 条缓存', false, 1200);
    scrollBottom(false);
  }

  // ---------- 实时流 ----------
  var metaTotal = -1;
  var received = 0;
  var syncDone = false;

  var es = new EventSource('/chat/stream?ch=' + encodeURIComponent(ch));
  es.onopen = function(){
    statusEl.textContent = '已连接 · ' + NAME_B;
    statusEl.classList.add('on');
  };
  es.onerror = function(){
    statusEl.textContent = '重连中…';
    statusEl.classList.remove('on');
  };

  es.addEventListener('meta', function(e){
    try {
      var d = JSON.parse(e.data);
      metaTotal = d.count || 0;
      if (metaTotal === 0) {
        syncDone = true;
        showToast(cacheMsgs.length ? '已是最新' : '这个频道还没有消息', true, 1600);
      } else {
        showToast('同步中… 0/' + metaTotal, false, 8000);
      }
    } catch (_) {}
  });

  es.onmessage = function(e){
    var msg;
    try { msg = JSON.parse(e.data); } catch (_) { return; }
    if (!msg || msg.id == null) return;

    received++;
    if (!seen[msg.id]) {
      seen[msg.id] = 1;
      cacheMsgs.push(msg);
      if (cacheMsgs.length > CACHE_MAX) cacheMsgs.splice(0, cacheMsgs.length - CACHE_MAX);
      appendMsg(msg, syncDone);      // 同步阶段不逐条滚，最后一次到位
      saveCache();
    }

    if (!syncDone && metaTotal > 0) {
      if (received >= metaTotal) {
        syncDone = true;
        scrollBottom(false);
        showToast(metaTotal + ' 条已同步', true, 1600);
      } else {
        showToast('同步中… ' + received + '/' + metaTotal, false, 8000);
      }
    }
  };

  // ---- 输入框：随内容长高，最多五行，之后内部滚动 ----
  function autoGrow(){
    input.style.height = 'auto';
    var need = input.scrollHeight;
    input.style.height = Math.min(need, MAX_INPUT_H) + 'px';
    input.style.overflowY = need > MAX_INPUT_H ? 'auto' : 'hidden';
    syncJumpPos();
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
    fetch('/chat/send?ch=' + encodeURIComponent(ch), {
      method: 'POST',
      headers: {'Content-Type': 'application/json'},
      body: JSON.stringify({text: text})
    }).then(function(){
      // 自己发完一定回到最新处
      atBottom = true; unread = 0; firstUnreadEl = null;
      scrollBottom(true); updateJumps();
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
    fetch('/chat/channels')
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
    fetch('/chat/channels/rename?ch=' + encodeURIComponent(ch), {
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
    fetch('/chat/channels/new', {method:'POST'})
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
  window.addEventListener('resize', syncJumpPos);

  // 首屏就拉一次频道信息，让按钮和标题立刻显示真实频道名
  loadChannels();
  autoGrow();
  syncJumpPos();
  updateJumps();
})();
</script>
</body>
</html>
"""


LOGIN_PAGE = r"""<!doctype html>
<html lang="zh-CN">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta name="theme-color" content="#11131a">
<title>Kokona Chat · 登录</title>
<style>
  :root{--bg:#11131a;--panel:#191b23;--ink:#f4f2ef;--muted:#8d8f9c;
        --accent:#f2b6bb;--line:#2a2d38}
  *{box-sizing:border-box}
  body{
    margin:0;min-height:100vh;display:flex;align-items:center;justify-content:center;
    background:var(--bg);color:var(--ink);padding:24px;
    font:14px/1.6 "Noto Sans SC","PingFang SC","Microsoft YaHei",system-ui,sans-serif;
  }
  .card{
    width:min(360px,100%);padding:28px 26px;border:1px solid var(--line);
    border-radius:14px;background:var(--panel);box-shadow:0 20px 50px rgba(0,0,0,.35);
  }
  h1{margin:0 0 6px;font-size:17px;font-weight:620;letter-spacing:.02em}
  p{margin:0 0 18px;color:var(--muted);font-size:12.5px}
  input{
    width:100%;padding:11px 13px;border-radius:9px;border:1px solid var(--line);
    background:#0e1016;color:var(--ink);font:inherit;outline:none;
  }
  input:focus{border-color:rgba(242,182,187,.6)}
  button{
    margin-top:12px;width:100%;height:42px;border-radius:9px;cursor:pointer;font:inherit;
    border:1px solid rgba(242,182,187,.55);background:rgba(242,182,187,.18);color:var(--ink);
  }
  button:active{background:rgba(242,182,187,.34)}
  .err{margin:11px 0 0;color:#ff9b9b;font-size:12px}
</style>
</head>
<body>
<form class="card" method="post" action="/chat/login">
  <h1>Kokona Chat</h1>
  <p>输入访问 token 继续（记住后不用再输）</p>
  <input type="password" name="token" placeholder="token" autofocus
         autocomplete="current-password" spellcheck="false">
  <input type="hidden" name="next" value="__NEXT__">
  <button type="submit">进入</button>
  __ERROR__
</form>
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
        if auth.lower().startswith("bearer ") and auth[7:].strip() == TOKEN:
            return True
        return self._cookie_token() == TOKEN

    def _cookie_token(self):
        raw = self.headers.get("Cookie") or ""
        for part in raw.split(";"):
            k, _, v = part.strip().partition("=")
            if k == "chat_token":
                return v
        return None

    def _set_cookie(self):
        cookie = "chat_token=%s; Path=/; Max-Age=31536000; HttpOnly; SameSite=Lax" % TOKEN
        if (self.headers.get("X-Forwarded-Proto") or "").lower() == "https":
            cookie += "; Secure"
        self.send_header("Set-Cookie", cookie)

    def _serve_page(self):
        """页面：URL 带正确 token 时种 cookie 并跳到干净地址；否则看 cookie；都没有给登录页"""
        q = self._qs()
        if q.get("token", [""])[0] == TOKEN:
            target = urlparse(self.path).path or "/chat/"
            self.send_response(302)
            self.send_header("Location", target)
            self._set_cookie()
            self.send_header("Content-Length", "0")
            self.end_headers()
            return
        if self._cookie_token() == TOKEN:
            return self._text(200, PAGE, "text/html; charset=utf-8")
        return self._login("")

    def _login(self, error="", next_path=None):
        import html as _html
        if next_path is None:
            next_path = urlparse(self.path).path or "/chat/"
        err_html = ('<p class="err">%s</p>' % _html.escape(error)) if error else ""
        body = (LOGIN_PAGE
                .replace("__NEXT__", _html.escape(next_path, quote=True))
                .replace("__ERROR__", err_html))
        return self._text(200, body, "text/html; charset=utf-8")

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

        if p in ("/", "/chat") or (
            p.startswith("/chat/") and p.count("/") == 2 and p.split("/")[2] not in RESERVED
        ):
            return self._serve_page()

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

        if p in ("/chat/login", "/login"):
            try:
                length = int(self.headers.get("Content-Length") or 0)
            except ValueError:
                length = 0
            raw = self.rfile.read(length) if length > 0 else b""
            form = parse_qs(raw.decode("utf-8", "replace"))
            token = (form.get("token") or [""])[0]
            nxt = (form.get("next") or ["/chat/"])[0]
            if not nxt.startswith("/") or nxt.startswith("//"):
                nxt = "/chat/"                     # 防开放重定向
            if token != TOKEN:
                time.sleep(0.4)                    # 拖一下猜 token 的节奏
                return self._login("token 不对，再试一次", nxt)
            self.send_response(302)
            self.send_header("Location", nxt)
            self._set_cookie()
            self.send_header("Content-Length", "0")
            self.end_headers()
            return

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

        if p in ("/chat/channels/clear", "/channels/clear"):
            if not self._token_ok():
                return self._json(401, {"error": "bad token"})
            ch = get_channel(self._ch_param(), create=False)
            if ch is None:
                return self._json(404, {"error": "no such channel"})
            with _lock:
                ch.history.clear()
            if _store is not None:
                _store.clear(ch.cid)
            return self._json(200, {"ok": True, "id": ch.cid, "cleared": True})

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

            # 先告诉前端这批历史共多少条，方便显示同步进度
            self.wfile.write(("event: meta\ndata: "
                              + json.dumps({"ch": ch.cid, "count": len(hist)}, ensure_ascii=False)
                              + "\n\n").encode("utf-8"))
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
