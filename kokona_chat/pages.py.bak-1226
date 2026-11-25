"""页面模板：全部内联 CSS/JS，减少请求数（低配设备友好）。"""

import json

from . import config


def j(obj):
    return json.dumps(obj, ensure_ascii=False).replace("</", "<\\/")


BASE_CSS = """
:root{
  --bg:#f2f2f2;--panel:#fff;--line:#e8e8e8;--text:#191919;--sub:#8a8a8a;
  --brand:#07c160;--brand-d:#06a851;--danger:#fa5151;--soft:#f7f7f7;
  --bubble-me:#95ec69;--bubble-other:#fff;--radius:10px;
}
*{box-sizing:border-box;-webkit-tap-highlight-color:transparent}
html,body{margin:0;padding:0;height:100%}
body{
  font-family:-apple-system,BlinkMacSystemFont,"PingFang SC","Microsoft YaHei","Helvetica Neue",sans-serif;
  background:var(--bg);color:var(--text);font-size:15px;line-height:1.5;
  -webkit-font-smoothing:antialiased;
}
button,input,textarea{font-family:inherit;font-size:inherit;color:inherit}
button{cursor:pointer;border:0;background:none;padding:0}
a{color:var(--brand-d);text-decoration:none}
.hidden{display:none!important}

/* ---------- 登录/注册 ---------- */
.auth-wrap{min-height:100%;display:flex;align-items:center;justify-content:center;padding:24px 16px;
  background:linear-gradient(160deg,#eafaf0 0%,#f2f2f2 40%,#f2f2f2 100%)}
.auth-card{width:100%;max-width:400px;background:var(--panel);border-radius:18px;padding:28px 22px 24px;
  box-shadow:0 8px 40px rgba(0,0,0,.06)}
.auth-logo{width:62px;height:62px;border-radius:18px;background:var(--brand);color:#fff;display:flex;
  align-items:center;justify-content:center;font-size:26px;font-weight:700;margin:0 auto 14px}
.auth-title{text-align:center;font-size:20px;font-weight:600;margin:0 0 4px}
.auth-sub{text-align:center;color:var(--sub);font-size:13px;margin:0 0 22px}
.field{margin-bottom:14px}
.field label{display:block;font-size:13px;color:var(--sub);margin-bottom:6px}
.field input{width:100%;padding:12px 13px;border:1px solid var(--line);border-radius:10px;background:var(--soft);
  outline:none;transition:border-color .15s,background .15s}
.field input:focus{border-color:var(--brand);background:#fff}
.btn{display:flex;align-items:center;justify-content:center;width:100%;padding:13px;border-radius:10px;
  background:var(--brand);color:#fff;font-weight:600;font-size:16px}
.btn:active{background:var(--brand-d)}
.btn[disabled]{opacity:.55}
.btn-ghost{background:transparent;color:var(--brand-d);font-weight:500;font-size:14px}
.auth-foot{display:flex;justify-content:space-between;margin-top:16px;font-size:13px;color:var(--sub)}
.msg-line{min-height:20px;font-size:13px;color:var(--danger);margin:4px 0 10px}
.msg-line.ok{color:var(--brand-d)}
.code-row{display:flex;gap:8px}
.code-row input{flex:1}
.code-btn{white-space:nowrap;padding:0 14px;border-radius:10px;border:1px solid var(--line);
  background:var(--soft);font-size:14px;color:var(--brand-d)}
.code-btn[disabled]{color:var(--sub)}
.dev-code{margin-top:10px;padding:10px 12px;border-radius:10px;background:#fff8e1;color:#8a6d00;font-size:13px;
  border:1px solid #ffe082}

/* ---------- 主界面 ---------- */
.app{display:grid;grid-template-columns:340px 1fr;height:100dvh;overflow:hidden}
.sidebar{display:flex;flex-direction:column;background:var(--panel);border-right:1px solid var(--line);min-width:0}
.side-head{display:flex;align-items:center;justify-content:space-between;padding:14px 14px 8px}
.side-head .brand{font-weight:700;font-size:17px}
.side-search{padding:0 12px 8px}
.side-search input{width:100%;padding:8px 12px;border-radius:8px;border:1px solid var(--line);
  background:var(--soft);outline:none;font-size:14px}
.conv-list{flex:1;overflow-y:auto;overscroll-behavior:contain}
.conv{display:flex;gap:10px;padding:11px 14px;align-items:center;position:relative}
.conv:active{background:#ececec}
.conv.on{background:#e6f7ec}
.avatar{width:44px;height:44px;border-radius:8px;background:#c9c9c9;color:#fff;display:flex;
  align-items:center;justify-content:center;font-weight:600;font-size:16px;flex:0 0 auto;overflow:hidden}
.avatar img{width:100%;height:100%;object-fit:cover}
.avatar.g{background:#f0a020}
.avatar.sm{width:34px;height:34px;font-size:13px;border-radius:7px}
.conv-body{flex:1;min-width:0}
.conv-top{display:flex;justify-content:space-between;align-items:baseline;gap:6px}
.conv-name{font-weight:500;font-size:15px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}
.conv-time{font-size:11px;color:var(--sub);flex:0 0 auto}
.conv-last{font-size:13px;color:var(--sub);overflow:hidden;text-overflow:ellipsis;white-space:nowrap}
.badge{position:absolute;left:46px;top:4px;min-width:18px;height:18px;padding:0 5px;border-radius:9px;
  background:var(--danger);color:#fff;font-size:11px;display:flex;align-items:center;justify-content:center}
.tabbar{display:flex;border-top:1px solid var(--line);background:var(--panel);padding-bottom:env(safe-area-inset-bottom)}
.tabbar button{flex:1;padding:10px 0 8px;font-size:11px;color:var(--sub);display:flex;flex-direction:column;
  align-items:center;gap:2px}
.tabbar button.on{color:var(--brand-d)}
.tabbar .ti{font-size:19px;line-height:1}

.main{display:flex;flex-direction:column;min-width:0;background:var(--bg);position:relative}
.chat-head{display:flex;align-items:center;gap:8px;padding:10px 12px;background:var(--panel);
  border-bottom:1px solid var(--line);padding-top:calc(10px + env(safe-area-inset-top))}
.chat-title{flex:1;text-align:center;font-weight:600;font-size:16px;overflow:hidden;
  text-overflow:ellipsis;white-space:nowrap}
.icon-btn{width:34px;height:34px;border-radius:8px;display:flex;align-items:center;justify-content:center;
  font-size:20px;color:var(--text);flex:0 0 auto}
.icon-btn:active{background:#eee}
.back{font-size:26px;line-height:1}
.msgs{flex:1;overflow-y:auto;padding:14px 12px 6px;overscroll-behavior:contain;-webkit-overflow-scrolling:touch}
.day-sep{text-align:center;margin:12px 0 10px}
.day-sep span{font-size:11px;color:var(--sub);background:rgba(0,0,0,.04);padding:2px 8px;border-radius:6px}
.row{display:flex;margin-bottom:12px;align-items:flex-start;gap:8px}
.row.me{flex-direction:row-reverse}
.bubble{max-width:min(74%,560px);padding:9px 12px;border-radius:var(--radius);background:var(--bubble-other);
  word-break:break-word;white-space:pre-wrap;box-shadow:0 1px 1px rgba(0,0,0,.04);position:relative}
.row.me .bubble{background:var(--bubble-me)}
.b-meta{font-size:11px;color:var(--sub);margin-bottom:3px}
.b-time{font-size:10px;color:var(--sub);margin-top:3px;text-align:right}
.sys{text-align:center;font-size:12px;color:var(--sub);margin:10px 0}
.composer{display:flex;gap:8px;padding:8px 10px;background:var(--panel);border-top:1px solid var(--line);
  align-items:flex-end;padding-bottom:calc(8px + env(safe-area-inset-bottom))}
.composer textarea{flex:1;resize:none;max-height:120px;min-height:40px;padding:9px 12px;border-radius:9px;
  border:1px solid var(--line);background:var(--soft);outline:none;line-height:1.4;overflow-y:auto}
.composer textarea:focus{border-color:var(--brand);background:#fff}
.send-btn{padding:0 16px;height:40px;border-radius:9px;background:var(--brand);color:#fff;font-weight:600}
.send-btn:active{background:var(--brand-d)}

/* ---------- 面板（通讯录/我/设置） ---------- */
.panel{flex:1;overflow-y:auto;padding:16px;overscroll-behavior:contain}
.panel h2{font-size:16px;margin:0 0 12px;font-weight:600}
.card{background:var(--panel);border-radius:12px;padding:4px 0;margin-bottom:14px;overflow:hidden}
.item{display:flex;align-items:center;gap:10px;padding:13px 14px;border-bottom:1px solid var(--line)}
.item:last-child{border-bottom:0}
.item:active{background:#f5f5f5}
.item .txt{flex:1;min-width:0}
.item .t1{font-size:15px}
.item .t2{font-size:12px;color:var(--sub);overflow:hidden;text-overflow:ellipsis;white-space:nowrap}
.item .arrow{color:#c8c8c8;font-size:18px}
.pill{font-size:11px;padding:2px 7px;border-radius:6px;background:#eef7f1;color:var(--brand-d)}
.pill.warn{background:#fff1f0;color:var(--danger)}
.pill.gray{background:#f0f0f0;color:var(--sub)}
.empty{text-align:center;color:var(--sub);font-size:13px;padding:40px 10px}
.mini-form{display:flex;flex-direction:column;gap:8px;padding:14px}
.mini-form input{padding:10px 12px;border:1px solid var(--line);border-radius:9px;background:var(--soft);outline:none}
.mini-form .btn{padding:10px;font-size:15px}

/* ---------- 弹层 ---------- */
.mask{position:fixed;inset:0;background:rgba(0,0,0,.42);display:flex;align-items:center;justify-content:center;
  padding:20px;z-index:60}
.sheet{width:100%;max-width:420px;background:var(--panel);border-radius:16px;overflow:hidden;
  max-height:82vh;display:flex;flex-direction:column}
.sheet-head{display:flex;align-items:center;justify-content:space-between;padding:14px 16px;border-bottom:1px solid var(--line)}
.sheet-head b{font-size:16px}
.sheet-body{overflow-y:auto;padding:0}
.sheet-foot{padding:12px 16px;border-top:1px solid var(--line);display:flex;gap:8px}
.sheet-foot .btn{padding:11px;font-size:15px}
.toast{position:fixed;left:50%;bottom:70px;transform:translateX(-50%);background:rgba(0,0,0,.78);color:#fff;
  padding:9px 16px;border-radius:20px;font-size:13px;z-index:90;max-width:80vw;text-align:center;
  opacity:0;transition:opacity .2s,transform .2s;pointer-events:none}
.toast.show{opacity:1;transform:translateX(-50%) translateY(-6px)}
.ann-bubble{position:fixed;right:16px;bottom:16px;background:var(--panel);border-radius:14px;padding:14px 16px;
  box-shadow:0 10px 40px rgba(0,0,0,.16);max-width:330px;z-index:70;border:1px solid var(--line)}
.ann-bubble b{display:block;font-size:14px;margin-bottom:4px}
.ann-bubble p{margin:0 0 10px;font-size:13px;color:#555;white-space:pre-wrap;max-height:40vh;overflow:auto}
.ann-bubble .btn{padding:8px;font-size:14px;border-radius:9px}

/* ---------- 移动端 ---------- */
@media(max-width:760px){
  .app{grid-template-columns:1fr}
  .main{display:none}
  body.chat-open .sidebar{display:none}
  body.chat-open .main{display:flex}
  body.panel-open .sidebar{display:none}
  body.panel-open .main{display:flex}
  .chat-head{padding-left:6px}
}
@media(min-width:761px){
  .chat-head .back{display:none}
}
"""


def _doc(title, body, extra_css="", extra_js="", base=None):
    if base is None:
        base = config.BASE or ""
    return """<!doctype html>
<html lang="zh-CN"><head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1,maximum-scale=1,viewport-fit=cover">
<meta name="theme-color" content="#07c160">
<title>%s</title>
<style>%s%s</style>
</head><body>
%s
<script>window.BASE=%s;</script>
<script>%s</script>
</body></html>""" % (title, BASE_CSS, extra_css, body, j(base), extra_js)


# ================================================================ 登录

LOGIN_JS = """
const msg = document.getElementById('msg');
function say(t, ok){ msg.textContent = t || ''; msg.className = 'msg-line' + (ok ? ' ok' : ''); }
document.getElementById('form').addEventListener('submit', async (e) => {
  e.preventDefault();
  const u = document.getElementById('username').value.trim();
  const p = document.getElementById('password').value;
  if (!u || !p) { say('请输入账号和密码'); return; }
  const btn = document.getElementById('submit');
  btn.disabled = true; btn.textContent = '登录中…';
  try {
    const r = await fetch(BASE + '/api/login', {
      method:'POST', headers:{'Content-Type':'application/json'},
      body: JSON.stringify({username:u, password:p})
    });
    const d = await r.json();
    if (!d.ok) { say(d.error || '登录失败'); return; }
    location.href = BASE + '/';
  } catch (err) {
    say('网络异常，请重试');
  } finally {
    btn.disabled = false; btn.textContent = '登录';
  }
});
"""


def login_page(base=None):
    body = """
<div class="auth-wrap"><div class="auth-card">
  <div class="auth-logo">心</div>
  <h1 class="auth-title">心夏 Chat</h1>
  <p class="auth-sub">登录后继续聊天</p>
  <form id="form" autocomplete="on">
    <div class="field"><label for="username">账号</label>
      <input id="username" name="username" autocomplete="username" placeholder="用户名或邮箱"></div>
    <div class="field"><label for="password">密码</label>
      <input id="password" name="password" type="password" autocomplete="current-password" placeholder="密码"></div>
    <div class="msg-line" id="msg"></div>
    <button class="btn" id="submit" type="submit">登录</button>
  </form>
  <div class="auth-foot">
    <a href="__BASE__/register">注册新账号</a>
    <a href="__BASE__/recover">忘记账号 / 密码</a>
  </div>
</div></div>
""".replace("__BASE__", config.BASE or "" if base is None else base)
    return _doc("登录 · 心夏 Chat", body, extra_js=LOGIN_JS, base=base)


REGISTER_JS = """
const msg = document.getElementById('msg');
const codeBtn = document.getElementById('code-btn');
const devBox = document.getElementById('dev-code');
let timer = null;
function say(t, ok){ msg.textContent = t || ''; msg.className = 'msg-line' + (ok ? ' ok' : ''); }
function cooldown(sec){
  let n = sec;
  codeBtn.disabled = true;
  codeBtn.textContent = n + 's';
  clearInterval(timer);
  timer = setInterval(() => {
    n -= 1;
    if (n <= 0) { clearInterval(timer); codeBtn.disabled = false; codeBtn.textContent = '获取验证码'; }
    else codeBtn.textContent = n + 's';
  }, 1000);
}
codeBtn.addEventListener('click', async () => {
  const email = document.getElementById('email').value.trim();
  if (!email) { say('先填邮箱'); return; }
  codeBtn.disabled = true;
  try {
    const r = await fetch(BASE + '/api/send_code', {
      method:'POST', headers:{'Content-Type':'application/json'},
      body: JSON.stringify({email:email, purpose:'register'})
    });
    const d = await r.json();
    if (!d.ok) { say(d.error); codeBtn.disabled = false; return; }
    if (d.dev_code) {
      devBox.classList.remove('hidden');
      devBox.textContent = '验证码：' + d.dev_code + '（' + (d.hint || '') + '）';
    }
    say('验证码已发送', true);
    cooldown(60);
  } catch (e) {
    say('网络异常，请重试'); codeBtn.disabled = false;
  }
});
document.getElementById('form').addEventListener('submit', async (e) => {
  e.preventDefault();
  const payload = {
    username: document.getElementById('username').value.trim(),
    email: document.getElementById('email').value.trim(),
    code: document.getElementById('code').value.trim(),
    password: document.getElementById('password').value,
  };
  const btn = document.getElementById('submit');
  btn.disabled = true; btn.textContent = '注册中…';
  try {
    const r = await fetch(BASE + '/api/register', {
      method:'POST', headers:{'Content-Type':'application/json'}, body: JSON.stringify(payload)
    });
    const d = await r.json();
    if (!d.ok) { say(d.error || '注册失败'); return; }
    location.href = BASE + '/';
  } catch (err) { say('网络异常，请重试'); }
  finally { btn.disabled = false; btn.textContent = '注册'; }
});
"""


def register_page(base=None):
    body = """
<div class="auth-wrap"><div class="auth-card">
  <div class="auth-logo">心</div>
  <h1 class="auth-title">注册账号</h1>
  <p class="auth-sub">需要邮箱验证</p>
  <form id="form">
    <div class="field"><label for="username">用户名</label>
      <input id="username" placeholder="2-20 位，字母/数字/中文"></div>
    <div class="field"><label for="email">邮箱</label>
      <input id="email" type="email" placeholder="用于接收验证码和找回密码"></div>
    <div class="field"><label for="code">邮箱验证码</label>
      <div class="code-row">
        <input id="code" inputmode="numeric" placeholder="6 位数字">
        <button class="code-btn" id="code-btn" type="button">获取验证码</button>
      </div>
    </div>
    <div class="dev-code hidden" id="dev-code"></div>
    <div class="field"><label for="password">密码</label>
      <input id="password" type="password" placeholder="至少 6 位"></div>
    <div class="msg-line" id="msg"></div>
    <button class="btn" id="submit" type="submit">注册</button>
  </form>
  <div class="auth-foot"><a href="__BASE__/login">已有账号，去登录</a><span></span></div>
</div></div>
""".replace("__BASE__", config.BASE or "" if base is None else base)
    return _doc("注册 · 心夏 Chat", body, extra_js=REGISTER_JS, base=base)


RECOVER_JS = """
const msg = document.getElementById('msg');
const tabA = document.getElementById('tab-a');
const tabB = document.getElementById('tab-b');
const formA = document.getElementById('form-a');
const formB = document.getElementById('form-b');
let mode = 'username';
function say(t, ok){ msg.textContent = t || ''; msg.className = 'msg-line' + (ok ? ' ok' : ''); }
function switchMode(m){
  mode = m;
  tabA.classList.toggle('on', m === 'username');
  tabB.classList.toggle('on', m === 'password');
  formA.classList.toggle('hidden', m !== 'username');
  formB.classList.toggle('hidden', m !== 'password');
  say('');
}
tabA.addEventListener('click', () => switchMode('username'));
tabB.addEventListener('click', () => switchMode('password'));

let timer = null;
function cooldown(btn, sec){
  let n = sec; btn.disabled = true; btn.textContent = n + 's';
  clearInterval(timer);
  timer = setInterval(() => {
    n -= 1;
    if (n <= 0){ clearInterval(timer); btn.disabled = false; btn.textContent = '获取验证码'; }
    else btn.textContent = n + 's';
  }, 1000);
}
async function sendCode(btn, purpose){
  const email = document.getElementById('email-' + (mode === 'username' ? 'a' : 'b')).value.trim();
  if (!email){ say('先填邮箱'); return; }
  btn.disabled = true;
  try{
    const r = await fetch(BASE + '/api/send_code', {method:'POST',
      headers:{'Content-Type':'application/json'}, body: JSON.stringify({email, purpose})});
    const d = await r.json();
    if (!d.ok){ say(d.error); btn.disabled = false; return; }
    if (d.dev_code){
      const box = document.getElementById('dev-' + (mode === 'username' ? 'a' : 'b'));
      box.classList.remove('hidden');
      box.textContent = '验证码：' + d.dev_code;
    }
    say('验证码已发送', true); cooldown(btn, 60);
  } catch(e){ say('网络异常'); btn.disabled = false; }
}
document.getElementById('code-a').addEventListener('click', function(){ sendCode(this, 'find_username'); });
document.getElementById('code-b').addEventListener('click', function(){ sendCode(this, 'reset_password'); });

formA.addEventListener('submit', async (e) => {
  e.preventDefault();
  const r = await fetch(BASE + '/api/recover/username', {method:'POST',
    headers:{'Content-Type':'application/json'}, body: JSON.stringify({
      email: document.getElementById('email-a').value.trim(),
      code: document.getElementById('code-a-in').value.trim()})});
  const d = await r.json();
  if (!d.ok){ say(d.error); return; }
  say('你的账号是：' + d.username, true);
});
formB.addEventListener('submit', async (e) => {
  e.preventDefault();
  const r = await fetch(BASE + '/api/recover/password', {method:'POST',
    headers:{'Content-Type':'application/json'}, body: JSON.stringify({
      email: document.getElementById('email-b').value.trim(),
      code: document.getElementById('code-b-in').value.trim(),
      new_password: document.getElementById('pw-b').value})});
  const d = await r.json();
  if (!d.ok){ say(d.error); return; }
  say('密码已重置，账号：' + d.username + '，可以去登录了', true);
});
"""


def recover_page(base=None):
    body = """
<div class="auth-wrap"><div class="auth-card">
  <div class="auth-logo">心</div>
  <h1 class="auth-title">找回</h1>
  <p class="auth-sub">通过邮箱验证</p>
  <div class="code-row" style="margin-bottom:14px">
    <button class="code-btn on" id="tab-a" style="flex:1">找回账号</button>
    <button class="code-btn" id="tab-b" style="flex:1">重置密码</button>
  </div>
  <form id="form-a">
    <div class="field"><label>注册邮箱</label><input id="email-a" type="email" placeholder="you@example.com"></div>
    <div class="field"><label>验证码</label>
      <div class="code-row"><input id="code-a-in" inputmode="numeric" placeholder="6 位数字">
      <button class="code-btn" id="code-a" type="button">获取验证码</button></div>
    </div>
    <div class="dev-code hidden" id="dev-a"></div>
    <div class="msg-line" id="msg"></div>
    <button class="btn" type="submit">查回我的账号</button>
  </form>
  <form id="form-b" class="hidden">
    <div class="field"><label>注册邮箱</label><input id="email-b" type="email" placeholder="you@example.com"></div>
    <div class="field"><label>验证码</label>
      <div class="code-row"><input id="code-b-in" inputmode="numeric" placeholder="6 位数字">
      <button class="code-btn" id="code-b" type="button">获取验证码</button></div>
    </div>
    <div class="dev-code hidden" id="dev-b"></div>
    <div class="field"><label>新密码</label><input id="pw-b" type="password" placeholder="至少 6 位"></div>
    <button class="btn" type="submit">重置密码</button>
  </form>
  <div class="auth-foot"><a href="__BASE__/login">返回登录</a><a href="__BASE__/register">注册新账号</a></div>
</div></div>
""".replace("__BASE__", config.BASE or "" if base is None else base)
    return _doc("找回账号 · 心夏 Chat", body, extra_css=".code-btn.on{background:#e6f7ec;border-color:#9ad9b4;color:#06a851}", extra_js=RECOVER_JS, base=base)


# ================================================================ 主界面

APP_BODY = """
<div class="app" id="app">
  <aside class="sidebar">
    <div class="side-head">
      <span class="brand" id="side-brand">聊天</span>
      <button class="icon-btn" id="btn-plus" data-act="plus" title="新建">＋</button>
    </div>
    <div class="side-search"><input id="search" placeholder="搜索会话" autocomplete="off"></div>
    <div class="conv-list" id="conv-list"></div>
    <nav class="tabbar">
      <button data-act="tab" data-tab="chats" class="on"><span class="ti">💬</span>消息</button>
      <button data-act="tab" data-tab="contacts"><span class="ti">👥</span>通讯录</button>
      <button data-act="tab" data-tab="me"><span class="ti">🙂</span>我的</button>
    </nav>
  </aside>
  <main class="main">
    <section class="chat-view hidden" id="chat-view">
      <header class="chat-head">
        <button class="icon-btn back" data-act="back">‹</button>
        <div class="chat-title" id="chat-title"></div>
        <button class="icon-btn" data-act="chat-setting">⋯</button>
      </header>
      <div class="msgs" id="msgs"></div>
      <div class="composer">
        <textarea id="input" rows="1" placeholder="发消息…" autocomplete="off"></textarea>
        <button class="send-btn" data-act="send">发送</button>
      </div>
    </section>
    <section class="panel hidden" id="panel-view"></section>
  </main>
</div>
<div class="toast" id="toast"></div>
"""

APP_JS = r"""
const $ = (s, r) => (r || document).querySelector(s);
const $$ = (s, r) => Array.prototype.slice.call((r || document).querySelectorAll(s));
const esc = (s) => String(s == null ? '' : s).replace(/[&<>"']/g, (c) => (
  { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]
));
const pad2 = (n) => (n < 10 ? '0' + n : '' + n);
const COARSE = window.matchMedia && window.matchMedia('(pointer:coarse)').matches;

const S = {
  me: ME, convs: [], cur: null, msgs: [],
  friends: [], blocks: [], subs: [], anns: [], tab: 'chats'
};

/* ---------------- 通用 ---------------- */

let toastTimer = null;
function toast(text) {
  const el = $('#toast');
  el.textContent = text;
  el.classList.add('show');
  clearTimeout(toastTimer);
  toastTimer = setTimeout(() => el.classList.remove('show'), 2200);
}

async function api(path, method, body) {
  const opt = { method: method || 'GET', headers: {}, cache: 'no-store' };
  if (body !== undefined) {
    opt.headers['Content-Type'] = 'application/json';
    opt.body = JSON.stringify(body);
  }
  const r = await fetch(BASE + path, opt);
  if (r.status === 401) { location.href = BASE + '/login'; throw new Error('401'); }
  let d;
  try { d = await r.json(); } catch (e) { throw new Error('响应异常'); }
  if (!d.ok) throw new Error(d.error || '操作失败');
  return d;
}

function fmtClock(ts) {
  const d = new Date(ts * 1000), n = new Date();
  const hm = pad2(d.getHours()) + ':' + pad2(d.getMinutes());
  if (d.toDateString() === n.toDateString()) return hm;
  const y = new Date(n.getTime() - 86400000);
  if (d.toDateString() === y.toDateString()) return '昨天 ' + hm;
  if (d.getFullYear() === n.getFullYear()) return (d.getMonth() + 1) + '月' + d.getDate() + '日 ' + hm;
  return d.getFullYear() + '年' + (d.getMonth() + 1) + '月' + d.getDate() + '日 ' + hm;
}

function fmtDay(ts) {
  const d = new Date(ts * 1000), n = new Date();
  if (d.toDateString() === n.toDateString()) return '今天';
  const y = new Date(n.getTime() - 86400000);
  if (d.toDateString() === y.toDateString()) return '昨天';
  if (d.getFullYear() === n.getFullYear()) return (d.getMonth() + 1) + '月' + d.getDate() + '日';
  return d.getFullYear() + '年' + (d.getMonth() + 1) + '月' + d.getDate() + '日';
}

function avatar(u, cls) {
  cls = cls || '';
  if (u && u.avatar) return '<div class="avatar ' + cls + '"><img src="' + esc(u.avatar) + '" alt=""></div>';
  const name = (u && (u.display_name || u.username)) || '?';
  return '<div class="avatar ' + cls + '">' + esc(String(name).slice(0, 1)) + '</div>';
}

function displayName(u) {
  return u ? (u.display_name || u.username) : '未知';
}

/* ---------------- 会话列表 ---------------- */

async function loadConvs(quiet) {
  try {
    const d = await api('/api/conversations');
    S.convs = d.conversations || [];
    renderConvs();
    if (S.cur) {
      const c = S.convs.find((x) => x.id === S.cur.id);
      if (c) { S.cur.title = c.title; const t = $('#chat-title'); if (t) t.textContent = c.title; }
    }
  } catch (e) {
    if (!quiet) toast(e.message);
  }
}

function renderConvs() {
  const kw = ($('#search').value || '').trim().toLowerCase();
  const list = S.convs.filter((c) => !kw || String(c.title || '').toLowerCase().indexOf(kw) >= 0);
  const box = $('#conv-list');
  if (!list.length) {
    box.innerHTML = '<div class="empty">还没有会话<br>点右上角 ＋ 开始聊天</div>';
    return;
  }
  box.innerHTML = list.map((c) => {
    const last = c.last ? String(c.last.body || '').slice(0, 40) : (c.kind === 'group' ? '群聊已创建' : '开始聊天吧');
    const av = c.kind === 'direct'
      ? avatar(c.peer)
      : '<div class="avatar g">' + esc(String(c.title || '群').slice(0, 1)) + '</div>';
    const badge = c.unread > 0 ? '<span class="badge">' + (c.unread > 99 ? '99+' : c.unread) + '</span>' : '';
    return '<div class="conv' + (S.cur && S.cur.id === c.id ? ' on' : '') + '" data-act="open-conv" data-id="' + c.id + '">'
      + av + '<div class="conv-body"><div class="conv-top"><span class="conv-name">' + esc(c.title)
      + '</span><span class="conv-time">' + (c.last ? fmtClock(c.last.created_at) : '')
      + '</span></div><div class="conv-last">' + esc(last) + '</div></div>' + badge + '</div>';
  }).join('');
}

/* ---------------- 聊天 ---------------- */

function showList() {
  document.body.classList.remove('chat-open', 'panel-open');
  if (!S.tab || S.tab === 'chats') renderConvs();
}

function convTitle(conv, members, meId) {
  if (conv.kind === 'direct') {
    const peer = conv.peer;
    return peer ? displayName(peer) : '私聊';
  }
  if (conv.kind === 'group') {
    const mem = (members || []).length;
    return conv.title + '（' + mem + '）';
  }
  return conv.title || '旧频道';
}

async function openConv(id) {
  try {
    const d = await api('/api/conversations/' + id);
    S.cur = d.conversation;
    S.cur.members = d.members || [];
    S.cur.title = convTitle(d.conversation, d.members, S.me.id);
    S.msgs = d.messages || [];
    $('#chat-title').textContent = S.cur.title;
    renderMsgs();
    $('#chat-view').classList.remove('hidden');
    $('#panel-view').classList.add('hidden');
    document.body.classList.add('chat-open');
    document.body.classList.remove('panel-open');
    scrollBottom(true);
    const c = S.convs.find((x) => x.id === id);
    if (c) { c.unread = 0; }
    renderConvs();
    api('/api/conversations/' + id + '/read', 'POST', {}).catch(() => {});
  } catch (e) {
    toast(e.message);
  }
}

function msgHtml(m) {
  const mine = S.me && m.sender_id === S.me.id;
  const who = mine ? '' : '<div class="b-meta">' + esc(displayName(m.sender)) + '</div>';
  return '<div class="row' + (mine ? ' me' : '') + '" data-mid="' + m.id + '">'
    + avatar(m.sender, 'sm')
    + '<div class="bubble">' + who + esc(m.body)
    + '<div class="b-time">' + fmtClock(m.created_at) + '</div></div></div>';
}

function renderMsgs() {
  const box = $('#msgs');
  if (!S.msgs.length) {
    box.innerHTML = '<div class="empty">还没有消息，打个招呼吧</div>';
    return;
  }
  let html = '', lastDay = '';
  for (let i = 0; i < S.msgs.length; i++) {
    const m = S.msgs[i];
    const day = new Date(m.created_at * 1000).toDateString();
    if (day !== lastDay) {
      lastDay = day;
      html += '<div class="day-sep"><span>' + fmtDay(m.created_at) + '</span></div>';
    }
    html += msgHtml(m);
  }
  box.innerHTML = html;
}

function nearBottom() {
  const b = $('#msgs');
  return b.scrollHeight - b.scrollTop - b.clientHeight < 140;
}

function scrollBottom(force) {
  const b = $('#msgs');
  if (!force && !nearBottom()) return;
  requestAnimationFrame(() => { b.scrollTop = b.scrollHeight; });
}

function appendMsg(m) {
  if (S.msgs.some((x) => x.id === m.id)) return;
  const box = $('#msgs');
  const stick = nearBottom();
  const prev = S.msgs[S.msgs.length - 1];
  S.msgs.push(m);
  const day = new Date(m.created_at * 1000).toDateString();
  if (!prev || new Date(prev.created_at * 1000).toDateString() !== day) {
    box.insertAdjacentHTML('beforeend', '<div class="day-sep"><span>' + fmtDay(m.created_at) + '</span></div>');
  }
  box.insertAdjacentHTML('beforeend', msgHtml(m));
  if (stick) scrollBottom(true);
}

function autoGrow(el) {
  el.style.height = 'auto';
  el.style.height = Math.min(el.scrollHeight, 120) + 'px';
}

async function sendMsg() {
  const el = $('#input');
  const body = el.value.trim();
  if (!body || !S.cur) return;
  el.value = '';
  autoGrow(el);
  try {
    const d = await api('/api/conversations/' + S.cur.id + '/messages', 'POST', { body: body });
    appendMsg(d.message);
    scrollBottom(true);
  } catch (e) {
    toast('没发出去：' + e.message);
    if (!el.value) el.value = body;
    autoGrow(el);
  }
}

/* ---------------- 实时流 ---------------- */

let es = null;
function connectSSE() {
  if (es) es.close();
  es = new EventSource(BASE + '/api/stream');
  es.onmessage = (e) => {
    let d;
    try { d = JSON.parse(e.data); } catch (err) { return; }
    if (d.type === 'message') {
      if (S.cur && S.cur.id === d.conv_id) {
        appendMsg(d.message);
        if (document.visibilityState === 'visible') {
          api('/api/conversations/' + d.conv_id + '/read', 'POST', {}).catch(() => {});
        }
      }
      loadConvs(true);
    } else if (d.type === 'conversation') {
      loadConvs(true);
    } else if (d.type === 'conversation_removed') {
      S.convs = S.convs.filter((c) => c.id !== d.conv_id);
      renderConvs();
      if (S.cur && S.cur.id === d.conv_id) { S.cur = null; showList(); $('#chat-view').classList.add('hidden'); }
    } else if (d.type === 'announcement') {
      loadAnns().then(() => popAnnouncement());
    } else if (d.type === 'friend') {
      loadFriends();
    }
  };
}

/* ---------------- 面板 ---------------- */

function showPanel(html) {
  const p = $('#panel-view');
  p.innerHTML = html;
  p.classList.remove('hidden');
  $('#chat-view').classList.add('hidden');
  document.body.classList.add('panel-open');
  document.body.classList.remove('chat-open');
}

function setTab(tab) {
  S.tab = tab;
  $$('.tabbar button').forEach((b) => b.classList.toggle('on', b.dataset.tab === tab));
  if (tab === 'contacts') { loadSubs().then(showContacts); }
  else if (tab === 'me') { showMe(); }
  else { showList(); $('#chat-view').classList.add('hidden'); $('#panel-view').classList.add('hidden'); loadConvs(true); }
}

async function loadFriends() {
  try {
    const d = await api('/api/friends');
    S.friends = d.friends || [];
    S.blocks = d.blocks || [];
    if (S.tab === 'contacts') showContacts();
  } catch (e) { /* 忽略 */ }
}

function showContacts() {
  const friendRows = S.friends.length
    ? S.friends.map((f) => '<div class="item" data-act="open-dm" data-id="' + f.id + '">'
        + avatar(f, 'sm') + '<div class="txt"><div class="t1">' + esc(displayName(f))
        + '</div><div class="t2">@' + esc(f.username) + '</div></div>'
        + '<span class="arrow">›</span></div>').join('')
    : '<div class="empty">还没有好友，去下面搜一个吧</div>';

  const groups = S.convs.filter((c) => c.kind === 'group');
  const groupRows = groups.length
    ? groups.map((g) => '<div class="item" data-act="open-conv" data-id="' + g.id + '">'
        + '<div class="avatar g sm">' + esc(String(g.title || '群').slice(0, 1)) + '</div>'
        + '<div class="txt"><div class="t1">' + esc(g.title) + '</div><div class="t2">'
        + (g.member_count || 0) + ' 人</div></div><span class="arrow">›</span></div>').join('')
    : '<div class="empty">还没有群聊</div>';

  const subRows = S.subs.length
    ? S.subs.map((s) => '<div class="item"><div class="txt"><div class="t1">' + esc(displayName(s))
        + '</div><div class="t2">@' + esc(s.username) + ' · 子账号</div></div>'
        + '<button class="code-btn" data-act="del-sub" data-id="' + s.id + '">删除</button></div>').join('')
    : '<div class="empty" style="padding:16px">还没有子账号</div>';

  const isSub = S.me.is_sub === 1;
  showPanel(
    '<h2>通讯录</h2>'
    + '<div class="side-search" style="padding:0 0 12px"><input id="uq" placeholder="搜索用户名加好友"></div>'
    + '<div id="user-results"></div>'
    + '<h2>好友（' + S.friends.length + '）</h2><div class="card">' + friendRows + '</div>'
    + '<h2>群聊（' + groups.length + '）</h2><div class="card">' + groupRows + '</div>'
    + (isSub ? '' : '<h2>我的子账号</h2><div class="card">' + subRows
        + '<div class="mini-form"><input id="sub-name" placeholder="子账号名（英文/数字）">'
        + '<input id="sub-pass" type="password" placeholder="子账号密码（≥6 位）">'
        + '<button class="btn" data-act="new-sub">创建子账号</button></div></div>')
  );

  const uq = $('#uq');
  let timer = null;
  uq.addEventListener('input', () => {
    clearTimeout(timer);
    timer = setTimeout(doSearch, 320);
  });
  loadSubs();
}

async function loadSubs() {
  if (S.me.is_sub === 1) return;
  try {
    const d = await api('/api/subs');
    S.subs = d.subs || [];
  } catch (e) { /* 忽略 */ }
}

async function doSearch() {
  const q = ($('#uq') && $('#uq').value || '').trim();
  const box = $('#user-results');
  if (!box) return;
  if (!q) { box.innerHTML = ''; return; }
  try {
    const d = await api('/api/search?q=' + encodeURIComponent(q));
    const users = d.users || [];
    if (!users.length) { box.innerHTML = '<div class="empty" style="padding:10px">没有找到用户</div>'; return; }
    box.innerHTML = '<div class="card">' + users.map((u) => {
      const btn = u.is_friend
        ? '<button class="code-btn" data-act="open-dm" data-id="' + u.id + '">聊天</button>'
        : '<button class="code-btn" data-act="add-friend" data-id="' + u.id + '">添加</button>';
      return '<div class="item">' + avatar(u, 'sm') + '<div class="txt"><div class="t1">' + esc(displayName(u))
        + '</div><div class="t2">@' + esc(u.username) + '</div></div>' + btn + '</div>';
    }).join('') + '</div>';
  } catch (e) { toast(e.message); }
}

function showMe() {
  const u = S.me;
  showPanel(
    '<h2>我的</h2>'
    + '<div class="card"><div class="item" data-act="edit-profile">' + avatar(u)
    + '<div class="txt"><div class="t1">' + esc(displayName(u)) + '</div>'
    + '<div class="t2">@' + esc(u.username) + (u.is_admin ? ' · 管理员' : '') + '</div></div>'
    + '<span class="arrow">›</span></div></div>'
    + '<div class="card">'
    + '<div class="item" data-act="ann-list"><div class="txt"><div class="t1">公告板</div>'
    + '<div class="t2" id="ann-tip">查看所有公告</div></div><span class="arrow">›</span></div>'
    + '<div class="item" data-act="change-pw"><div class="txt"><div class="t1">修改密码</div></div>'
    + '<span class="arrow">›</span></div>'
    + (u.is_admin ? '<div class="item" data-act="admin"><div class="txt"><div class="t1">管理后台</div>'
        + '<div class="t2">用户 / 公告 / 邮件 / 服务状态</div></div><span class="arrow">›</span></div>' : '')
    + '<div class="item" data-act="logout"><div class="txt"><div class="t1" style="color:#fa5151">退出登录</div></div></div>'
    + '</div>'
    + '<div class="empty" style="padding:8px">心夏 Chat · 轻量版</div>'
  );
  const unread = S.anns.filter((a) => !a.read).length;
  const tip = $('#ann-tip');
  if (tip) tip.textContent = unread ? (unread + ' 条未读公告') : '查看所有公告';
}

/* ---------------- 公告 ---------------- */

async function loadAnns() {
  try {
    const d = await api('/api/announcements');
    S.anns = d.announcements || [];
  } catch (e) { /* 忽略 */ }
}

function popAnnouncement() {
  const unread = S.anns.filter((a) => !a.read);
  if (!unread.length) return;
  const a = unread[0];
  const div = document.createElement('div');
  div.className = 'ann-bubble';
  div.innerHTML = '<b>📢 ' + esc(a.title || '公告') + '</b><p>' + esc(a.body) + '</p>'
    + '<button class="btn" data-act="ann-read" data-id="' + a.id + '">知道了</button>';
  document.body.appendChild(div);
}

function openAnnList() {
  const rows = S.anns.length
    ? S.anns.map((a) => '<div class="item" style="align-items:flex-start;flex-direction:column;gap:4px">'
        + '<div class="t1">' + (a.read ? '' : '<span class="pill warn">未读</span> ') + esc(a.title || '公告') + '</div>'
        + '<div class="t2" style="white-space:pre-wrap;font-size:13px;color:#444">' + esc(a.body) + '</div>'
        + '<div class="t2">' + esc(a.author) + ' · ' + fmtClock(a.created_at) + '</div></div>').join('')
    : '<div class="empty">还没有公告</div>';
  openSheet('公告板', rows, '');
}

/* ---------------- 弹层 ---------------- */

function openSheet(title, bodyHtml, footHtml) {
  const mask = document.createElement('div');
  mask.className = 'mask';
  mask.innerHTML = '<div class="sheet"><div class="sheet-head"><b>' + esc(title) + '</b>'
    + '<button class="icon-btn" data-close="1">✕</button></div>'
    + '<div class="sheet-body">' + bodyHtml + '</div>'
    + (footHtml ? '<div class="sheet-foot">' + footHtml + '</div>' : '') + '</div>';
  document.body.appendChild(mask);
  mask.addEventListener('click', (e) => {
    if (e.target === mask || e.target.getAttribute('data-close')) mask.remove();
  });
  return mask;
}

function chatSetting() {
  if (!S.cur) return;
  const conv = S.cur;
  if (conv.kind === 'direct') {
    const peer = (conv.members || []).find((m) => m.id !== S.me.id) || conv.peer || {};
    const blocked = S.blocks.some((b) => b.id === peer.id);
    const mineRow = (conv.members || []).find((m) => m.id === S.me.id);
    const myAlias = mineRow ? (mineRow.alias || '') : '';
    openSheet('聊天设置',
      '<div class="mini-form">'
      + '<label style="font-size:13px;color:#888">备注名</label>'
      + '<input id="alias-in" placeholder="给 TA 起个备注" value="' + esc(myAlias) + '">'
      + '<button class="btn" data-act="save-alias">保存备注</button>'
      + '</div>'
      + '<div class="card" style="margin:0 14px 14px">'
      + '<div class="item" data-act="' + (blocked ? 'unblock' : 'block') + '" data-id="' + peer.id + '">'
      + '<div class="txt"><div class="t1">' + (blocked ? '解除黑名单' : '加入黑名单') + '</div></div></div>'
      + '<div class="item" data-act="unfriend" data-id="' + peer.id + '">'
      + '<div class="txt"><div class="t1" style="color:#fa5151">删除好友</div>'
      + '<div class="t2">对方不会收到通知</div></div></div>'
      + '<div class="item" data-act="del-conv"><div class="txt"><div class="t1" style="color:#fa5151">'
      + '删除这个聊天</div></div></div>'
      + '</div>', '');
  } else {
    openSheet('群聊设置',
      '<div class="mini-form"><label style="font-size:13px;color:#888">群名</label>'
      + '<input id="gname-in" value="' + esc(conv.title) + '">'
      + '<button class="btn" data-act="save-gname">保存群名</button></div>'
      + '<div class="card" style="margin:0 14px 14px">'
      + (conv.members || []).map((m) => '<div class="item">' + avatar(m, 'sm')
          + '<div class="txt"><div class="t1">' + esc(displayName(m)) + '</div><div class="t2">@'
          + esc(m.username) + '</div></div></div>').join('')
      + '</div>'
      + '<div class="card" style="margin:0 14px 14px">'
      + '<div class="item" data-act="del-conv"><div class="txt"><div class="t1" style="color:#fa5151">'
      + '解散 / 退出群聊</div></div></div></div>', '');
  }
}

/* ---------------- 事件 ---------------- */

document.addEventListener('click', async (e) => {
  const el = e.target.closest('[data-act]');
  if (!el) return;
  const act = el.getAttribute('data-act');
  const id = el.getAttribute('data-id');

  try {
    if (act === 'open-conv') { openConv(Number(id)); }
    else if (act === 'back') { showList(); }
    else if (act === 'send') { sendMsg(); }
    else if (act === 'tab') { setTab(el.getAttribute('data-tab')); }
    else if (act === 'chat-setting') { chatSetting(); }
    else if (act === 'plus') {
      openSheet('新建',
        '<div class="card" style="margin:0">'
        + '<div class="item" data-act="new-group"><div class="txt"><div class="t1">发起群聊</div></div><span class="arrow">›</span></div>'
        + '<div class="item" data-act="go-search"><div class="txt"><div class="t1">加好友</div></div><span class="arrow">›</span></div>'
        + '</div>', '');
    }
    else if (act === 'new-group') { document.querySelectorAll('.mask').forEach((m) => m.remove()); newGroup(); }
    else if (act === 'go-search') {
      document.querySelectorAll('.mask').forEach((m) => m.remove());
      setTab('contacts');
      setTimeout(() => { const u = $('#uq'); if (u) u.focus(); }, 80);
    }
    else if (act === 'open-dm') {
      document.querySelectorAll('.mask').forEach((m) => m.remove());
      const d = await api('/api/conversations', 'POST', { kind: 'direct', peer_id: Number(id) });
      await loadConvs(true);
      openConv(d.conv_id);
    }
    else if (act === 'add-friend') {
      await api('/api/friends', 'POST', { peer_id: Number(id) });
      toast('已添加');
      await loadFriends();
      doSearch();
    }
    else if (act === 'unfriend') {
      await api('/api/friends/' + id, 'DELETE');
      toast('已删除好友');
      await loadFriends();
      document.querySelectorAll('.mask').forEach((m) => m.remove());
      showContacts();
    }
    else if (act === 'block') {
      await api('/api/blocks', 'POST', { peer_id: Number(id) });
      toast('已加入黑名单');
      await loadFriends();
      document.querySelectorAll('.mask').forEach((m) => m.remove());
    }
    else if (act === 'unblock') {
      await api('/api/blocks/' + id, 'DELETE');
      toast('已解除');
      await loadFriends();
      document.querySelectorAll('.mask').forEach((m) => m.remove());
    }
    else if (act === 'save-alias') {
      const v = $('#alias-in').value.trim();
      await api('/api/conversations/' + S.cur.id + '/alias', 'POST', { alias: v });
      toast('备注已保存');
      document.querySelectorAll('.mask').forEach((m) => m.remove());
      await loadConvs(true);
    }
    else if (act === 'save-gname') {
      const v = $('#gname-in').value.trim();
      if (!v) { toast('群名不能为空'); return; }
      await api('/api/conversations/' + S.cur.id + '/rename', 'POST', { title: v });
      toast('群名已更新');
      document.querySelectorAll('.mask').forEach((m) => m.remove());
      await loadConvs(true);
    }
    else if (act === 'del-conv') {
      if (!confirm('确定要删除这个聊天吗？')) return;
      await api('/api/conversations/' + S.cur.id + '/delete', 'POST', {});
      document.querySelectorAll('.mask').forEach((m) => m.remove());
      S.cur = null;
      $('#chat-view').classList.add('hidden');
      await loadConvs(true);
      showList();
    }
    else if (act === 'new-sub') {
      const name = $('#sub-name').value.trim();
      const pass = $('#sub-pass').value;
      if (!name || pass.length < 6) { toast('子账号名必填，密码至少 6 位'); return; }
      await api('/api/subs', 'POST', { username: name, password: pass });
      toast('子账号已创建，可用 wss://' + location.host + '/chat/ws 连接');
      showContacts();
    }
    else if (act === 'del-sub') {
      if (!confirm('删除这个子账号？')) return;
      await api('/api/subs/' + id, 'DELETE');
      toast('已删除');
      showContacts();
    }
    else if (act === 'ann-list') { openAnnList(); }
    else if (act === 'ann-read') {
      await api('/api/announcements/' + id + '/read', 'POST', {});
      const b = el.closest('.ann-bubble');
      if (b) b.remove();
      await loadAnns();
      setTimeout(popAnnouncement, 120);
    }
    else if (act === 'edit-profile') { editProfile(); }
    else if (act === 'change-pw') { changePassword(); }
    else if (act === 'logout') {
      await api('/api/logout', 'POST', {});
      location.href = BASE + '/login';
    }
    else if (act === 'admin') { location.href = BASE + '/admin'; }
  } catch (err) {
    toast(err.message || '操作失败');
  }
});

/* ---------------- 表单类弹层 ---------------- */

function editProfile() {
  openSheet('编辑资料',
    '<div class="mini-form">'
    + '<label style="font-size:13px;color:#888">显示名</label>'
    + '<input id="dn-in" value="' + esc(S.me.display_name) + '">'
    + '<label style="font-size:13px;color:#888">头像链接（可选）</label>'
    + '<input id="av-in" value="' + esc(S.me.avatar) + '" placeholder="https://…">'
    + '<button class="btn" data-act="save-profile">保存</button></div>', '');
}

function changePassword() {
  openSheet('修改密码',
    '<div class="mini-form">'
    + '<input id="old-pw" type="password" placeholder="原密码">'
    + '<input id="new-pw" type="password" placeholder="新密码（≥6 位）">'
    + '<button class="btn" data-act="save-pw">确定修改</button></div>', '');
}

async function newGroup() {
  await loadFriends();
  if (!S.friends.length) { toast('先加几个好友吧'); return; }
  const rows = S.friends.map((f) => '<label class="item" style="cursor:pointer">'
    + '<input type="checkbox" value="' + f.id + '" style="width:18px;height:18px">'
    + avatar(f, 'sm') + '<div class="txt"><div class="t1">' + esc(displayName(f)) + '</div></div></label>').join('');
  openSheet('发起群聊',
    '<div class="mini-form"><input id="g-title" placeholder="群名称"></div><div class="card">' + rows + '</div>',
    '<button class="btn" data-act="create-group">创建</button>');
}

document.addEventListener('click', async (e) => {
  const el = e.target.closest('[data-act]');
  if (!el) return;
  const act = el.getAttribute('data-act');
  try {
    if (act === 'save-profile') {
      const d = await api('/api/profile', 'POST', {
        display_name: $('#dn-in').value.trim(), avatar: $('#av-in').value.trim()
      });
      S.me = Object.assign(S.me, d.user);
      toast('已保存');
      document.querySelectorAll('.mask').forEach((m) => m.remove());
      showMe();
    } else if (act === 'save-pw') {
      await api('/api/password', 'POST', {
        old_password: $('#old-pw').value, new_password: $('#new-pw').value
      });
      toast('密码已修改');
      document.querySelectorAll('.mask').forEach((m) => m.remove());
    } else if (act === 'create-group') {
      const title = $('#g-title').value.trim() || '新群聊';
      const ids = $$('.sheet input[type=checkbox]:checked').map((x) => Number(x.value));
      const d = await api('/api/conversations', 'POST', { kind: 'group', title: title, member_ids: ids });
      document.querySelectorAll('.mask').forEach((m) => m.remove());
      await loadConvs(true);
      openConv(d.conv_id);
    }
  } catch (err) { toast(err.message || '操作失败'); }
});

/* ---------------- 启动 ---------------- */

$('#search').addEventListener('input', renderConvs);

$('#input').addEventListener('input', function () { autoGrow(this); });
$('#input').addEventListener('keydown', function (e) {
  if (e.key === 'Enter' && !e.shiftKey && !e.isComposing && !COARSE) {
    e.preventDefault();
    sendMsg();
  }
});

document.addEventListener('visibilitychange', () => {
  if (document.visibilityState === 'visible' && S.cur) {
    api('/api/conversations/' + S.cur.id + '/read', 'POST', {}).catch(() => {});
  }
});

(async function boot() {
  await loadConvs(true);
  await loadFriends();
  await loadAnns();
  connectSSE();
  setTimeout(popAnnouncement, 700);
  if (window.innerWidth > 760) {
    showList();
    $('#panel-view').classList.remove('hidden');
    $('#panel-view').innerHTML = '<div class="empty" style="padding-top:28vh">从左边选一个会话开始聊天</div>';
  }
})();
"""


def app_page(user, store=None, hub=None, base=None):
    me = {
        "id": user["id"],
        "username": user["username"],
        "display_name": user["display_name"] or user["username"],
        "avatar": user["avatar"] or "",
        "role": user["role"],
        "is_admin": user["role"] == "admin",
        "is_sub": int(user["is_sub"] or 0),
    }
    js = "const ME=" + j(me) + ";\n" + APP_JS + "\n"
    return _doc("心夏 Chat", APP_BODY, extra_js=js, base=base)


# ================================================================ 管理后台

ADMIN_CSS = """
.admin{max-width:960px;margin:0 auto;padding:18px 16px 60px}
.admin header{display:flex;align-items:center;justify-content:space-between;margin-bottom:16px}
.admin header b{font-size:18px}
.admin h3{font-size:15px;margin:22px 0 10px;color:#333}
.grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(140px,1fr));gap:10px}
.stat{background:var(--panel);border-radius:12px;padding:14px}
.stat .n{font-size:22px;font-weight:700;color:var(--brand-d)}
.stat .k{font-size:12px;color:var(--sub);margin-top:2px}
table{width:100%;border-collapse:collapse;background:var(--panel);border-radius:12px;overflow:hidden;font-size:13px}
th,td{padding:9px 10px;text-align:left;border-bottom:1px solid var(--line);white-space:nowrap}
th{background:var(--soft);font-weight:600;color:#555;font-size:12px}
tbody tr:last-child td{border-bottom:0}
.tbl-wrap{overflow-x:auto;border-radius:12px}
.mini{font-size:12px;padding:5px 9px;border-radius:7px;background:var(--soft);border:1px solid var(--line)}
.mini.danger{color:var(--danger);border-color:#ffd7d5;background:#fff5f5}
.mini.ok{color:var(--brand-d);border-color:#c8ebd6;background:#f2fbf5}
.form-card{background:var(--panel);border-radius:12px;padding:14px;display:flex;flex-direction:column;gap:9px}
.form-card input,.form-card textarea{padding:10px 12px;border:1px solid var(--line);border-radius:9px;
  background:var(--soft);outline:none;resize:vertical}
.form-card .btn{padding:11px;font-size:15px}
.mono{font-family:ui-monospace,Menlo,Consolas,monospace;font-size:12px}
"""

ADMIN_JS = r"""
const $ = (s, r) => (r || document).querySelector(s);
const esc = (s) => String(s == null ? '' : s).replace(/[&<>"']/g, (c) => (
  { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]
));
const pad2 = (n) => (n < 10 ? '0' + n : '' + n);
function fmt(ts) {
  const d = new Date(ts * 1000);
  return d.getFullYear() + '-' + pad2(d.getMonth() + 1) + '-' + pad2(d.getDate())
    + ' ' + pad2(d.getHours()) + ':' + pad2(d.getMinutes());
}
let toastTimer = null;
function toast(t) {
  const el = $('#toast');
  el.textContent = t; el.classList.add('show');
  clearTimeout(toastTimer);
  toastTimer = setTimeout(() => el.classList.remove('show'), 2200);
}
async function api(path, method, body) {
  const opt = { method: method || 'GET', headers: {}, cache: 'no-store' };
  if (body !== undefined) { opt.headers['Content-Type'] = 'application/json'; opt.body = JSON.stringify(body); }
  const r = await fetch(BASE + path, opt);
  if (r.status === 401) { location.href = BASE + '/login'; throw new Error('401'); }
  const d = await r.json();
  if (!d.ok) throw new Error(d.error || '失败');
  return d;
}

async function loadStats() {
  const d = await api('/api/admin/stats');
  const s = d.stats;
  const items = [
    ['注册用户', s.users], ['子账号', s.subs], ['会话', s.conversations],
    ['消息', s.messages], ['在线', s.online], ['封禁', s.banned],
    ['登录态', s.sessions], ['24h 邮件', s.mails_24h],
  ];
  $('#stats').innerHTML = items.map((x) =>
    '<div class="stat"><div class="n">' + x[1] + '</div><div class="k">' + x[0] + '</div></div>').join('')
    + '<div class="stat"><div class="n" style="font-size:14px">' + esc(s.smtp) + '</div><div class="k">发信通道</div></div>'
    + '<div class="stat"><div class="n" style="font-size:14px">' + s.history_max + '</div><div class="k">云端消息上限</div></div>';
}

async function loadUsers(q) {
  const d = await api('/api/admin/users' + (q ? '?q=' + encodeURIComponent(q) : ''));
  const rows = d.users.map((u) => {
    const banned = u.status === 'banned';
    const isMainAdmin = u.username === 'akizukikokona';
    return '<tr><td>' + u.id + '</td><td>' + esc(u.username)
      + (u.is_sub ? ' <span class="mini">子</span>' : '') + '</td>'
      + '<td>' + esc(u.display_name) + '</td><td class="mono">' + esc(u.email || '-') + '</td>'
      + '<td>' + (u.role === 'admin' ? '管理员' : '普通') + '</td>'
      + '<td>' + (banned ? '<span class="mini danger">已封禁</span>' : '<span class="mini ok">正常</span>') + '</td>'
      + '<td>' + fmt(u.created_at) + '</td><td>'
      + (isMainAdmin ? '<span class="mini">主管理员</span>'
        : '<button class="mini ' + (banned ? 'ok' : 'danger') + '" data-ban="' + u.id
          + '" data-to="' + (banned ? 'active' : 'banned') + '">' + (banned ? '解封' : '封禁') + '</button>')
      + '</td></tr>';
  }).join('');
  $('#users').innerHTML = '<div class="tbl-wrap"><table><thead><tr><th>ID</th><th>用户名</th><th>显示名</th>'
    + '<th>邮箱</th><th>角色</th><th>状态</th><th>注册时间</th><th>操作</th></tr></thead><tbody>'
    + rows + '</tbody></table></div>';
}

async function loadMails() {
  const d = await api('/api/admin/mails');
  if (!d.mails.length) { $('#mails').innerHTML = '<div class="empty">还没有发过邮件</div>'; return; }
  $('#mails').innerHTML = '<div class="tbl-wrap"><table><thead><tr><th>时间</th><th>收件人</th>'
    + '<th>主题</th><th>状态</th><th>错误</th></tr></thead><tbody>'
    + d.mails.map((m) => '<tr><td>' + fmt(m.created_at) + '</td><td class="mono">' + esc(m.to)
      + '</td><td>' + esc(m.subject) + '</td><td>' + esc(m.status)
      + '</td><td class="mono" style="max-width:280px;overflow:hidden;text-overflow:ellipsis">'
      + esc(m.error || '') + '</td></tr>').join('') + '</tbody></table></div>';
}

async function loadCodes() {
  const d = await api('/api/admin/codes');
  if (!d.codes.length) { $('#codes').innerHTML = '<div class="empty">当前没有未使用的验证码</div>'; return; }
  $('#codes').innerHTML = '<div class="tbl-wrap"><table><thead><tr><th>邮箱</th><th>验证码</th>'
    + '<th>用途</th><th>过期时间</th></tr></thead><tbody>'
    + d.codes.map((c) => '<tr><td class="mono">' + esc(c.email) + '</td><td class="mono"><b>'
      + esc(c.code) + '</b></td><td>' + esc(c.purpose) + '</td><td>' + fmt(c.expires_at)
      + '</td></tr>').join('') + '</tbody></table></div>';
}

document.addEventListener('click', async (e) => {
  const el = e.target.closest('[data-ban]');
  if (!el) return;
  try {
    await api('/api/admin/users/' + el.dataset.ban + '/status', 'POST', { status: el.dataset.to });
    toast('已更新');
    loadUsers($('#user-q').value.trim());
    loadStats();
  } catch (err) { toast(err.message); }
});

$('#user-q').addEventListener('input', function () {
  clearTimeout(this._t);
  this._t = setTimeout(() => loadUsers(this.value.trim()), 300);
});

$('#btn-create').addEventListener('click', async () => {
  try {
    await api('/api/admin/users', 'POST', {
      username: $('#nu-name').value.trim(),
      password: $('#nu-pass').value,
      email: $('#nu-email').value.trim(),
      role: $('#nu-role').value,
    });
    toast('账号已创建');
    $('#nu-name').value = ''; $('#nu-pass').value = ''; $('#nu-email').value = '';
    loadUsers(''); loadStats();
  } catch (err) { toast(err.message); }
});

$('#btn-ann').addEventListener('click', async () => {
  const body = $('#ann-body').value.trim();
  if (!body) { toast('公告内容不能为空'); return; }
  try {
    await api('/api/admin/announcements', 'POST', {
      title: $('#ann-title').value.trim() || '公告', body: body
    });
    toast('公告已发布');
    $('#ann-title').value = ''; $('#ann-body').value = '';
  } catch (err) { toast(err.message); }
});

(async function () {
  try {
    await loadStats(); await loadUsers(''); await loadMails(); await loadCodes();
  } catch (e) { toast(e.message); }
  setInterval(() => { loadStats().catch(() => {}); }, 15000);
})();
"""


def admin_page(user, store=None, hub=None, base=None):
    if base is None:
        base = config.BASE or ""
    body = """
<div class="admin">
  <header>
    <b>管理后台</b>
    <div style="display:flex;gap:8px">
      <a class="mini" href="__BASE__/">返回聊天</a>
      <button class="mini" onclick="loadStats();loadUsers('');loadMails();loadCodes()">刷新</button>
    </div>
  </header>

  <div class="grid" id="stats"></div>

  <h3>用户管理</h3>
  <div class="form-card" style="margin-bottom:10px">
    <input id="user-q" placeholder="搜索用户名 / 邮箱 / 显示名">
  </div>
  <div id="users"></div>

  <h3>新建账号</h3>
  <div class="form-card">
    <input id="nu-name" placeholder="用户名">
    <input id="nu-pass" type="password" placeholder="密码（≥6 位）">
    <input id="nu-email" type="email" placeholder="邮箱（可选）">
    <select id="nu-role" style="padding:10px 12px;border:1px solid #e8e8e8;border-radius:9px;background:#f7f7f7">
      <option value="user">普通用户</option>
      <option value="admin">管理员</option>
    </select>
    <button class="btn" id="btn-create">创建</button>
  </div>

  <h3>发布公告</h3>
  <div class="form-card">
    <input id="ann-title" placeholder="标题">
    <textarea id="ann-body" rows="4" placeholder="公告内容，发布后所有用户会看到未读提示"></textarea>
    <button class="btn" id="btn-ann">发布公告</button>
  </div>

  <h3>发信记录（最近 100 条）</h3>
  <div id="mails"></div>

  <h3>未使用的验证码</h3>
  <div class="empty" style="padding:0 0 10px;text-align:left">没配 SMTP 时，这里可以拿到验证码，先把注册流程跑通。</div>
  <div id="codes"></div>
</div>
<div class="toast" id="toast"></div>
""".replace("__BASE__", base)
    js = "const ME=" + j({
        "id": user["id"], "username": user["username"],
        "display_name": user["display_name"] or user["username"],
        "role": user["role"],
    }) + ";\n" + ADMIN_JS + "\n"
    return _doc("管理后台 · 心夏 Chat", body, extra_css=ADMIN_CSS, extra_js=js, base=base)
