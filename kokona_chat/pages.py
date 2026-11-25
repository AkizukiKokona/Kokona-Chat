"""页面模板：全部内联 CSS/JS，减少请求数（低配设备友好）。"""

import json

from . import config


def j(obj):
    return json.dumps(obj, ensure_ascii=False).replace("</", "<\\/")


BASE_CSS = """
:root{
  --bg:#f7f3ea;--panel:#fff;--line:#eadfcc;--text:#2e2517;--sub:#8b7a61;
  --brand:#9a6c3c;--brand-d:#83582c;--danger:#c1503c;--soft:#fbf7ef;
  --bubble-me:#f4e3c4;--bubble-other:#fff;--radius:10px;
  --cover-grad:linear-gradient(150deg,#cda36c 0%,#b08050 55%,#93653a 100%);
  --ta-max:102px;
}
*{box-sizing:border-box;-webkit-tap-highlight-color:transparent}
html{height:100%;overflow:hidden;overscroll-behavior:none}
/* body 钉死：iOS 弹键盘时整页会被顶起来滚一段，钉住就滚不动了，白色缝隙也从源头没了 */
body{margin:0;padding:0;height:100%;overflow:hidden;position:fixed;inset:0;overscroll-behavior:none}
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
.auth-wrap{height:100%;overflow-y:auto;-webkit-overflow-scrolling:touch;display:flex;padding:24px 16px;
  background:linear-gradient(160deg,#f7efe0 0%,#f7f3ea 40%,#f7f3ea 100%)}
/* margin:auto 居中；内容比屏幕高时自动贴顶，卡片不会被裁掉（表/矮屏也能登录） */
.auth-card{width:100%;max-width:400px;margin:auto;background:var(--panel);border-radius:18px;padding:28px 22px 24px;
  box-shadow:0 8px 40px rgba(0,0,0,.06)}
.auth-logo{width:72px;height:72px;border-radius:20px;object-fit:cover;display:block;
  margin:0 auto 14px;box-shadow:0 6px 20px rgba(154,108,60,.18)}
.remember{display:flex;align-items:center;gap:7px;font-size:13px;color:var(--sub);margin:0 0 12px;cursor:pointer}
.remember input{width:16px;height:16px;accent-color:var(--brand);margin:0}
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
/* 默认高度就是布局视口（安卓键盘会连布局视口一起缩，CSS 天然正确）；
   只有 iOS / adjustPan 那种「键盘盖上来、视口不缩」的情况，JS 才写 --app-h、--vv-top */
.app{position:fixed;left:0;right:0;top:var(--vv-top,0px);display:grid;grid-template-columns:340px 1fr;
  height:var(--app-h,100%);overflow:hidden;min-height:0}
.sidebar{display:flex;flex-direction:column;background:var(--panel);border-right:1px solid var(--line);min-width:0}
.side-top{display:flex;align-items:center;gap:8px;padding:12px 12px 6px}
.me-btn{display:flex;align-items:center;gap:9px;flex:1;min-width:0;padding:3px;border-radius:10px;text-align:left}
.me-btn:active{background:#f2ead9}
.me-av{width:38px;height:38px;border-radius:10px;object-fit:cover;background:#efe4d0;flex:0 0 auto;border:1px solid rgba(0,0,0,.05)}
.me-name{font-weight:600;font-size:16px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}
.side-search{padding:4px 12px 8px}
.side-search input{width:100%;padding:8px 12px;border-radius:8px;border:1px solid var(--line);background:var(--soft);outline:none;font-size:14px}
.conv-list{flex:1;overflow-y:auto;overscroll-behavior:contain}
.conv{display:flex;gap:10px;padding:11px 14px;align-items:center;position:relative}
.conv.press{background:#ececec}
.conv.on{background:#f4e8d4}
.avatar{width:44px;height:44px;border-radius:50%;background:#d9c6a8;color:#fff;display:flex;
  align-items:center;justify-content:center;font-weight:600;font-size:16px;flex:0 0 auto;overflow:hidden}
.avatar img{width:100%;height:100%;object-fit:cover}
.avatar.g{background:#b08050}
.avatar.sm{width:34px;height:34px;font-size:13px;border-radius:50%}
.conv-body{flex:1;min-width:0}
.conv-top{display:flex;justify-content:space-between;align-items:baseline;gap:6px}
.conv-name{font-weight:500;font-size:15px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}
.conv-time{font-size:11px;color:var(--sub);flex:0 0 auto}
.conv-last{font-size:13px;color:var(--sub);overflow:hidden;text-overflow:ellipsis;white-space:nowrap}
.badge{position:absolute;left:46px;top:4px;min-width:18px;height:18px;padding:0 5px;border-radius:9px;
  background:var(--danger);color:#fff;font-size:11px;display:flex;align-items:center;justify-content:center}

.main{display:flex;flex-direction:column;min-width:0;min-height:0;background:var(--bg);position:relative}
/* 聊天区必须是纵向弹性容器：缺这条时 msgs 的 flex:1 失效，输入框会被顶到屏幕中间 */
.chat-view{display:flex;flex-direction:column;flex:1;min-height:0;height:100%;overflow:hidden}
.chat-head{display:flex;align-items:center;gap:8px;padding:10px 12px;background:var(--panel);
  border-bottom:1px solid var(--line);padding-top:calc(10px + env(safe-area-inset-top));flex:0 0 auto}
.chat-title{flex:1;text-align:center;font-weight:600;font-size:16px;overflow:hidden;
  text-overflow:ellipsis;white-space:nowrap}
.icon-btn{width:34px;height:34px;border-radius:8px;display:flex;align-items:center;justify-content:center;
  font-size:20px;color:var(--text);flex:0 0 auto}
.icon-btn:active{background:#eee}
.back{font-size:26px;line-height:1}
.msgs{flex:1;min-height:0;overflow-y:auto;padding:14px 12px 6px;overscroll-behavior:contain;-webkit-overflow-scrolling:touch}
.day-sep{text-align:center;margin:12px 0 10px}
.day-sep span{font-size:11px;color:var(--sub);background:rgba(0,0,0,.04);padding:2px 8px;border-radius:6px}
.row{display:flex;margin-bottom:12px;align-items:flex-start;gap:8px;
  -webkit-user-select:none;user-select:none;-webkit-touch-callout:none;
  touch-action:pan-y;-webkit-tap-highlight-color:transparent}
.row.selectable .bubble{-webkit-user-select:text;user-select:text}
.av-btn{display:block;flex:0 0 auto;border-radius:50%}
.av-btn:active{opacity:.72}
.row.me{flex-direction:row-reverse}
.bubble{max-width:min(74%,560px);padding:9px 12px;border-radius:var(--radius);background:var(--bubble-other);
  word-break:break-word;white-space:pre-wrap;box-shadow:0 1px 1px rgba(0,0,0,.04);position:relative;
  cursor:pointer}
.row.me .bubble{background:var(--bubble-me)}
.col{display:flex;flex-direction:column;align-items:flex-start;gap:4px;min-width:0;max-width:min(74%,560px)}
.col .bubble{max-width:100%}
.b-meta{font-size:11px;color:var(--sub);padding:0 2px;line-height:1.3}
.sys{text-align:center;font-size:12px;color:var(--sub);margin:10px 0}
.composer{display:flex;gap:8px;padding:8px 10px;background:var(--panel);border-top:1px solid var(--line);
  align-items:flex-end;flex:0 0 auto;padding-bottom:calc(8px + env(safe-area-inset-bottom))}
.composer textarea{flex:1 1 0;min-width:0;resize:none;max-height:var(--ta-max,104px);min-height:40px;padding:9px 12px;border-radius:9px;
  border:1px solid var(--line);background:var(--soft);outline:none;line-height:1.4;overflow-y:auto}
.composer textarea:focus{border-color:var(--brand);background:#fff}
.send-btn{flex:0 0 auto;padding:0 14px;height:40px;border-radius:9px;background:var(--brand);color:#fff;font-weight:600}
.send-btn:active{background:var(--brand-d)}
.cmb{display:flex;align-items:center;justify-content:center;width:34px;height:34px;flex:0 0 auto;
  border-radius:50%;color:var(--sub);padding:0;margin-bottom:3px}
.cmb svg{display:block}
.cmb:active,.cmb.on{background:#f4e8d4;color:var(--brand)}
.composer{align-items:center}
.main,.chat-view,.msgs,.tray{min-width:0}
.chat-view{overflow-x:hidden}
.tray{flex:0 0 auto;height:268px;overflow-y:auto;background:var(--panel);
  border-top:1px solid var(--line);padding:12px 12px calc(12px + env(safe-area-inset-bottom))}
.tray-grid{display:grid;grid-template-columns:repeat(5,minmax(0,1fr));gap:8px}
.tray-cell{min-width:0;aspect-ratio:1/1;border-radius:10px;background:var(--soft);display:flex;
  align-items:center;justify-content:center;overflow:hidden;padding:4px}
.tray-cell img{max-width:100%;max-height:100%;object-fit:contain}
.tray-cell.up{color:var(--sub);background:#f7f3ea;border:1px dashed var(--line)}
.tray-big{display:flex;gap:10px;padding:2px}
.tray-big button{display:flex;flex-direction:column;align-items:center;gap:7px;font-size:12px;width:64px;
  color:var(--text);background:transparent}
.tray-big .ic{width:54px;height:54px;border-radius:14px;background:var(--soft);
  display:flex;align-items:center;justify-content:center;color:var(--brand)}
.msg-menu{position:fixed;z-index:88;display:flex;align-items:stretch;padding:3px;
  background:#2f2a25;border-radius:11px;box-shadow:0 8px 26px rgba(0,0,0,.28);
  animation:menu-in .13s ease-out}
@keyframes menu-in{from{opacity:0;transform:translateY(4px) scale(.96)}to{opacity:1;transform:none}}
.msg-menu button{appearance:none;border:0;background:none;color:#f4ede1;font:inherit;font-size:13px;
  line-height:1;padding:10px 13px;border-radius:8px;white-space:nowrap}
.msg-menu button:active{background:rgba(255,255,255,.13)}
.msg-menu .caret{position:absolute;bottom:-5px;left:var(--caret,50%);margin-left:-5px;
  width:10px;height:10px;background:#2f2a25;transform:rotate(45deg);border-radius:2px}
.msg-menu.below .caret{bottom:auto;top:-5px}
.tray-tip{color:var(--sub);font-size:12px;text-align:center;padding:16px 8px;line-height:1.7}
.cmb:active{color:var(--brand)}
.bubble.img{padding:4px;background:transparent;box-shadow:none;max-width:min(72%,240px)}
.quote-bar{flex:0 0 auto;display:flex;align-items:center;gap:8px;padding:7px 12px;
  background:var(--soft);border-top:1px solid var(--line);font-size:12px;color:var(--sub)}
.quote-bar .q-txt{flex:1;min-width:0;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}
.quote-bar b{color:var(--brand);font-weight:600;margin-right:4px}
.quote-bar .q-x{appearance:none;border:0;background:none;color:var(--sub);font-size:14px;padding:0 2px}
.q-box{font-size:12px;line-height:1.5;color:var(--sub);background:rgba(120,96,64,.09);
  border-left:3px solid #c9b79b;border-radius:6px;padding:5px 8px;margin-bottom:6px;
  white-space:pre-wrap;word-break:break-word}
.q-box b{color:var(--brand);font-weight:600;margin-right:4px}
.bubble.q-only{padding:6px 8px;background:var(--bubble-other);box-shadow:none;max-width:100%}
.bubble.q-only .q-box{margin:0;border-left:0;padding:0;background:none}
.at{color:var(--brand);font-weight:600}
.at-pop{position:fixed;z-index:87;padding:4px;background:#fff;border:1px solid var(--line);
  border-radius:10px;box-shadow:0 8px 24px rgba(0,0,0,.16);max-height:210px;overflow:auto;min-width:180px}
.at-pop .item{display:flex;align-items:center;gap:8px;padding:7px 9px;border-radius:8px;font-size:13px}
.at-pop .item:active{background:var(--soft)}
.bubble.hold{position:relative;padding:4px;background:transparent;box-shadow:none;
  max-width:min(72%,240px);overflow:hidden}
.bubble.hold img{display:block;width:100%;height:auto;border-radius:10px;background:var(--soft)}
.up-mask{position:absolute;inset:4px;border-radius:10px;background:rgba(28,24,20,.46);
  display:flex;flex-direction:column;align-items:center;justify-content:center;gap:3px;color:#fff}
.up-mask .pct{font-size:18px;font-weight:600;line-height:1}
.up-mask .lbl{font-size:11px;opacity:.9}
.bubble.img img{display:block;width:100%;height:auto;border-radius:10px;background:var(--soft)}
.recall{color:var(--sub);font-size:12px;text-align:center;margin:8px 0}
.st-grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(72px,1fr));gap:10px;padding:4px 2px}
.st-cell{position:relative;border-radius:10px;background:var(--soft);padding:6px;display:flex;
  align-items:center;justify-content:center;min-height:72px}
.st-cell img{max-width:100%;max-height:64px;display:block;border-radius:6px}
.st-empty{color:var(--sub);font-size:13px;padding:18px 4px;text-align:center;line-height:1.7}
.view-wrap img{width:100%;display:block;border-radius:10px}
.ucard-top{background:var(--cover-grad);padding:26px 20px 22px;border-radius:0}
.chat-title.typing{color:var(--brand);font-weight:600;font-size:14px}
.ucard-top .ucard-close{z-index:4}
.ucard-top > .profile-av{border-radius:50%}
.pill.role{background:#f4e8d4;color:var(--brand-d);margin-left:6px}

/* ---------- 面板（通讯录等） ---------- */
.panel{flex:1;min-height:0;overflow-y:auto;display:flex;flex-direction:column;overscroll-behavior:contain;background:var(--bg)}
.panel-head{display:none;align-items:center;gap:8px;padding:10px 12px;background:var(--panel);
  border-bottom:1px solid var(--line);padding-top:calc(10px + env(safe-area-inset-top))}
.panel-head b{flex:1;text-align:center;font-size:16px;font-weight:600}
.panel-body{padding:16px;flex:1}
.panel h2{font-size:15px;margin:0 0 10px;font-weight:600;color:#333}
.card{background:var(--panel);border-radius:12px;padding:4px 0;margin-bottom:14px;overflow:hidden}
.item{display:flex;align-items:center;gap:10px;padding:13px 14px;border-bottom:1px solid var(--line)}
.item:last-child{border-bottom:0}
.item:active{background:#f5efe3}
.item .txt{flex:1;min-width:0}
.item .t1{font-size:15px}
.item .t2{font-size:12px;color:var(--sub);overflow:hidden;text-overflow:ellipsis;white-space:nowrap}
.item .arrow{color:#c8c8c8;font-size:18px}
.pill{font-size:11px;padding:2px 7px;border-radius:6px;background:#f6ecdb;color:var(--brand-d)}
.pill.warn{background:#fbeee8;color:var(--danger)}
.pill.gray{background:#f2ead9;color:var(--sub)}
.empty{text-align:center;color:var(--sub);font-size:13px;padding:40px 10px}
.mini-form{display:flex;flex-direction:column;gap:8px;padding:14px}
.mini-form textarea,.mini-form input{padding:10px 12px;border:1px solid var(--line);border-radius:9px;background:var(--soft);outline:none;font:inherit;width:100%}.mini-form textarea{resize:vertical;min-height:70px;line-height:1.6}
.mini-form .btn{padding:10px;font-size:15px}
.mini-form label{font-size:13px;color:var(--sub)}

/* ---------- 侧滑抽屉 ---------- */
.drawer-mask{position:fixed;inset:0;background:rgba(0,0,0,.38);z-index:80;opacity:0;transition:opacity .22s ease}
.drawer-mask.show{opacity:1}
.drawer{width:82%;max-width:330px;height:100%;background:var(--panel);display:flex;flex-direction:column;
  transform:translateX(-102%);transition:transform .26s cubic-bezier(.32,.72,.28,1);
  box-shadow:2px 0 26px rgba(0,0,0,.14)}
.drawer-mask.show .drawer{transform:translateX(0)}
.profile-card{position:relative;display:block;width:100%;text-align:left;
  padding:calc(26px + env(safe-area-inset-top)) 20px 22px;
  background:var(--cover-grad);color:#fff;overflow:hidden}
.profile-card:active{filter:brightness(.97)}
.cover-img{position:absolute;inset:0;width:100%;height:100%;object-fit:cover}
.cover-scrim{position:absolute;inset:0;
  background:linear-gradient(180deg,rgba(30,18,6,.10) 0%,rgba(30,18,6,.52) 100%)}
.profile-card > .profile-av,
.profile-card > .profile-name,
.profile-card > .profile-id{position:relative;z-index:2}
.profile-av{width:66px;height:66px;border-radius:50%;object-fit:cover;
  border:2px solid rgba(255,255,255,.85);box-shadow:0 4px 14px rgba(0,0,0,.16);background:#fff}
.profile-name{font-size:19px;font-weight:700;margin-top:12px}
.profile-id{font-size:12px;opacity:.88;margin-top:3px}
.drawer-nav{flex:1;overflow-y:auto;padding:8px 0}
.drawer-nav button{display:flex;align-items:center;width:100%;padding:14px 20px;font-size:15px;text-align:left;gap:12px}
.drawer-nav button:active{background:#f5efe3}
.drawer-nav .di{width:22px;text-align:center;font-size:17px}
.drawer-nav .danger{color:var(--danger)}
.drawer-foot{padding:14px 20px;font-size:12px;color:var(--sub);padding-bottom:calc(14px + env(safe-area-inset-bottom))}

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
.ann-bubble{position:fixed;right:16px;bottom:calc(86px + env(safe-area-inset-bottom));background:var(--panel);
  border-radius:14px;padding:14px 16px;
  box-shadow:0 10px 40px rgba(0,0,0,.16);max-width:330px;z-index:70;border:1px solid var(--line)}
.ann-bubble b{display:block;font-size:14px;margin-bottom:4px}
.ann-bubble p{margin:0 0 10px;font-size:13px;color:#555;white-space:pre-wrap;max-height:40vh;overflow:auto}
.ann-bubble .btn{padding:8px;font-size:14px;border-radius:9px}
.push-bubble{left:16px;right:16px;margin:0 auto;bottom:calc(86px + env(safe-area-inset-bottom))}
.push-acts{display:flex;gap:8px}
.push-acts .btn{flex:1;padding:9px;font-size:14px;border-radius:9px}
.push-acts .later{flex:0 0 auto;padding:9px 14px;font-size:14px;border-radius:9px;
  background:var(--soft);color:var(--sub);border:1px solid var(--line)}

/* ---------- 设置页 ---------- */
.set-hero{position:relative;overflow:hidden;border-radius:14px;margin-bottom:14px;min-height:140px;
  background:var(--cover-grad);color:#fff;padding:18px 16px 16px;display:flex;align-items:flex-end;gap:13px}
.set-hero > .set-av,
.set-hero > .set-hero-txt{position:relative;z-index:2}
.set-av{width:62px;height:62px;border-radius:50%;object-fit:cover;flex:0 0 auto;
  border:2px solid rgba(255,255,255,.9);background:#efe4d0;box-shadow:0 3px 12px rgba(0,0,0,.16)}
.set-hero-txt{flex:1;min-width:0;padding-bottom:2px}
.set-name{font-size:19px;font-weight:700;line-height:1.25;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}
.set-user{font-size:12px;opacity:.9;margin-top:3px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}
.set-tools{position:absolute;right:10px;top:10px;z-index:3;display:flex;gap:6px}
.set-tools button{padding:5px 10px;border-radius:999px;background:rgba(0,0,0,.3);color:#fff;font-size:11px}
.set-tools button:active{background:rgba(0,0,0,.45)}
.set-group{background:var(--panel);border-radius:12px;overflow:hidden;margin-bottom:14px}
.set-group .item{border-bottom:1px solid var(--line)}
.set-group .item:last-child{border-bottom:0}
.set-group-head{padding:12px 16px 8px;font-size:12px;font-weight:600;color:var(--sub)}
.gset-head{display:flex;align-items:center;gap:12px;padding:16px 16px;border-bottom:1px solid var(--line);
  margin-bottom:12px}
.gset-head .avatar.lg{width:56px;height:56px;border-radius:50%;font-size:20px;flex:0 0 auto}
.gset-info{flex:1;min-width:0}
.gset-name{font-size:16px;font-weight:700;color:var(--text);overflow:hidden;text-overflow:ellipsis;white-space:nowrap}
.gset-sub{font-size:12px;color:var(--sub);margin-top:3px}
.set-note{padding:0 4px 10px;font-size:12px;color:var(--sub);line-height:1.6}
.set-note code{background:#f6ecdb;color:var(--brand-d);padding:1px 5px;border-radius:4px;font-size:11px}
.mini-pw{display:flex;gap:8px;padding:10px 14px 12px;align-items:center}
.mini-pw input{flex:1;min-width:0;padding:9px 12px;border:1px solid var(--line);border-radius:9px;
  background:var(--soft);outline:none;font-size:14px}
.mini-pw .btn{width:auto;padding:0 14px;height:38px;font-size:14px}

/* ---------- 资料卡 ---------- */
.ucard{position:relative;border-radius:14px;overflow:hidden;background:var(--panel)}
.ucard-hero{position:relative;height:158px;background:var(--cover-grad);overflow:hidden}
.ucard-av{position:absolute;left:18px;bottom:-32px;width:78px;height:78px;border-radius:50%;
  border:3px solid #fff;object-fit:cover;background:#efe4d0;z-index:2;box-shadow:0 4px 14px rgba(0,0,0,.14)}
.ucard-close{position:absolute;right:10px;top:10px;width:30px;height:30px;border-radius:50%;
  background:rgba(0,0,0,.32);color:#fff;display:flex;align-items:center;justify-content:center;z-index:3;font-size:15px}
.ucard-body{padding:40px 18px 10px}
.ucard-name{font-size:19px;font-weight:700;line-height:1.25;word-break:break-word}
.ucard-user{font-size:12px;color:var(--sub);margin-top:4px}
.ucard-acts{margin-top:14px}
.ucard-acts .item{border-bottom:1px solid var(--line)}
.ucard-acts .item:last-child{border-bottom:0}
#ucard-sheet .sheet-body{padding:0}
#ucard-sheet .sheet-head{display:none}

/* ---------- 头像裁剪 ---------- */
.crop-box{position:relative;width:100%;max-width:300px;aspect-ratio:1/1;margin:16px auto 10px;
  border-radius:14px;overflow:hidden;background:#111;touch-action:none;cursor:grab}
.crop-box:active{cursor:grabbing}
.crop-box.wide{max-width:340px;aspect-ratio:3/2}
.crop-box img{position:absolute;left:50%;top:50%;transform-origin:center;will-change:transform;
  -webkit-user-drag:none;user-select:none;pointer-events:none}
.crop-mask{position:absolute;inset:0;border-radius:14px;pointer-events:none;
  box-shadow:inset 0 0 0 1px rgba(255,255,255,.28)}
.crop-ring{position:absolute;left:50%;top:50%;width:78%;aspect-ratio:1/1;transform:translate(-50%,-50%);
  border:2px dashed rgba(255,255,255,.7);border-radius:50%;pointer-events:none}
.crop-ctrl{display:flex;align-items:center;gap:10px;padding:0 18px 12px;font-size:12px;color:var(--sub)}
.crop-ctrl input[type=range]{flex:1;accent-color:var(--brand)}

/* ---------- 移动端 ---------- */
@media(max-width:760px){
  .app{grid-template-columns:1fr}
  .main{display:none}
  body.chat-open .sidebar{display:none}
  body.chat-open .main{display:flex}
  body.panel-open .sidebar{display:none}
  body.panel-open .main{display:flex}
  .chat-head{padding-left:6px}
  .panel-head{display:flex}
}
@media(max-height:320px){
  .chat-head{padding-top:4px;padding-bottom:4px}
  .chat-title{font-size:14px}
  .composer{padding-top:4px;padding-bottom:4px}
  .composer textarea{min-height:34px;padding:6px 10px}
  .send-btn,.cmb{height:34px}
}
@media(min-width:761px){
  .chat-head .back{display:none}
}
"""


def _doc(title, body, extra_css="", extra_js="", base=None):
    if base is None:
        base = config.BASE or ""
    icon = (base or "") + "/static/icon.png"
    return """<!doctype html>
<html lang="zh-CN"><head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1,maximum-scale=1,viewport-fit=cover,interactive-widget=resizes-content">
<meta name="theme-color" content="#9a6c3c">
<link rel="icon" type="image/png" href="%s">
<link rel="apple-touch-icon" href="%s">
<title>%s</title>
<style>%s%s</style>
</head><body>
%s
<script>window.BASE=%s;</script>
<script>%s</script>
</body></html>""" % (icon, icon, title, BASE_CSS, extra_css, body, j(base), extra_js)


# ================================================================ 登录

LOGIN_JS = """
const msg = document.getElementById('msg');
const KEY = 'kc_login_v1';
function say(t, ok){ msg.textContent = t || ''; msg.className = 'msg-line' + (ok ? ' ok' : ''); }

function encodeSaved(o){
  try { return btoa(unescape(encodeURIComponent(JSON.stringify(o)))); } catch (e) { return ''; }
}
function decodeSaved(raw){
  try { return JSON.parse(decodeURIComponent(escape(atob(raw)))); } catch (e) { return null; }
}
function loadSaved(){
  try {
    const raw = localStorage.getItem(KEY);
    return raw ? decodeSaved(raw) : null;
  } catch (e) { return null; }
}
function saveSaved(u, p){
  try { localStorage.setItem(KEY, encodeSaved({ u: u, p: p })); } catch (e) {}
}
function clearSaved(){
  try { localStorage.removeItem(KEY); } catch (e) {}
}

const saved = loadSaved();
if (saved) {
  document.getElementById('username').value = saved.u || '';
  document.getElementById('password').value = saved.p || '';
}

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
    if (document.getElementById('remember').checked) saveSaved(u, p);
    else clearSaved();
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
  <img class="auth-logo" src="__BASE__/static/icon.png" alt="心夏通讯">
  <h1 class="auth-title">心夏通讯</h1>
  <p class="auth-sub">登录后继续聊天</p>
  <form id="form" autocomplete="on">
    <div class="field"><label for="username">账号</label>
      <input id="username" name="username" autocomplete="username" placeholder="用户名或邮箱"></div>
    <div class="field"><label for="password">密码</label>
      <input id="password" name="password" type="password" autocomplete="current-password" placeholder="密码"></div>
    <label class="remember"><input type="checkbox" id="remember" checked>记住账号密码</label>
    <div class="msg-line" id="msg"></div>
    <button class="btn" id="submit" type="submit">登录</button>
  </form>
  <div class="auth-foot">
    <a href="__BASE__/register">注册新账号</a>
    <a href="__BASE__/recover">忘记账号 / 密码</a>
  </div>
</div></div>
""".replace("__BASE__", config.BASE or "" if base is None else base)
    return _doc("登录 · 心夏通讯", body, extra_js=LOGIN_JS, base=base)


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
  <img class="auth-logo" src="__BASE__/static/icon.png" alt="心夏通讯">
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
    return _doc("注册 · 心夏通讯", body, extra_js=REGISTER_JS, base=base)


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
  <img class="auth-logo" src="__BASE__/static/icon.png" alt="心夏通讯">
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
    return _doc("找回账号 · 心夏通讯", body, extra_css=".code-btn.on{background:#f4e8d4;border-color:#9ad9b4;color:#83582c}", extra_js=RECOVER_JS, base=base)


# ================================================================ 主界面

APP_BODY = """<div class="app" id="app">
  <aside class="sidebar">
    <div class="side-top">
      <button class="me-btn" data-act="drawer-open">
        <img class="me-av" id="me-av" src="__BASE__/static/icon.png" alt="">
        <span class="me-name" id="me-name">聊天</span>
      </button>
      <button class="icon-btn" data-act="plus" title="新建">＋</button>
    </div>
    <div class="side-search"><input id="search" placeholder="搜索会话" autocomplete="off"></div>
    <div class="conv-list" id="conv-list"></div>
  </aside>
  <main class="main">
    <section class="chat-view hidden" id="chat-view">
      <header class="chat-head">
        <button class="icon-btn back" data-act="back">‹</button>
        <div class="chat-title" id="chat-title"></div>
        <button class="icon-btn" data-act="chat-setting">⋯</button>
      </header>
      <div class="msgs" id="msgs"></div>
      <div class="quote-bar hidden" id="quote-bar"></div>
      <div class="composer">
        <button class="cmb" data-act="open-plus" title="更多" aria-label="更多">
          <svg viewBox="0 0 24 24" width="22" height="22" fill="none" stroke="currentColor"
               stroke-width="1.6" stroke-linecap="round"><circle cx="12" cy="12" r="9"/>
            <path d="M12 8.2v7.6M8.2 12h7.6"/></svg>
        </button>
        <textarea id="input" rows="1" placeholder="发消息…" autocomplete="off"></textarea>
        <button class="cmb" data-act="open-stickers" title="表情" aria-label="表情">
          <svg viewBox="0 0 24 24" width="22" height="22" fill="none" stroke="currentColor"
               stroke-width="1.6" stroke-linecap="round"><circle cx="12" cy="12" r="9"/>
            <path d="M9 9.6h.01M15 9.6h.01"/>
            <path d="M8.4 14.2c.9 1.2 2.1 1.8 3.6 1.8s2.7-.6 3.6-1.8"/></svg>
        </button>
        <button class="send-btn" data-act="send">发送</button>
      </div>
      <div class="tray hidden" id="tray"></div>
    </section>
    <section class="panel hidden" id="panel-view"></section>
  </main>
</div>

<div class="drawer-mask hidden" id="drawer">
  <aside class="drawer">
    <div class="profile-card" data-act="drawer-profile">
      <img class="cover-img hidden" id="drawer-cover" alt="">
      <div class="cover-scrim"></div>
      <img class="profile-av" id="drawer-av" src="__BASE__/static/icon.png" alt="">
      <div class="profile-name" id="drawer-name"></div>
      <div class="profile-id" id="drawer-id"></div>
    </div>
    <nav class="drawer-nav" id="drawer-nav"></nav>
    <div class="drawer-foot">心夏通讯</div>
  </aside>
</div>
<input type="file" id="img-file" accept="image/*" hidden>
<input type="file" id="st-file" accept="image/*" hidden>
<div class="toast" id="toast"></div>
"""

APP_JS = r"""const $ = (s, r) => (r || document).querySelector(s);
const $$ = (s, r) => Array.prototype.slice.call((r || document).querySelectorAll(s));
const esc = (s) => String(s == null ? '' : s).replace(/[&<>"']/g, (c) => (
  { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]
));
const pad2 = (n) => (n < 10 ? '0' + n : '' + n);
const COARSE = window.matchMedia && window.matchMedia('(pointer:coarse)').matches;
const ICON = BASE + '/static/icon.png';

const S = {
  me: ME, convs: [], cur: null, msgs: [], openId: null,
  friends: [], blocks: [], subs: [], subCanCreate: false, anns: [], view: 'chats'
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

/* ---------------- 浏览器推送 ---------------- */

const PUSH = { key: '', supported: false, perm: 'default', sub: null };

function urlB64ToU8(base64) {
  const s = (base64 + '='.repeat((4 - base64.length % 4) % 4)).replace(/-/g, '+').replace(/_/g, '/');
  const raw = atob(s);
  const out = new Uint8Array(raw.length);
  for (let i = 0; i < raw.length; i++) out[i] = raw.charCodeAt(i);
  return out;
}

async function initPush() {
  PUSH.supported = ('serviceWorker' in navigator) && ('PushManager' in window) && ('Notification' in window);
  PUSH.perm = ('Notification' in window) ? Notification.permission : 'unsupported';
  if (!PUSH.supported) return;
  try {
    await navigator.serviceWorker.register(BASE + '/sw.js');
    const d = await api('/api/push/key');
    PUSH.key = d.key || '';
    if (!PUSH.key) { PUSH.supported = false; return; }
    const reg = await navigator.serviceWorker.ready;
    PUSH.sub = await reg.pushManager.getSubscription();
    if (PUSH.sub) {
      // 换账号登录时，把同一个订阅重新挂到当前账号上
      api('/api/push/subscribe', 'POST', { subscription: PUSH.sub.toJSON() }).catch(() => {});
    }
  } catch (e) { PUSH.supported = false; }
}

async function refreshPushState() {
  if (!('Notification' in window)) { PUSH.perm = 'unsupported'; return; }
  PUSH.perm = Notification.permission;
  if (!('serviceWorker' in navigator)) return;
  try {
    const reg = await navigator.serviceWorker.getRegistration();
    PUSH.sub = reg ? await reg.pushManager.getSubscription() : null;
  } catch (e) { PUSH.sub = null; }
}

async function pushEnable() {
  if (!PUSH.supported) { toast('这个浏览器不支持推送'); return; }
  if (PUSH.perm === 'denied') { toast('浏览器已记住拒绝，去地址栏左侧的站点设置里改'); return; }
  const perm = await Notification.requestPermission();
  PUSH.perm = perm;
  if (perm !== 'granted') { toast('没有拿到通知权限'); return; }
  try {
    const reg = await navigator.serviceWorker.ready;
    let sub = await reg.pushManager.getSubscription();
    if (!sub) {
      sub = await reg.pushManager.subscribe({
        userVisibleOnly: true, applicationServerKey: urlB64ToU8(PUSH.key),
      });
    }
    PUSH.sub = sub;
    await api('/api/push/subscribe', 'POST', { subscription: sub.toJSON() });
    toast('通知已开启');
  } catch (e) { toast('开启失败：' + (e.message || '未知错误')); }
  if (S.view === 'settings') openSettings();
}

async function pushDisable() {
  try {
    const reg = await navigator.serviceWorker.getRegistration();
    const sub = reg ? await reg.pushManager.getSubscription() : null;
    if (sub) {
      await api('/api/push/unsubscribe', 'POST', { endpoint: sub.endpoint }).catch(() => {});
      await sub.unsubscribe().catch(() => {});
    }
    PUSH.sub = null;
    toast('通知已关闭');
  } catch (e) { toast('关闭失败了'); }
  if (S.view === 'settings') openSettings();
}

async function pushTest() {
  try { await api('/api/push/test', 'POST', {}); toast('已发一条测试通知'); }
  catch (e) { toast(e.message); }
}

const IS_IOS = /iPad|iPhone|iPod/.test(navigator.userAgent)
  || (navigator.platform === 'MacIntel' && navigator.maxTouchPoints > 1);
const IS_STANDALONE = ((window.matchMedia && window.matchMedia('(display-mode: standalone)').matches)
  || navigator.standalone === true);

function pushNeverAsk() {
  try { localStorage.setItem('kc_push_never', '1'); } catch (e) {}
}

function pushBubble(title, text, acts) {
  document.querySelectorAll('.push-bubble').forEach((n) => n.remove());
  const div = document.createElement('div');
  div.className = 'ann-bubble push-bubble';
  div.innerHTML = '<b>' + esc(title) + '</b><p>' + esc(text) + '</p>'
    + '<div class="push-acts">' + acts + '</div>';
  document.body.appendChild(div);
}

function showIosPushTip() {
  pushBubble('iPhone 要先添加到主屏幕',
    'Safari 里开着页面收不到推送。点底部分享按钮，选「添加到主屏幕」，再从主屏幕图标打开，就能开启通知了。',
    '<button class="later" data-act="push-ask-later">不再显示</button>'
    + '<button class="btn" data-act="push-ask-later">知道了</button>');
}

function showPushAsk() {
  pushBubble('开启消息通知？',
    '开启后，关掉页面也能收到新消息提醒。只用来推你收到的消息，不发别的。',
    '<button class="later" data-act="push-ask-later">不再显示</button>'
    + '<button class="btn" data-act="push-ask-ok">请求权限</button>');
}

function maybeAskPush() {
  // 问过一次就不再问：点「不再显示」或「知道了」都记下来，后面只能去设置里主动开
  try { if (localStorage.getItem('kc_push_never') === '1') return; } catch (e) {}
  if (IS_IOS && !IS_STANDALONE) { showIosPushTip(); return; }
  if (!PUSH.supported) return;
  if (PUSH.perm === 'granted' || PUSH.perm === 'denied') return;
  showPushAsk();
}

function pushRow() {
  if (!PUSH.supported) {
    return '<div class="item"><div class="txt"><div class="t1">浏览器通知</div>'
      + '<div class="t2">这个浏览器不支持；iPhone 要先「添加到主屏幕」</div></div></div>';
  }
  let hint = '开启后关掉页面也能收到新消息';
  let onAct = 'push-on';
  if (IS_IOS && !IS_STANDALONE) {
    hint = '要先「添加到主屏幕」，再从这里开启';
    onAct = 'push-ios-tip';
  } else if (PUSH.perm === 'denied') {
    hint = '浏览器记住了拒绝，点这里再请求一次权限';
  } else if (PUSH.sub) {
    hint = '已开启，关掉页面也能收到';
  }
  if (PUSH.sub) {
    return '<div class="item" data-act="push-off"><div class="txt"><div class="t1">浏览器通知</div>'
      + '<div class="t2">' + hint + '</div></div><span class="arrow">关闭</span></div>'
      + '<div class="item" data-act="push-test"><div class="txt"><div class="t1">发一条测试通知</div>'
      + '</div><span class="arrow">›</span></div>';
  }
  return '<div class="item" data-act="' + onAct + '"><div class="txt"><div class="t1">浏览器通知</div>'
    + '<div class="t2">' + hint + '</div></div><span class="arrow">›</span></div>';
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

function hhmm(ts) {
  const d = new Date(ts * 1000);
  return pad2(d.getHours()) + ':' + pad2(d.getMinutes());
}

/** 居中那条小条：日期 + 时刻，例如「今天 14:32」。 */
function fmtSep(ts) {
  return fmtDay(ts) + ' ' + hhmm(ts);
}

/** 点消息弹 toast 时用的完整时间。 */
function fmtFull(ts) {
  const d = new Date(ts * 1000);
  const y = d.getFullYear();
  const md = (d.getMonth() + 1) + '月' + d.getDate() + '日';
  const day = (y === new Date().getFullYear()) ? md : y + '年' + md;
  return day + ' ' + hhmm(ts);
}

/** 消息间隔超过 5 分钟（或跨天）才重新插一条时间小条。 */
const SEP_GAP = 5 * 60;

function needSep(prev, cur) {
  if (!prev) return true;
  const a = new Date(prev.created_at * 1000), b = new Date(cur.created_at * 1000);
  if (a.toDateString() !== b.toDateString()) return true;
  return (cur.created_at - prev.created_at) >= SEP_GAP;
}

/** 头像地址：av:xxx 走服务端头像接口；兼容老的 http(s) 链接；没设返回空串。 */
function avatarSrc(u) {
  const a = String((u && u.avatar) || '');
  if (a.indexOf('av:') === 0) return BASE + '/avatar/' + encodeURIComponent(a.slice(3));
  if (/^https?:\/\//.test(a)) return a;
  return '';
}

/** 资料卡封面：cv:文件名 → /cover/xxx；没有就返回空串（走默认渐变）。 */
function coverSrc(u) {
  const c = String((u && u.cover) || '');
  if (c.indexOf('cv:') === 0) return BASE + '/cover/' + encodeURIComponent(c.slice(3));
  if (/^https?:\/\//.test(c)) return c;
  return '';
}

function coverImg(u, cls, id) {
  const src = coverSrc(u);
  const attrs = ' class="cover-img ' + (cls || '') + (src ? '' : ' hidden') + '"'
    + (id ? ' id="' + id + '"' : '')
    + (src ? ' src="' + esc(src) + '"' : '');
  return '<img' + attrs + ' alt="">';
}

/** 自己没设头像时用站点头像，别人没设就用名字首字。 */
function avatar(u, cls) {
  cls = cls || '';
  const src = avatarSrc(u);
  if (src) return '<div class="avatar ' + cls + '"><img src="' + esc(src) + '" alt=""></div>';
  const self = u && S.me && Number(u.id) === Number(S.me.id);
  if (self) return '<div class="avatar ' + cls + '"><img src="' + esc(ICON) + '" alt=""></div>';
  const name = (u && (u.display_name || u.username)) || '?';
  return '<div class="avatar ' + cls + '">' + esc(String(name).slice(0, 1)) + '</div>';
}

/** 会话头像：群有 gv: 就贴图，否则用首字；pkn 用站点图标。 */
function convAvatar(c, cls) {
  const box = 'avatar g ' + (cls || '');
  if (!c) return '<div class="' + box + '">群</div>';
  if (c.kind === 'pkn') return '<div class="avatar ' + (cls || '') + '"><img src="' + esc(ICON) + '" alt=""></div>';
  const a = String(c.avatar || '');
  if (a.indexOf('gv:') === 0) {
    return '<div class="' + box + '"><img src="' + esc(BASE + '/gavatar/' + encodeURIComponent(a.slice(3))) + '" alt=""></div>';
  }
  return '<div class="' + box + '">' + esc(String(c.title || '群').slice(0, 1)) + '</div>';
}

function displayName(u) {
  return u ? (u.display_name || u.username) : '未知';
}

/* ---------------- 侧滑抽屉 ---------------- */

function renderDrawer() {
  const me = S.me;
  $('#drawer-av').src = avatarSrc(me) || ICON;
  $('#drawer-name').textContent = displayName(me);
  $('#drawer-id').textContent = '@' + me.username + (me.is_admin ? ' · 管理员' : '');
  const cv = coverSrc(me), el = $('#drawer-cover');
  if (el) {
    if (cv) { el.src = cv; el.classList.remove('hidden'); }
    else { el.removeAttribute('src'); el.classList.add('hidden'); }
  }

  const items = [
    ['open-settings', '⚙️', '设置'],
    ['drawer-contacts', '👥', '通讯录'],
    ['drawer-addfriend', '➕', '添加好友'],
    ['drawer-ann', '📢', '公告板'],
    ['drawer-reload', '🔄', '刷新会话列表'],
  ];
  if (me.is_admin) items.push(['drawer-admin', '🛠️', '管理后台']);

  let html = items.map((x) =>
    '<button data-act="' + x[0] + '"><span class="di">' + x[1] + '</span>' + x[2] + '</button>').join('');
  html += '<button data-act="logout" class="danger"><span class="di">🚪</span>退出登录</button>';
  $('#drawer-nav').innerHTML = html;
}

let drawerTimer = null;
function openDrawer() {
  const d = $('#drawer');
  clearTimeout(drawerTimer);
  d.classList.remove('hidden');
  requestAnimationFrame(() => d.classList.add('show'));
}

function closeDrawer() {
  const d = $('#drawer');
  d.classList.remove('show');
  clearTimeout(drawerTimer);
  drawerTimer = setTimeout(() => {
    if (!d.classList.contains('show')) d.classList.add('hidden');
  }, 280);
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
    const av = c.kind === 'direct' ? avatar(c.peer) : convAvatar(c);
    const badge = c.unread > 0 ? '<span class="badge">' + (c.unread > 99 ? '99+' : c.unread) + '</span>' : '';
    return '<div class="conv' + (S.openId === c.id ? ' on' : '') + '" data-act="open-conv" data-id="' + c.id + '">'
      + av + '<div class="conv-body"><div class="conv-top"><span class="conv-name">' + esc(c.title)
      + '</span><span class="conv-time">' + (c.last ? fmtClock(c.last.created_at) : '')
      + '</span></div><div class="conv-last">' + esc(last) + '</div></div>' + badge + '</div>';
  }).join('');
}

/* ---------------- 聊天 ---------------- */

function showList() {
  document.body.classList.remove('chat-open', 'panel-open');
  S.view = 'chats';
  S.openId = null;
  hideTyping();
  const p = $('#panel-view');
  p.classList.add('hidden');
  $('#chat-view').classList.add('hidden');
  renderConvs();
}

function convTitle(conv, members) {
  if (conv.kind === 'direct') {
    const peer = conv.peer;
    return peer ? displayName(peer) : '私聊';
  }
  if (conv.kind === 'group') {
    return conv.title + '（' + ((members || []).length) + '）';
  }
  return conv.title || '旧频道';
}

function msgCacheKey(id) { return 'kc_msgs_' + id; }

function readMsgCache(id) {
  try {
    const raw = localStorage.getItem(msgCacheKey(id));
    return raw ? JSON.parse(raw) : null;
  } catch (e) { return null; }
}

function writeMsgCache(id, msgs) {
  try { localStorage.setItem(msgCacheKey(id), JSON.stringify(msgs.slice(-60))); } catch (e) {}
}

async function openConv(id) {
  try {
    hideTyping();
    clearQuote();
    closeAtPop();
    closeTray();
    S.openId = id;
    const cached = readMsgCache(id);
    if (cached && cached.length) {
      if (!S.cur || Number(S.cur.id) !== Number(id)) S.cur = { id: id, kind: 'direct', members: [] };
      S.msgs = cached;
      $('#chat-title').textContent = (S.convs.find((c) => c.id === id) || {}).title || '';
      renderMsgs();
      $('#chat-view').classList.remove('hidden');
      $('#panel-view').classList.add('hidden');
      document.body.classList.add('chat-open');
      document.body.classList.remove('panel-open');
      scrollBottom(true);
    }
    const d = await api('/api/conversations/' + id);
    S.cur = d.conversation;
    S.cur.members = d.members || [];
    S.cur.title = convTitle(d.conversation, d.members);
    S.msgs = d.messages || [];
    writeMsgCache(id, S.msgs);
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

function nameOf(uid) {
  const id = Number(uid);
  if (S.me && Number(S.me.id) === id) return displayName(S.me);
  const mem = (S.cur && S.cur.members || []).find((x) => Number(x.id) === id);
  if (mem) return displayName(mem);
  return '有人';
}

/** 撤回后的一行系统提示。 */
function recallHtml(m) {
  const who = nameOf(m.sender_id);
  const by = nameOf(m.recall_by || m.sender_id);
  if (m.recall_by && Number(m.recall_by) !== Number(m.sender_id)) {
    return '<div class="recall">管理员 ' + esc(by) + ' 撤回了 ' + esc(who) + ' 的消息</div>';
  }
  return '<div class="recall">' + esc(who) + ' 撤回了一条消息</div>';
}

function mediaHtml(m) {
  const md = m.media || {};
  if (!md.url) return '';
  const w = md.w || 0, h = md.h || 0;
  let boxW = 220, boxH = 220;
  if (w && h) {
    const ratio = w / h;
    boxW = Math.min(220, w);
    boxH = Math.round(boxW / ratio);
    if (boxH > 260) { boxH = 260; boxW = Math.round(boxH * ratio); }
  }
  return '<div class="bubble img"><img src="' + esc(md.url) + '" width="' + boxW + '" height="'
    + boxH + '" loading="lazy" alt="" data-act="view-image" data-src="' + esc(md.url) + '"></div>';
}

let QUOTE = null;

function quoteText(q) {
  if (!q) return '';
  if (q.recalled) return '消息已撤回';
  if (q.kind === 'image') return '[图片]';
  return q.body || '';
}

function quoteBoxHtml(q) {
  if (!q) return '';
  const who = q.sender ? displayName(q.sender) : '消息';
  return '<div class="q-box"><b>' + esc(who) + '</b>' + esc(quoteText(q).slice(0, 80)) + '</div>';
}

function setQuote(m) {
  closeMsgMenu();
  if (!m) return;
  QUOTE = { id: m.id, sender_id: m.sender_id, kind: m.kind, body: m.body, recalled: m.recalled };
  const bar = $('#quote-bar');
  if (!bar) return;
  bar.classList.remove('hidden');
  bar.innerHTML = '<div class="q-txt"><b>' + esc(nameOf(m.sender_id)) + '</b>'
    + esc(quoteText(m).slice(0, 60)) + '</div>'
    + '<button class="q-x" data-act="quote-cancel">✕</button>';
  const el = $('#input');
  if (el) el.focus();
}

function clearQuote() {
  QUOTE = null;
  const bar = $('#quote-bar');
  if (bar) { bar.classList.add('hidden'); bar.innerHTML = ''; }
}

/** 正文里把 @到的名字 标出来。 */
function bodyHtml(m) {
  let html = esc(m.body);
  (m.mentions || []).forEach((uid) => {
    const mem = ((S.cur && S.cur.members) || []).find((x) => Number(x.id) === Number(uid));
    if (!mem) return;
    const tag = esc('@' + displayName(mem));
    html = html.split(tag).join('<span class="at">' + tag + '</span>');
  });
  return html;
}

function msgHtml(m) {
  if (Number(m.recalled) === 1) return recallHtml(m);
  const mine = S.me && m.sender_id === S.me.id;
  const kind = (S.cur && S.cur.kind) || 'direct';
  // 私聊（含 WSS 那条）不显示名字；群聊/频道里别人的消息，名字放在气泡上方
  const showName = !mine && kind !== 'direct' && kind !== 'pkn';
  const bubble = (m.kind === 'image')
    ? mediaHtml(m)
    : '<div class="bubble">' + quoteBoxHtml(m.quote) + bodyHtml(m) + '</div>';
  const stack = (m.kind === 'image' && m.quote)
    ? '<div class="col"><div class="bubble q-only">' + quoteBoxHtml(m.quote) + '</div>' + bubble + '</div>'
    : bubble;
  const inner = showName
    ? '<div class="col"><div class="b-meta">' + esc(displayName(m.sender)) + '</div>' + stack + '</div>'
    : stack;
  const av = '<span class="av-btn" data-act="msg-user" data-id="' + (m.sender_id || 0) + '">'
    + avatar(m.sender, 'sm') + '</span>';
  return '<div class="row' + (mine ? ' me' : '') + '" data-mid="' + m.id + '" data-ts="' + m.created_at + '">'
    + av + inner + '</div>';
}

function renderMsgs() {
  const box = $('#msgs');
  if (!S.msgs.length) {
    box.innerHTML = '<div class="empty">还没有消息，打个招呼吧</div>';
    return;
  }
  let html = '', prev = null;
  for (let i = 0; i < S.msgs.length; i++) {
    const m = S.msgs[i];
    if (needSep(prev, m)) {
      html += '<div class="day-sep"><span>' + fmtSep(m.created_at) + '</span></div>';
    }
    html += Number(m.recalled) === 1 ? recallHtml(m) : msgHtml(m);
    prev = m;
  }
  box.innerHTML = html;
  $$('.row[data-mid]', box).forEach((row) => {
    bindLongPress(row, () => openMsgMenu(row.getAttribute('data-mid')));
  });
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
  if (needSep(prev, m)) {
    box.insertAdjacentHTML('beforeend', '<div class="day-sep"><span>' + fmtSep(m.created_at) + '</span></div>');
  }
  writeMsgCache(S.cur ? S.cur.id : 0, S.msgs);
  box.insertAdjacentHTML('beforeend', Number(m.recalled) === 1 ? recallHtml(m) : msgHtml(m));
  const lastRow = box.querySelector('.row[data-ts]:last-of-type');
  if (lastRow && !Number(m.recalled)) {
    bindLongPress(lastRow, () => openMsgMenu(lastRow.getAttribute('data-mid')));
  }
  if (stick) scrollBottom(true);
}

/* ---------------- 图片 ---------------- */

const IMG_MAX_EDGE = 1600;
const IMG_MAX_BYTES = 760 * 1024;

function loadImage(src) {
  return new Promise((resolve, reject) => {
    const img = new Image();
    img.onload = () => resolve(img);
    img.onerror = () => reject(new Error('\u56fe\u7247\u8bfb\u53d6\u5931\u8d25'));
    img.src = src;
  });
}

async function fileToWebp(file) {
  const url = URL.createObjectURL(file);
  let img;
  try { img = await loadImage(url); } finally { setTimeout(() => URL.revokeObjectURL(url), 1000); }
  let { width: w, height: h } = img;
  const scale = Math.min(1, IMG_MAX_EDGE / Math.max(w, h));
  w = Math.max(1, Math.round(w * scale));
  h = Math.max(1, Math.round(h * scale));
  const cv = document.createElement('canvas');
  cv.width = w; cv.height = h;
  const ctx = cv.getContext('2d');
  ctx.imageSmoothingQuality = 'high';
  ctx.drawImage(img, 0, 0, w, h);
  let data = cv.toDataURL('image/webp', 0.86);
  if (data.indexOf('data:image/webp') !== 0) data = cv.toDataURL('image/png');
  let q = 0.86;
  while (data.length * 0.75 > IMG_MAX_BYTES && q > 0.4) {
    q -= 0.08;
    data = cv.toDataURL('image/webp', q);
  }
  return data;
}

function uploadMedia(data, onProgress) {
  return new Promise((resolve, reject) => {
    const xhr = new XMLHttpRequest();
    xhr.open('POST', BASE + '/api/media');
    xhr.setRequestHeader('Content-Type', 'application/json');
    xhr.upload.onprogress = (e) => {
      if (e.lengthComputable && onProgress) onProgress(e.loaded / e.total);
    };
    xhr.onload = () => {
      let d = null;
      try { d = JSON.parse(xhr.responseText); } catch (e) { /* 非 JSON 按失败处理 */ }
      if (xhr.status === 200 && d && d.ok) resolve(d);
      else reject(new Error((d && d.error) || '上传失败'));
    };
    xhr.onerror = () => reject(new Error('网络错误'));
    xhr.send(JSON.stringify({ data: data }));
  });
}

let tempSeq = 0;

async function sendImageFile(file) {
  if (!S.cur) return;
  const cid = S.cur.id;
  const url = URL.createObjectURL(file);
  const tid = 'tmp-' + (++tempSeq);
  const box = $('#msgs');
  if (!S.msgs.length) box.innerHTML = '';
  box.insertAdjacentHTML('beforeend',
    '<div class="row me" id="' + tid + '">'
    + '<div class="bubble hold"><img src="' + url + '" alt="">'
    + '<div class="up-mask"><span class="pct">0%</span><span class="lbl">压缩中</span></div>'
    + '</div></div>');
  const row = $('#' + tid);
  const pctEl = row.querySelector('.pct');
  const lblEl = row.querySelector('.lbl');
  const setP = (p, label) => {
    pctEl.textContent = Math.round(p) + '%';
    if (label) lblEl.textContent = label;
  };
  scrollBottom(true);

  // 压缩这一步拿不到真实进度，先缓慢爬到四成，压完再交给上传
  let fake = 0;
  const timer = setInterval(() => {
    fake = Math.min(42, fake + 5);
    setP(fake);
  }, 100);

  try {
    const data = await fileToWebp(file);
    clearInterval(timer);
    setP(44, '发送中');
    const up = await uploadMedia(data, (r) => setP(44 + r * 50));
    setP(96, '发送中');
    const d = await api('/api/conversations/' + cid + '/messages', 'POST',
      { media_id: up.media.id, body: '', quote_id: QUOTE ? QUOTE.id : 0 });
    clearQuote();
    setP(100);
    row.remove();
    // 上传期间切走了会话就别往当前列表里塞
    if (d.message && S.cur && Number(S.cur.id) === Number(cid)) appendMsg(d.message);
  } catch (e) {
    clearInterval(timer);
    row.remove();
    toast('图片发送失败：' + (e.message || '未知错误'));
  } finally {
    setTimeout(() => URL.revokeObjectURL(url), 4000);
  }
}

const onImagePicked = (e) => {
  const file = e.target.files && e.target.files[0];
  e.target.value = '';
  closeTray();
  if (file) sendImageFile(file);
};

/* ---------------- 表情包 ---------------- */

let STICKERS = [];

let trayMode = '';

function closeTray() {
  trayMode = '';
  const t = $('#tray');
  if (t) { t.classList.add('hidden'); t.innerHTML = ''; }
  $$('.cmb').forEach((b) => b.classList.remove('on'));
}

function trayToggle(mode) {
  if (trayMode === mode) { closeTray(); return; }
  trayMode = mode;
  const t = $('#tray');
  if (!t) return;
  t.classList.remove('hidden');
  $$('.cmb').forEach((b) => b.classList.toggle('on', b.getAttribute('data-act') ===
    (mode === 'plus' ? 'open-plus' : 'open-stickers')));
  if (mode === 'plus') renderPlusTray(); else renderStickerTray();
  $('#input').blur();
  scrollBottom(true);
}

function renderPlusTray() {
  $('#tray').innerHTML = '<div class="tray-big">'
    + '<button data-act="pick-image"><span class="ic">'
    + '<svg viewBox="0 0 24 24" width="24" height="24" fill="none" stroke="currentColor" stroke-width="1.5">'
    + '<rect x="3.5" y="4.5" width="17" height="15" rx="3"/><circle cx="9" cy="10" r="1.6"/>'
    + '<path d="M5 17l4.5-4.5 3.5 3.5 2.5-2.5L20 17" stroke-linecap="round"/></svg></span>图片</button>'
    + '</div>';
}

const ST_UP_CELL = '<div class="tray-cell up" data-act="upload-sticker" title="上传表情">'
  + '<svg viewBox="0 0 24 24" width="22" height="22" fill="none" stroke="currentColor"'
  + ' stroke-width="1.6" stroke-linecap="round"><path d="M12 6v12M6 12h12"/></svg></div>';

function paintStickerTray(list, tip, note) {
  const t = $('#tray');
  if (!t) return;
  t.innerHTML = '<div class="tray-grid" id="st-grid">'
    + (list || []).map((st) => '<div class="tray-cell" data-act="send-sticker" data-id="' + st.id + '">'
      + '<img src="' + esc(st.url) + '" alt=""></div>').join('')
    + ST_UP_CELL + '</div>'
    + '<div class="tray-tip" style="padding:10px 4px 2px">' + tip + '</div>'
    + (note ? '<div class="tray-tip" style="padding:0 8px 10px">' + note + '</div>' : '');
  $$('.tray-cell[data-id]', t).forEach((cell) => {
    bindLongPress(cell, () => deleteSticker(Number(cell.getAttribute('data-id'))));
  });
  const g = $('#st-grid');
  if (g) {
    g.addEventListener('click', (ev) => {
      if (ev.target.closest('[data-act]')) return;
      const f = $('#st-file');
      if (f) f.click();
    });
  }
}

async function renderStickerTray() {
  // 先铺骨架：不管接口成不成，上传格和提示都在，不会卡在「读取中」
  paintStickerTray(STICKERS, '读取中…', '');
  try {
    const d = await Promise.race([
      api('/api/stickers'),
      new Promise((_, rej) => setTimeout(() => rej(new Error('超时')), 8000)),
    ]);
    STICKERS = d.stickers || [];
    const tip = d.limit
      ? ('已存 ' + STICKERS.length + ' / ' + d.limit + ' · 长按删除 · 点空白处上传')
      : ('已存 ' + STICKERS.length + ' · 长按删除 · 点空白处上传');
    paintStickerTray(STICKERS, tip, STICKERS.length ? '' : '还没有表情，点 ＋ 上传，或长按聊天里的图片存下来');
  } catch (e) {
    paintStickerTray(STICKERS, '表情读取失败，点 ＋ 上传', '');
  }
}

async function uploadSticker(file) {
  try {
    const data = await fileToWebp(file);
    const up = await api('/api/media', 'POST', { data: data });
    await api('/api/stickers', 'POST', { media_id: up.media.id });
    toast('已存为表情');
    renderStickerTray();
  } catch (e) { toast('上传失败：' + (e.message || '未知错误')); }
}

const onStickerPicked = (e) => {
  const file = e.target.files && e.target.files[0];
  e.target.value = '';
  if (file) uploadSticker(file);
};

async function deleteSticker(id) {
  try {
    await api('/api/stickers/' + id, 'DELETE');
    toast('已删除');
    if (trayMode === 'stickers') renderStickerTray();
  } catch (e) { toast(e.message); }
}

async function sendSticker(id) {
  document.querySelectorAll('.mask').forEach((m) => m.remove());
  try {
    await api('/api/conversations/' + S.cur.id + '/messages', 'POST', { media_id: id, body: '' });
  } catch (e) { toast(e.message); }
}

/* ---------------- 群聊 @ ---------------- */

function closeAtPop() {
  $$('.at-pop').forEach((n) => n.remove());
}

function openAtPop() {
  if (!S.cur || S.cur.kind !== 'group') return;
  const mems = (S.cur.members || []).filter((x) => Number(x.id) !== Number(S.me.id));
  if (!mems.length) return;
  closeAtPop();
  const pop = document.createElement('div');
  pop.className = 'at-pop';
  pop.innerHTML = mems.map((m) => '<div class="item" data-act="at-pick" data-id="' + m.id + '">'
    + avatar(m, 'sm') + '<span>' + esc(displayName(m)) + '</span></div>').join('');
  document.body.appendChild(pop);
  const bar = $('#quote-bar');
  const anchor = (bar && !bar.classList.contains('hidden')) ? bar : document.querySelector('.composer');
  const c = anchor.getBoundingClientRect();
  const r = pop.getBoundingClientRect();
  pop.style.left = Math.max(8, Math.min(c.left + 8, window.innerWidth - r.width - 8)) + 'px';
  pop.style.top = Math.max(8, c.top - r.height - 8) + 'px';
  // 别让点选人时输入框失焦
  pop.addEventListener('pointerdown', (ev) => ev.preventDefault());
}

function insertMention(mem) {
  const el = $('#input');
  if (!el || !mem) return;
  el.value = el.value.replace(/@$/, '@' + displayName(mem) + ' ');
  closeAtPop();
  el.focus();
  autoGrow(el);
}

/* ---------------- 消息长按菜单 ---------------- */

let pressTimer = null;
let longPressed = false;
let menuOpenedAt = 0;

function bindLongPress(el, fn) {
  let sx = 0;
  let sy = 0;

  const start = (x, y) => {
    longPressed = false;
    clearTimeout(pressTimer);
    sx = x;
    sy = y;
    pressTimer = setTimeout(() => {
      longPressed = true;
      fn();
      // 有的浏览器长按完不补 click，别让标记一直挂着吃下一次点击
      setTimeout(() => { longPressed = false; }, 900);
    }, 420);
  };
  const moved = (x, y) => {
    if (Math.abs(x - sx) > 10 || Math.abs(y - sy) > 10) clearTimeout(pressTimer);
  };

  // 触摸走 touch：pointermove 在手机上会持续冒出来，一点抖动就把菜单掐了
  el.addEventListener('touchstart', (e) => {
    const t = e.touches[0];
    if (t) start(t.clientX, t.clientY);
  }, { passive: true });
  el.addEventListener('touchmove', (e) => {
    const t = e.touches[0];
    if (t) moved(t.clientX, t.clientY);
  }, { passive: true });
  el.addEventListener('touchend', () => clearTimeout(pressTimer));
  el.addEventListener('touchcancel', () => clearTimeout(pressTimer));

  // 鼠标只认 pointer
  el.addEventListener('pointerdown', (e) => {
    if (e.pointerType === 'mouse') start(e.clientX, e.clientY);
  });
  el.addEventListener('pointerup', () => clearTimeout(pressTimer));
  el.addEventListener('pointercancel', () => clearTimeout(pressTimer));
}

function msgById(id) {
  return S.msgs.find((m) => Number(m.id) === Number(id));
}

function canRecall(m) {
  if (Number(m.recalled) === 1) return false;
  const mine = Number(m.sender_id) === Number(S.me.id);
  const mod = S.cur && (S.cur.my_role === 'owner' || S.cur.my_role === 'admin');
  if (!mine && !mod) return false;
  if (mine && !mod && (Math.floor(Date.now() / 1000) - Number(m.created_at)) > 300) return false;
  return true;
}

function memberActions(id) {
  const m = (S.cur.members || []).find((x) => Number(x.id) === Number(id));
  if (!m) return;
  const isAdmin = m.member_role === 'admin';
  openSheet(displayName(m),
    '<div class="card" style="margin:0">'
    + '<div class="item" data-act="set-role" data-id="' + id + '" data-role="'
    + (isAdmin ? 'member' : 'admin') + '"><div class="txt"><div class="t1">'
    + (isAdmin ? '取消群管理员' : '设为群管理员') + '</div></div></div>'
    + '<div class="item" data-act="member-card" data-id="' + id + '"><div class="txt">'
    + '<div class="t1">查看资料卡</div></div></div></div>', '');
}

async function reloadConv() {
  if (!S.cur) return;
  const d = await api('/api/conversations/' + S.cur.id);
  S.cur = d.conversation;
  S.cur.members = d.members || [];
  await loadConvs(true);
}

let typingHideTimer = null;
let typingSentAt = 0;

function showTyping() {
  const el = $('#chat-title');
  if (!el || !S.cur) return;
  el.textContent = '对方正在输入…';
  el.classList.add('typing');
  clearTimeout(typingHideTimer);
  typingHideTimer = setTimeout(() => hideTyping(), 4000);
}

function hideTyping() {
  clearTimeout(typingHideTimer);
  const el = $('#chat-title');
  if (!el) return;
  el.classList.remove('typing');
  if (S.cur) el.textContent = convTitle(S.cur, S.cur.members || []);
}

function sendTyping(active) {
  if (!S.cur) return;
  if (S.cur.kind !== 'direct' && S.cur.kind !== 'pkn') return;
  const now = Date.now();
  if (active && now - typingSentAt < 1500) return;
  typingSentAt = active ? now : 0;
  api('/api/conversations/' + S.cur.id + '/typing', 'POST', { active: !!active }).catch(() => {});
}

function openViewImage(src) {
  if (!src) return;
  openSheet(null, '<div class="view-wrap"><img src="' + esc(src) + '" alt=""></div>', '');
}

function closeMsgMenu() {
  $$('.msg-menu').forEach((el) => el.remove());
}

/** 长按气泡：贴着气泡弹出的小菜单，微信那套。 */
function openMsgMenu(mid) {
  const m = msgById(mid);
  if (!m) return;
  const row = document.querySelector('.row[data-mid="' + m.id + '"]');
  if (!row) return;
  closeMsgMenu();

  const items = [];
  if (canRecall(m)) items.push(['recall-msg', '撤回', m.id]);
  if (m.kind !== 'image') items.push(['select-msg', '选择文本', m.id]);
  items.push(['quote-msg', '引用', m.id]);
  items.push(['hide-msg', '删除', m.id]);
  if (m.kind === 'image' && m.media && m.media.id) {
    items.push(['save-media', '保存图片', m.id]);
    items.push(['save-sticker', '存表情', m.media.id]);
  }

  const box = document.createElement('div');
  box.className = 'msg-menu';
  box.innerHTML = items.map((it) => '<button data-act="' + it[0] + '" data-id="' + it[2] + '">'
    + it[1] + '</button>').join('') + '<i class="caret"></i>';
  document.body.appendChild(box);

  const bubble = row.querySelector('.bubble') || row;
  const b = bubble.getBoundingClientRect();
  const r = box.getBoundingClientRect();
  const pad = 8;
  let left = b.left + b.width / 2 - r.width / 2;
  left = Math.min(Math.max(left, pad), window.innerWidth - r.width - pad);
  let top = b.top - r.height - 9;
  let below = false;
  if (top < pad) { top = b.bottom + 9; below = true; }
  top = Math.min(top, window.innerHeight - r.height - pad);
  box.classList.toggle('below', below);
  box.style.left = left + 'px';
  box.style.top = top + 'px';
  const cx = Math.min(Math.max(b.left + b.width / 2 - left, 16), r.width - 16);
  box.style.setProperty('--caret', cx + 'px');

  menuOpenedAt = Date.now();
}

/** 点「选择文本」才放开这一条的文字选择，并直接全选，方便复制。 */
function selectMsgText(id) {
  const m = msgById(id);
  closeMsgMenu();
  if (!m) return;
  const row = document.querySelector('.row[data-mid="' + m.id + '"]');
  if (!row) return;
  $$('.row.selectable').forEach((el) => el.classList.remove('selectable'));
  row.classList.add('selectable');
  const bubble = row.querySelector('.bubble');
  if (!bubble) return;
  const range = document.createRange();
  range.selectNodeContents(bubble);
  const sel = window.getSelection();
  sel.removeAllRanges();
  sel.addRange(range);
}

async function recallMsg(id) {
  closeMsgMenu();
  try { await api('/api/messages/' + id + '/recall', 'POST', {}); }
  catch (e) { toast(e.message); }
}

async function hideMsg(id) {
  closeMsgMenu();
  try {
    await api('/api/messages/' + id + '/hide', 'POST', {});
    S.msgs = S.msgs.filter((m) => Number(m.id) !== Number(id));
    renderMsgs();
    toast('已删除');
  } catch (e) { toast(e.message); }
}

async function saveMedia(mid) {
  const m = msgById(mid);
  closeMsgMenu();
  if (!m || !m.media || !m.media.url) return;
  const name = 'kokona-' + m.id + '.webp';
  try {
    const r = await fetch(m.media.url, { cache: 'force-cache' });
    const blob = await r.blob();
    const a = document.createElement('a');
    a.href = URL.createObjectURL(blob);
    a.download = name;
    document.body.appendChild(a);
    a.click();
    a.remove();
    setTimeout(() => URL.revokeObjectURL(a.href), 4000);
    toast('已保存');
  } catch (e) {
    window.open(m.media.url, '_blank');
  }
}

async function saveSticker(mediaId) {
  closeMsgMenu();
  try {
    const d = await api('/api/stickers', 'POST', { media_id: Number(mediaId) });
    toast('已存表情 ' + d.used);
  } catch (e) { toast(e.message); }
}

function autoGrow(el) {
  if (!el) return;
  const cs = getComputedStyle(el);
  const cap = parseFloat(cs.maxHeight) || 102;
  const min = parseFloat(cs.minHeight) || 40;
  if (!el.value) {
    el.style.height = '';
    el.style.overflowY = 'hidden';
    return;
  }
  // 先塌回 auto 才量得到真实内容高度；量完立刻写回，中间不会渲染出闪跳
  el.style.height = 'auto';
  const h = Math.min(el.scrollHeight, cap);
  el.style.height = Math.max(h, min) + 'px';
  const over = el.scrollHeight > cap + 1;
  el.style.overflowY = over ? 'auto' : 'hidden';
  if (over) el.scrollTop = el.scrollHeight;
}

async function sendMsg() {
  const el = $('#input');
  const body = el.value.trim();
  if (!body || !S.cur) return;
  el.value = '';
  autoGrow(el);
  try {
    const d = await api('/api/conversations/' + S.cur.id + '/messages', 'POST',
      { body: body, quote_id: QUOTE ? QUOTE.id : 0 });
    clearQuote();
    sendTyping(false);
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
    if (d.type === 'typing') {
      if (S.cur && Number(S.cur.id) === Number(d.conv_id) && Number(d.user_id) !== Number(S.me.id)) {
        if (d.active) showTyping(); else hideTyping();
      }
    } else if (d.type === 'message_recalled') {
      const hit = S.msgs.find((x) => Number(x.id) === Number(d.message_id));
      if (hit && S.cur && Number(S.cur.id) === Number(d.conv_id)) {
        hit.recalled = 1;
        hit.body = '';
        hit.media = null;
        hit.recall_by = d.by;
        renderMsgs();
      }
      loadConvs(true);
    } else if (d.type === 'message') {
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
      if (S.cur && S.cur.id === d.conv_id) { S.cur = null; showList(); }
    } else if (d.type === 'announcement') {
      loadAnns().then(() => popAnnouncement());
    } else if (d.type === 'friend') {
      loadFriends();
    }
  };
}

/* ---------------- 面板 ---------------- */

function showPanel(title, html) {
  const p = $('#panel-view');
  p.innerHTML = '<div class="panel-head"><button class="icon-btn back" data-act="back">‹</button><b>'
    + esc(title) + '</b><span style="width:34px"></span></div>'
    + '<div class="panel-body">' + html + '</div>';
  p.classList.remove('hidden');
  $('#chat-view').classList.add('hidden');
  document.body.classList.add('panel-open');
  document.body.classList.remove('chat-open');
}

async function loadFriends() {
  try {
    const d = await api('/api/friends');
    S.friends = d.friends || [];
    S.blocks = d.blocks || [];
    if (S.view === 'contacts') showContacts();
  } catch (e) { /* 忽略 */ }
}

function showContacts() {
  S.view = 'contacts';
  const friendRows = S.friends.length
    ? S.friends.map((f) => '<div class="item" data-act="user-card" data-id="' + f.id + '">'
        + avatar(f, 'sm') + '<div class="txt"><div class="t1">' + esc(displayName(f))
        + '</div><div class="t2">@' + esc(f.username) + '</div></div>'
        + '<span class="arrow">›</span></div>').join('')
    : '<div class="empty">通讯录还是空的，去「添加好友」搜一个吧</div>';

  const groups = S.convs.filter((c) => c.kind === 'group');
  const groupRows = groups.length
    ? groups.map((g) => '<div class="item" data-act="open-conv" data-id="' + g.id + '">'
        + convAvatar(g, 'sm')
        + '<div class="txt"><div class="t1">' + esc(g.title) + '</div><div class="t2">'
        + (g.member_count || 0) + ' 人</div></div><span class="arrow">›</span></div>').join('')
    : '<div class="empty">还没有群聊</div>';

  showPanel('通讯录',
    '<h2>好友（' + S.friends.length + '）</h2><div class="card">' + friendRows + '</div>'
    + '<h2>群聊（' + groups.length + '）</h2><div class="card">' + groupRows + '</div>'
    + '<div class="set-note">要加新朋友，打开左上角菜单里的「添加好友」。</div>'
  );
}

function showAddFriend() {
  S.view = 'add';
  showPanel('添加好友',
    '<div class="side-search" style="padding:0 0 12px"><input id="uq" placeholder="输入用户名或显示名" autocomplete="off"></div>'
    + '<div id="user-results"><div class="empty" style="padding:14px">支持模糊匹配，也能搜到自己</div></div>'
  );

  const uq = $('#uq');
  let timer = null;
  uq.addEventListener('input', () => {
    clearTimeout(timer);
    timer = setTimeout(doSearch, 320);
  });
  setTimeout(() => uq.focus(), 60);
}

async function loadSubs() {
  if (Number(S.me.is_sub) === 1) { S.subs = []; S.subCanCreate = false; return; }
  try {
    const d = await api('/api/subs');
    S.subs = d.subs || [];
    S.subCanCreate = d.can_create === true;
  } catch (e) { S.subs = []; S.subCanCreate = false; }
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
      let btn;
      if (u.is_self) {
        btn = '<button class="code-btn" data-act="self-card">我的资料卡</button>';
      } else if (u.is_friend) {
        btn = '<button class="code-btn" data-act="open-dm" data-id="' + u.id + '">聊天</button>';
      } else {
        btn = '<button class="code-btn" data-act="add-friend" data-id="' + u.id + '">添加</button>';
      }
      const pill = u.is_self ? ' <span class="pill">我</span>' : '';
      return '<div class="item">' + avatar(u, 'sm') + '<div class="txt"><div class="t1">' + esc(displayName(u))
        + pill + '</div><div class="t2">@' + esc(u.username) + '</div></div>' + btn + '</div>';
    }).join('') + '</div>';
  } catch (e) { toast(e.message); }
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

function openSheet(title, bodyHtml, footHtml, sheetId) {
  const mask = document.createElement('div');
  mask.className = 'mask';
  if (sheetId) mask.id = sheetId;
  const head = title === null ? ''
    : '<div class="sheet-head"><b>' + esc(title) + '</b>'
      + '<button class="icon-btn" data-close="1">✕</button></div>';
  mask.innerHTML = '<div class="sheet">' + head
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
      + '<label>备注名</label>'
      + '<input id="alias-in" placeholder="给 TA 起个备注" value="' + esc(myAlias) + '">'
      + '<button class="btn" data-act="save-alias">保存备注</button>'
      + '</div>'
      + '<div class="card" style="margin:0 14px 14px">'
      + '<div class="item" data-act="' + (blocked ? 'unblock' : 'block') + '" data-id="' + peer.id + '">'
      + '<div class="txt"><div class="t1">' + (blocked ? '解除黑名单' : '加入黑名单') + '</div></div></div>'
      + '<div class="item" data-act="unfriend" data-id="' + peer.id + '">'
      + '<div class="txt"><div class="t1" style="color:#c1503c">删除好友</div>'
      + '<div class="t2">对方不会收到通知</div></div></div>'
      + '<div class="item" data-act="del-conv"><div class="txt"><div class="t1" style="color:#c1503c">'
      + '删除这个聊天</div></div></div>'
      + '</div>', '');
  } else {
    const role = conv.my_role || 'member';
    const canEdit = role === 'owner' || role === 'admin';
    const isOwner = role === 'owner';

    const memberRows = (conv.members || []).map((m) => {
      let tag = '';
      if (m.member_role === 'owner') tag = '<span class="pill role">群主</span>';
      else if (m.member_role === 'admin') tag = '<span class="pill role">管理员</span>';
      const tappable = isOwner && Number(m.id) !== Number(S.me.id);
      return '<div class="item"' + (tappable ? ' data-act="member-actions" data-id="' + m.id + '"' : '') + '>'
        + avatar(m, 'sm') + '<div class="txt"><div class="t1">' + esc(displayName(m)) + tag
        + '</div><div class="t2">@' + esc(m.username) + '</div></div>'
        + (tappable ? '<span class="arrow">\u203a</span>' : '') + '</div>';
    }).join('');

    openSheet('群聊设置',
      '<div class="gset-head">' + convAvatar(conv, 'lg')
      + '<div class="gset-info"><div class="gset-name">' + esc(conv.title) + '</div>'
      + '<div class="gset-sub">' + ((conv.members || []).length) + ' 人'
      + (isOwner ? ' · 你是群主' : (canEdit ? ' · 群管理员' : '')) + '</div></div>'
      + (canEdit ? '<button class="code-btn" data-act="pick-group-avatar">换头像</button>' : '')
      + '</div>'
      + (canEdit ? '<input type="file" id="gv-file" accept="image/*" hidden>' : '')

      + (canEdit ? '<div class="mini-form"><label>群名</label>'
        + '<input id="gname-in" value="' + esc(conv.title) + '">'
        + '<button class="btn" data-act="save-gname">保存群名</button></div>' : '')

      + '<div class="mini-form"><label>群公告</label>'
      + (canEdit
        ? '<textarea id="gnote-in" rows="3">' + esc(conv.notice || '') + '</textarea>'
          + '<button class="btn" data-act="save-gnotice">保存群公告</button>'
        : '<div class="set-note" style="margin:0">'
          + (conv.notice ? esc(conv.notice) : '还没有群公告') + '</div>')
      + '</div>'

      + '<div class="set-group-head">群成员（' + (conv.members || []).length + '）</div>'
      + '<div class="card" style="margin:0 14px 14px">' + memberRows + '</div>'

      + (S.me.is_admin
        ? '<div class="set-group-head">消息留存</div>'
          + '<div class="mini-pw"><input id="ghist-in" type="number" value="'
          + (conv.history_max || 200) + '"><button class="btn" data-act="save-ghist">保存</button></div>'
          + '<div class="set-note">200 / 300 / 500 / 1000，只影响之后的消息。</div>'
        : '')

      + '<div class="card" style="margin:0 14px 14px">'
      + '<div class="item" data-act="' + (isOwner ? 'del-conv' : 'leave-conv') + '">'
      + '<div class="txt"><div class="t1" style="color:#c1503c">'
      + (isOwner ? '解散群聊' : '退出群聊') + '</div></div></div></div>', '');
    const gv = $('#gv-file');
    if (gv) gv.addEventListener('change', onGroupAvatarPicked);
  }
}

/* ---------------- 表单类弹层 ---------------- */

/** 个人资料 / 账号设置：所有登录用户都有这一页。 */
async function openSettings() {
  S.view = 'settings';
  await loadSubs();
  await refreshPushState();
  renderSettings();
}

function wssEndpoint() {
  return 'wss://' + location.host + BASE + '/ws';
}

function renderSettings() {
  const me = S.me;
  const isSub = Number(me.is_sub) === 1;
  const tag = me.is_admin ? ' \u00b7 \u7ba1\u7406\u5458' : (isSub ? ' \u00b7 \u5b50\u8d26\u53f7' : '');
  const url = wssEndpoint();

  let wss = '';
  if (isSub) {
    wss = '<div class="set-note">\u5b50\u8d26\u53f7\u4e0d\u80fd\u518d\u521b\u5efa WSS \u8d26\u53f7\u3002</div>';
  } else if (S.subs.length) {
    const s = S.subs[0];
    wss = '<div class="item"><div class="txt"><div class="t1">\u663e\u793a\u540d</div>'
      + '<div class="t2">' + esc(s.display_name) + '</div></div></div>'
      + '<div class="mini-pw"><input id="sub-dn" maxlength="30" value="' + esc(s.display_name) + '">'
      + '<button class="btn" data-act="save-sub-dn" data-id="' + s.id + '">\u6539\u540d</button></div>'
      + '<div class="mini-pw"><input id="sub-pw" type="password" placeholder="\u65b0\u5bc6\u7801\uff08\u22656 \u4f4d\uff0c\u7559\u7a7a\u4e0d\u6539\uff09">'
      + '<button class="btn" data-act="save-sub-pw" data-id="' + s.id + '">\u91cd\u8bbe</button></div>'
      + '<div class="item" data-act="del-sub" data-id="' + s.id + '"><div class="txt">'
      + '<div class="t1" style="color:var(--danger)">\u5220\u9664 WSS \u8d26\u53f7</div>'
      + '<div class="t2">\u548c\u5b83\u7684\u804a\u5929\u8bb0\u5f55\u4f1a\u7559\u4e0b</div></div></div>'
      + '<div class="set-note">\u7528\u6237\u540d\u8ddf\u4e3b\u8d26\u53f7\u5171\u7528\uff0c\u53ea\u9700\u8981\u5bc6\u7801\uff1a<br><code>'
      + esc(url) + '?user=' + esc(me.username) + '&amp;pass=\u5bc6\u7801</code></div>';
  } else if (S.subCanCreate) {
    wss = '<div class="mini-pw"><input id="sub-dn-new" maxlength="30" placeholder="\u663e\u793a\u540d\uff08\u53ef\u7559\u7a7a\uff09"></div>'
      + '<div class="mini-pw"><input id="sub-pw-new" type="password" placeholder="\u5bc6\u7801\uff08\u22656 \u4f4d\uff09">'
      + '<button class="btn" data-act="new-sub">\u521b\u5efa</button></div>'
      + '<div class="set-note">\u4e0d\u4f1a\u65b0\u6ce8\u518c\u4e00\u4e2a\u8d26\u53f7\uff1a\u7528\u6237\u540d\u4ecd\u662f\u4f60\u81ea\u5df1\u7684\uff0c\u53ea\u662f\u591a\u4e00\u4e2a\u5bc6\u7801\u3002\u8fde <code>'
      + esc(url) + '</code> \u65f6\u7528 <code>user=' + esc(me.username) + '</code>\u3002</div>';
  } else {
    wss = '<div class="set-note">\u5f53\u524d\u8d26\u53f7\u4e0d\u80fd\u518d\u521b\u5efa WSS \u8d26\u53f7\u3002</div>';
  }

  showPanel('\u8bbe\u7f6e',
    '<div class="set-hero">'
    + coverImg(me, '', 'set-cover')
    + '<div class="cover-scrim"></div>'
    + '<div class="set-tools"><button data-act="pick-avatar">\u6362\u5934\u50cf</button>'
    + '<button data-act="pick-cover">\u6362\u5c01\u9762</button></div>'
    + '<img class="set-av" id="set-av" src="' + esc(avatarSrc(me) || ICON) + '" alt="">'
    + '<div class="set-hero-txt"><div class="set-name">' + esc(displayName(me)) + '</div>'
    + '<div class="set-user">@' + esc(me.username) + esc(tag) + '</div></div></div>'

    + '<div class="set-group">'
    + '<div class="item" data-act="edit-name"><div class="txt"><div class="t1">\u663e\u793a\u540d</div>'
    + '<div class="t2">' + esc(displayName(me)) + '</div></div><span class="arrow">\u203a</span></div>'
    + '<div class="item"><div class="txt"><div class="t1">\u8d26\u53f7</div><div class="t2">@'
    + esc(me.username) + '</div></div></div>'
    + (me.email ? '<div class="item"><div class="txt"><div class="t1">\u90ae\u7bb1</div><div class="t2">'
      + esc(me.email) + '</div></div></div>' : '')
    + '</div>'

    + '<div class="set-group"><div class="set-group-head">WSS \u8d26\u53f7</div>' + wss + '</div>'

    + '<div class="set-group"><div class="set-group-head">通知</div>' + pushRow() + '</div>'
    + '<div class="set-group"><div class="set-group-head">\u8d26\u53f7\u5b89\u5168</div>'
    + '<div class="item" data-act="password"><div class="txt"><div class="t1">\u4fee\u6539\u5bc6\u7801</div></div>'
    + '<span class="arrow">\u203a</span></div></div>'

    + '<div class="set-group">'
    + '<div class="item" data-act="drawer-ann"><div class="txt"><div class="t1">\u516c\u544a\u677f</div></div>'
    + '<span class="arrow">\u203a</span></div>'
    + (me.is_admin ? '<div class="item" data-act="drawer-admin"><div class="txt"><div class="t1">\u7ba1\u7406\u540e\u53f0</div>'
      + '</div><span class="arrow">\u203a</span></div>' : '')
    + '<div class="item" data-act="logout"><div class="txt"><div class="t1" style="color:var(--danger)">\u9000\u51fa\u767b\u5f55</div>'
    + '</div></div></div>'
    + '<div class="set-note">\u5934\u50cf\u4e0e\u5c01\u9762\u90fd\u5728\u672c\u5730\u88c1\u597d\u3001\u8f6c\u6210 webp \u518d\u4e0a\u4f20\u3002</div>'
    + '<input type="file" id="av-file" accept="image/*" hidden>'
    + '<input type="file" id="cover-file" accept="image/*" hidden>',
    '');

  const av = $('#av-file');
  if (av) av.addEventListener('change', onAvatarPicked);
  const cv = $('#cover-file');
  if (cv) cv.addEventListener('change', onCoverPicked);
}

/** 把服务端返回的最新用户信息同步到界面各处。 */
function applyMe(u) {
  if (!u) return;
  S.me = Object.assign(S.me, u);
  const av = avatarSrc(S.me) || ICON;
  const a = $('#me-av');
  if (a) a.src = av;
  const n = $('#me-name');
  if (n) n.textContent = displayName(S.me);
  const sa = $('#set-av');
  if (sa) sa.src = av;
  const sc = $('#set-cover');
  const cv = coverSrc(S.me);
  if (sc) {
    if (cv) { sc.src = cv; sc.classList.remove('hidden'); }
    else { sc.removeAttribute('src'); sc.classList.add('hidden'); }
  }
  renderDrawer();
}

function editName() {
  openSheet('修改显示名',
    '<div class="mini-form"><label>显示名</label>'
    + '<input id="dn-in" maxlength="30" value="' + esc(displayName(S.me)) + '" placeholder="别人看到的名字">'
    + '<button class="btn" data-act="save-name">保存</button></div>', '');
}

function changePassword() {
  openSheet('修改密码',
    '<div class="mini-form">'
    + '<input id="old-pw" type="password" placeholder="原密码" autocomplete="current-password">'
    + '<input id="new-pw" type="password" placeholder="新密码，至少 6 位" autocomplete="new-password">'
    + '<input id="new-pw2" type="password" placeholder="再输一次新密码" autocomplete="new-password">'
    + '<button class="btn" data-act="save-pw">确定修改</button></div>', '');
}

/* ---------------- 头像：选图 → 拖动/缩放裁剪 → 转 webp 上传 ---------------- */

const CROP = { img: null, mode: 'avatar', zoom: 1, x: 0, y: 0, base: 1, w: 0, h: 0, bw: 0, bh: 0 };

function pickImage(handler) {
  return (e) => {
    const file = e.target.files && e.target.files[0];
    e.target.value = '';
    if (!file) return;
    if (!/^image\//.test(file.type)) { toast('\u8bf7\u9009\u62e9\u56fe\u7247\u6587\u4ef6'); return; }
    if (file.size > 10 * 1024 * 1024) { toast('\u56fe\u7247\u592a\u5927\uff0810MB \u4ee5\u5185\uff09'); return; }
    const reader = new FileReader();
    reader.onload = () => handler(String(reader.result || ''));
    reader.onerror = () => toast('\u8bfb\u53d6\u56fe\u7247\u5931\u8d25');
    reader.readAsDataURL(file);
  };
}

const onAvatarPicked = pickImage((src) => openCropper(src, 'avatar'));
const onCoverPicked = pickImage((src) => openCropper(src, 'cover'));
const onGroupAvatarPicked = pickImage((src) => {
  CROP.convId = S.cur ? S.cur.id : 0;
  openCropper(src, 'group');
});

function cropApply() {
  if (!CROP.img) return;
  const W = CROP.bw, H = CROP.bh;
  const s = CROP.base * CROP.zoom;
  const dw = CROP.w * s, dh = CROP.h * s;
  const maxX = Math.max(0, (dw - W) / 2), maxY = Math.max(0, (dh - H) / 2);
  CROP.x = Math.min(maxX, Math.max(-maxX, CROP.x));
  CROP.y = Math.min(maxY, Math.max(-maxY, CROP.y));
  CROP.img.style.width = dw + 'px';
  CROP.img.style.height = dh + 'px';
  CROP.img.style.transform = 'translate(-50%,-50%) translate(' + CROP.x + 'px,' + CROP.y + 'px)';
}

function openCropper(src, mode) {
  const cover = mode === 'cover';
  openSheet(cover ? '\u8c03\u6574\u5c01\u9762' : '\u8c03\u6574\u5934\u50cf',
    '<div class="crop-box' + (cover ? ' wide' : '') + '" id="crop-box">'
    + '<img id="crop-img" alt="">'
    + '<div class="crop-mask"></div>' + (cover ? '' : '<div class="crop-ring"></div>') + '</div>'
    + '<div class="crop-ctrl"><span>\u7f29\u653e</span>'
    + '<input type="range" id="crop-zoom" min="1" max="3" step="0.01" value="1"></div>',
    '<button class="btn" data-act="crop-save">\u4fdd\u5b58</button>');

  const box = $('#crop-box'), img = $('#crop-img'), range = $('#crop-zoom');
  if (!box || !img || !range) return;

  CROP.img = img; CROP.mode = cover ? 'cover' : (mode === 'group' ? 'group' : 'avatar');
  CROP.zoom = 1; CROP.x = 0; CROP.y = 0;

  const start = () => {
    CROP.w = img.naturalWidth || 1;
    CROP.h = img.naturalHeight || 1;
    CROP.bw = box.clientWidth || 240;
    CROP.bh = box.clientHeight || 240;
    CROP.base = Math.max(CROP.bw / CROP.w, CROP.bh / CROP.h);
    CROP.x = 0; CROP.y = 0;
    cropApply();
  };
  img.onload = start;
  img.src = src;
  if (img.complete && img.naturalWidth) start();

  range.addEventListener('input', () => { CROP.zoom = Number(range.value) || 1; cropApply(); });

  let drag = null;
  box.addEventListener('pointerdown', (ev) => {
    drag = { x: ev.clientX, y: ev.clientY, ox: CROP.x, oy: CROP.y };
    try { box.setPointerCapture(ev.pointerId); } catch (err) {}
  });
  box.addEventListener('pointermove', (ev) => {
    if (!drag) return;
    ev.preventDefault();
    CROP.x = drag.ox + (ev.clientX - drag.x);
    CROP.y = drag.oy + (ev.clientY - drag.y);
    cropApply();
  });
  const stop = () => { drag = null; };
  box.addEventListener('pointerup', stop);
  box.addEventListener('pointercancel', stop);
  box.addEventListener('pointerleave', stop);
}

async function saveCrop() {
  const img = CROP.img;
  if (!img || !CROP.bw) { toast('\u56fe\u7247\u8fd8\u6ca1\u51c6\u5907\u597d'); return; }
  const mode = CROP.mode || 'avatar';
  const cover = mode === 'cover';
  const outW = cover ? 720 : 256, outH = cover ? 480 : 256;

  // 按「实际渲染出来的像素」反推原图取景框：宽高各自算，绝不会把原图压成别的比例
  const boxEl = $('#crop-box');
  if (!boxEl) { toast('裁剪框丢了'); return; }
  const rect = img.getBoundingClientRect();
  const br = boxEl.getBoundingClientRect();
  if (!rect.width || !rect.height || !br.width || !br.height) { toast('图片还没准备好'); return; }
  const kx = img.naturalWidth / rect.width;
  const ky = img.naturalHeight / rect.height;

  let frameW = br.width, frameH = br.height;
  if (!cover) {
    // 头像是正方形：在框里取居中的正方形，保证输出不变形
    const side = Math.min(br.width, br.height);
    frameW = side; frameH = side;
  }
  const sw = frameW * kx;
  const sh = frameH * ky;
  const sx = ((br.left + br.width / 2) - rect.left) * kx - sw / 2;
  const sy = ((br.top + br.height / 2) - rect.top) * ky - sh / 2;
  const cv = document.createElement('canvas');
  cv.width = outW; cv.height = outH;
  const ctx = cv.getContext('2d');
  ctx.imageSmoothingEnabled = true;
  ctx.imageSmoothingQuality = 'high';
  ctx.drawImage(img, sx, sy, sw, sh, 0, 0, outW, outH);
  let data = cv.toDataURL('image/webp', 0.86);
  if (data.indexOf('data:image/webp') !== 0) data = cv.toDataURL('image/png');
  try {
    if (mode === 'group') {
      const cid = CROP.convId || (S.cur ? S.cur.id : 0);
      const g = await api('/api/conversations/' + cid + '/avatar', 'POST', { data: data });
      if (S.cur && Number(S.cur.id) === Number(cid)) S.cur.avatar = g.avatar;
      await loadConvs(true);
      document.querySelectorAll('.mask').forEach((m) => m.remove());
      toast('群头像已更新');
      chatSetting();
      return;
    }
    const d = await api(cover ? '/api/cover' : '/api/avatar', 'POST', { data: data });
    applyMe(d.user);
    document.querySelectorAll('.mask').forEach((m) => m.remove());
    toast(cover ? '\u5c01\u9762\u5df2\u66f4\u65b0' : '\u5934\u50cf\u5df2\u66f4\u65b0');
    if (S.view === 'settings') openSettings();
  } catch (err) {
    toast('\u4e0a\u4f20\u5931\u8d25\uff1a' + (err.message || '\u672a\u77e5\u9519\u8bef'));
  }
}

/* ---------------- \u8d44\u6599\u5361 ---------------- */

async function openUserCard(u) {
  if (!u || !u.id) return;
  const isSelf = Number(u.id) === Number(S.me.id);
  const isFriend = S.friends.some((f) => Number(f.id) === Number(u.id));
  const blocked = S.blocks.some((b) => Number(b.id) === Number(u.id));

  let acts = '';
  if (isSelf) {
    acts = '<div class="item" data-act="open-settings"><div class="txt"><div class="t1">\u7f16\u8f91\u6211\u7684\u8d44\u6599</div>'
      + '</div><span class="arrow">\u203a</span></div>';
  } else {
    acts = '<div class="item" data-act="dm-from-card" data-id="' + u.id + '"><div class="txt">'
      + '<div class="t1">\u53d1\u6d88\u606f</div></div><span class="arrow">\u203a</span></div>';
    if (isFriend) {
      acts += '<div class="item" data-act="alias-from-card" data-id="' + u.id + '"><div class="txt">'
        + '<div class="t1">\u8bbe\u7f6e\u5907\u6ce8</div></div><span class="arrow">\u203a</span></div>'
        + '<div class="item" data-act="' + (blocked ? 'unblock' : 'block') + '" data-id="' + u.id + '"><div class="txt">'
        + '<div class="t1">' + (blocked ? '\u89e3\u9664\u9ed1\u540d\u5355' : '\u52a0\u5165\u9ed1\u540d\u5355')
        + '</div></div></div>'
        + '<div class="item" data-act="unfriend" data-id="' + u.id + '"><div class="txt">'
        + '<div class="t1" style="color:var(--danger)">\u5220\u9664\u597d\u53cb</div></div></div>';
    }
  }

  const tag = u.is_sub ? ' \u00b7 WSS' : (u.role === 'admin' ? ' \u00b7 \u7ba1\u7406\u5458' : '');
  // 顶部沿用左侧抽屉那张卡片的样式：封面 + 暗角 + 方头像 + 名字 + @ID
  openSheet(null,
    '<div class="profile-card ucard-top">' + coverImg(u)
    + '<div class="cover-scrim"></div>'
    + '<button class="ucard-close" data-close="1">\u2715</button>'
    + '<img class="profile-av" src="' + esc(avatarSrc(u) || ICON) + '" alt="">'
    + '<div class="profile-name">' + esc(displayName(u)) + '</div>'
    + '<div class="profile-id">@' + esc(u.username) + esc(tag) + '</div>'
    + '</div>'
    + '<div class="ucard-acts set-group" style="border-radius:0">' + acts + '</div>', '', 'ucard-sheet');
}

async function openAliasSheet(uid) {
  let convId = 0, alias = '';
  try {
    const d = await api('/api/conversations', 'POST', { kind: 'direct', peer_id: Number(uid) });
    convId = d.conv_id;
    const full = await api('/api/conversations/' + convId);
    const mine = (full.members || []).find((m) => Number(m.id) === Number(S.me.id));
    alias = (mine && mine.alias) || '';
  } catch (e) {
    toast(e.message || '\u65e0\u6cd5\u6253\u5f00\u4f1a\u8bdd');
    return;
  }
  document.querySelectorAll('.mask').forEach((m) => m.remove());
  openSheet('\u8bbe\u7f6e\u5907\u6ce8',
    '<div class="mini-form"><label>\u7ed9 TA \u7684\u5907\u6ce8\uff08\u7559\u7a7a\u53d6\u6d88\uff09</label>'
    + '<input id="alias-in" maxlength="20" value="' + esc(alias) + '">'
    + '<button class="btn" data-act="save-alias" data-conv="' + convId + '">\u4fdd\u5b58</button></div>', '');
}

function editProfile() { openSettings(); }

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

/* ---------------- 事件 ---------------- */

/* 点一条消息：弹出它的完整时间（气泡上不再挂小字） */
document.addEventListener('click', (e) => {
  if (e.target.closest('[data-act]')) return;
  const row = e.target.closest('.row[data-ts]');
  if (!row) return;
  // 长按刚弹完菜单，别顺手把时间也弹出来
  if (Date.now() - menuOpenedAt < 600) return;
  toast(fmtFull(Number(row.getAttribute('data-ts'))));
});

/* 菜单外点一下、列表一滚，就收起来；顺便退出文字选择态 */
document.addEventListener('pointerdown', (e) => {
  if (!e.target.closest('.msg-menu')) closeMsgMenu();
  if (!e.target.closest('.at-pop')) closeAtPop();
  if (!e.target.closest('.row.selectable')) {
    $$('.row.selectable').forEach((el) => el.classList.remove('selectable'));
  }
}, true);

/* 长按气泡时不弹系统的图片/文字菜单 */
document.addEventListener('contextmenu', (e) => {
  if (e.target.closest('.row')) e.preventDefault();
});
window.addEventListener('resize', closeMsgMenu);

/* 触摸按压态用 class 控制，避免移动端 :active 黏在那一行 */
document.addEventListener('pointerdown', (e) => {
  const row = e.target.closest('.conv');
  if (row) row.classList.add('press');
}, true);
['pointerup', 'pointercancel', 'pointerleave'].forEach((ev) => {
  document.addEventListener(ev, () => {
    $$('.conv.press').forEach((el) => el.classList.remove('press'));
  }, true);
});

document.addEventListener('click', async (e) => {
  const el = e.target.closest('[data-act]');
  if (!el) return;
  // 长按之后浏览器补发的那次点击要吃掉；但菜单里的按钮必须照常响应
  if (longPressed) {
    longPressed = false;
    if (!el.closest('.msg-menu')) return;
  }
  const act = el.getAttribute('data-act');
  const id = el.getAttribute('data-id');

  try {
    if (act === 'drawer-open') { openDrawer(); }
    else if (act === 'drawer-contacts') { closeDrawer(); await loadFriends(); showContacts(); }
    else if (act === 'drawer-addfriend') { closeDrawer(); await loadFriends(); showAddFriend(); }
    else if (act === 'drawer-ann') { closeDrawer(); openAnnList(); }
    else if (act === 'open-settings') { closeDrawer(); openSettings(); }
    else if (act === 'drawer-password') { closeDrawer(); changePassword(); }
    else if (act === 'drawer-reload') { closeDrawer(); await loadConvs(); toast('已刷新'); }
    else if (act === 'drawer-admin') { location.href = BASE + '/admin'; }
    else if (act === 'drawer-profile') { closeDrawer(); openSettings(); }
    else if (act === 'pick-avatar') { const f = $('#av-file'); if (f) f.click(); }
    else if (act === 'pick-cover') { const f = $('#cover-file'); if (f) f.click(); }
    else if (act === 'pick-group-avatar') { const f = $('#gv-file'); if (f) f.click(); }
    else if (act === 'open-plus') { trayToggle('plus'); }
    else if (act === 'pick-image') { const f = $('#img-file'); if (f) f.click(); }
    else if (act === 'open-stickers') { trayToggle('stickers'); }
    else if (act === 'send-sticker') { await sendSticker(Number(id)); }
    else if (act === 'upload-sticker') { const f = $('#st-file'); if (f) f.click(); }
    else if (act === 'recall-msg') { await recallMsg(Number(id)); }
    else if (act === 'select-msg') { selectMsgText(Number(id)); }
    else if (act === 'quote-msg') { setQuote(msgById(Number(id))); }
    else if (act === 'quote-cancel') { clearQuote(); }
    else if (act === 'at-pick') {
      insertMention(((S.cur && S.cur.members) || []).find((x) => Number(x.id) === Number(id)));
    }
    else if (act === 'hide-msg') { await hideMsg(Number(id)); }
    else if (act === 'save-media') { await saveMedia(Number(id)); }
    else if (act === 'save-sticker') { await saveSticker(Number(id)); }
    else if (act === 'view-image') { openViewImage(el.getAttribute('data-src')); }
    else if (act === 'msg-user') {
      const uid = Number(id);
      let u = (S.cur && (S.cur.members || []).find((x) => Number(x.id) === uid))
        || S.friends.find((x) => Number(x.id) === uid);
      if (!u && S.me && Number(S.me.id) === uid) u = S.me;
      if (!u) {
        const hit = S.msgs.find((x) => Number(x.sender_id) === uid && x.sender);
        if (hit) u = hit.sender;
      }
      if (u) openUserCard(u);
    }
    else if (act === 'member-actions') { memberActions(Number(id)); }
    else if (act === 'member-card') {
      document.querySelectorAll('.mask').forEach((m) => m.remove());
      const mm = (S.cur.members || []).find((x) => Number(x.id) === Number(id));
      if (mm) openUserCard(mm);
    }
    else if (act === 'set-role') {
      const role = el.getAttribute('data-role');
      await api('/api/conversations/' + S.cur.id + '/members/' + id + '/role', 'POST', { role: role });
      document.querySelectorAll('.mask').forEach((m) => m.remove());
      await reloadConv();
      toast(role === 'admin' ? '已设为群管理员' : '已取消管理员');
      chatSetting();
    }
    else if (act === 'save-gnotice') {
      const v = ($('#gnote-in') && $('#gnote-in').value || '').trim();
      await api('/api/conversations/' + S.cur.id + '/notice', 'POST', { notice: v });
      document.querySelectorAll('.mask').forEach((m) => m.remove());
      await reloadConv();
      toast('群公告已保存');
      chatSetting();
    }
    else if (act === 'save-ghist') {
      const n = Number($('#ghist-in').value);
      await api('/api/conversations/' + S.cur.id + '/history', 'POST', { history_max: n });
      document.querySelectorAll('.mask').forEach((m) => m.remove());
      await reloadConv();
      toast('已设为留存 ' + n + ' 条');
      chatSetting();
    }
    else if (act === 'leave-conv') {
      if (!confirm('确定退出这个群吗？')) return;
      await api('/api/conversations/' + S.cur.id + '/leave', 'POST', {});
      document.querySelectorAll('.mask').forEach((m) => m.remove());
      S.cur = null;
      S.openId = null;
      await loadConvs(true);
      showList();
    }
    else if (act === 'push-on') { await pushEnable(); }
    else if (act === 'push-off') { await pushDisable(); }
    else if (act === 'push-test') { await pushTest(); }
    else if (act === 'push-ask-later') { pushNeverAsk(); document.querySelectorAll('.push-bubble').forEach((n) => n.remove()); }
    else if (act === 'push-ios-tip') { document.querySelectorAll('.mask').forEach((n) => n.remove()); showIosPushTip(); }
    else if (act === 'push-ask-ok') {
      pushNeverAsk();
      document.querySelectorAll('.push-bubble').forEach((n) => n.remove());
      await pushEnable();
    }
    else if (act === 'crop-save') { await saveCrop(); }
    else if (act === 'user-card') {
      let u = S.friends.find((x) => Number(x.id) === Number(id));
      if (!u && S.cur) u = (S.cur.members || []).find((x) => Number(x.id) === Number(id));
      if (!u && Number(id) === Number(S.me.id)) u = S.me;
      if (u) openUserCard(u);
    }
    else if (act === 'dm-from-card') {
      document.querySelectorAll('.mask').forEach((m) => m.remove());
      const d = await api('/api/conversations', 'POST', { kind: 'direct', peer_id: Number(id) });
      await loadConvs(true);
      openConv(d.conv_id);
    }
    else if (act === 'alias-from-card') { await openAliasSheet(Number(id)); }
    else if (act === 'edit-name') { editName(); }
    else if (act === 'password') { changePassword(); }
    else if (act === 'open-conv') { openConv(Number(id)); }
    else if (act === 'back') { showList(); }
    else if (act === 'send') { sendMsg(); }
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
      await loadFriends();
      showAddFriend();
    }
    else if (act === 'self-card') {
      document.querySelectorAll('.mask').forEach((m) => m.remove());
      openUserCard(S.me);
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
      if (S.view === 'add') doSearch(); else showContacts();
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
      const cid = el.getAttribute('data-conv') || (S.cur ? S.cur.id : 0);
      if (!cid) { toast('会话不存在'); return; }
      await api('/api/conversations/' + cid + '/alias', 'POST', { alias: v });
      toast('备注已保存');
      document.querySelectorAll('.mask').forEach((m) => m.remove());
      await loadConvs(true);
      if (S.cur && Number(S.cur.id) === Number(cid)) {
        S.cur.title = v || S.cur.title;
        $('#chat-title').textContent = S.cur.title;
      }
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
      await loadConvs(true);
      showList();
    }
    else if (act === 'new-sub') {
      const dn = ($('#sub-dn-new') ? $('#sub-dn-new').value.trim() : '');
      const pass = $('#sub-pw-new').value;
      if (pass.length < 6) { toast('密码至少 6 位'); return; }
      await api('/api/subs', 'POST', { display_name: dn || 'WSS 账号', password: pass });
      toast('WSS 账号已创建');
      await loadSubs();
      renderSettings();
    }
    else if (act === 'save-sub-dn') {
      const dn = $('#sub-dn').value.trim();
      if (!dn) { toast('显示名不能为空'); return; }
      await api('/api/subs/' + id, 'POST', { display_name: dn });
      toast('显示名已保存');
      await loadSubs();
      renderSettings();
    }
    else if (act === 'save-sub-pw') {
      const pw = $('#sub-pw').value;
      if (pw.length < 6) { toast('密码至少 6 位'); return; }
      await api('/api/subs/' + id, 'POST', { password: pw });
      toast('密码已重设，旧连接会断开');
      await loadSubs();
      renderSettings();
    }
    else if (act === 'del-sub') {
      if (!confirm('删除这个 WSS 账号？它的聊天记录会保留。')) return;
      await api('/api/subs/' + id, 'DELETE');
      toast('已删除');
      await loadSubs();
      renderSettings();
    }
    else if (act === 'ann-read') {
      await api('/api/announcements/' + id + '/read', 'POST', {});
      const b = el.closest('.ann-bubble');
      if (b) b.remove();
      await loadAnns();
      setTimeout(popAnnouncement, 120);
    }
    else if (act === 'save-name') {
      const v = $('#dn-in').value.trim();
      if (!v) { toast('显示名不能为空'); return; }
      const d = await api('/api/profile', 'POST', { display_name: v });
      applyMe(d.user);
      document.querySelectorAll('.mask').forEach((m) => m.remove());
      toast('显示名已保存');
      if (S.view === 'settings') openSettings();
    }
    else if (act === 'save-pw') {
      const n1 = $('#new-pw').value, n2 = $('#new-pw2').value;
      if (n1 !== n2) { toast('两次输入的新密码不一致'); return; }
      await api('/api/password', 'POST', {
        old_password: $('#old-pw').value, new_password: n1
      });
      toast('密码已修改');
      document.querySelectorAll('.mask').forEach((m) => m.remove());
    }
    else if (act === 'create-group') {
      const title = $('#g-title').value.trim() || '新群聊';
      const ids = $$('.sheet input[type=checkbox]:checked').map((x) => Number(x.value));
      const d = await api('/api/conversations', 'POST', { kind: 'group', title: title, member_ids: ids });
      document.querySelectorAll('.mask').forEach((m) => m.remove());
      await loadConvs(true);
      openConv(d.conv_id);
    }
    else if (act === 'logout') {
      if (!confirm('确定退出登录吗？')) return;
      await api('/api/logout', 'POST', {});
      location.href = BASE + '/login';
    }
  } catch (err) {
    toast(err.message || '操作失败');
  }
});

$('#search').addEventListener('input', renderConvs);

/* 点聊天标题看对方资料卡 */
$('#chat-title').addEventListener('click', () => {
  if (!S.cur || S.cur.kind !== 'direct') return;
  const peer = (S.cur.members || []).find((m) => Number(m.id) !== Number(S.me.id)) || S.cur.peer;
  if (peer && peer.id) openUserCard(peer);
});

/* 输入框高度只在 boot() 里管：那里会避开输入法组词阶段，别在这里再挂一个 input */
$('#input').addEventListener('keydown', function (e) {
  if (e.key === 'Enter' && !e.shiftKey && !e.isComposing && !COARSE) {
    e.preventDefault();
    sendMsg();
  }
});

$('#drawer').addEventListener('click', (e) => {
  if (e.target.id === 'drawer') closeDrawer();
});

document.addEventListener('visibilitychange', () => {
  if (document.visibilityState === 'visible' && S.cur) {
    api('/api/conversations/' + S.cur.id + '/read', 'POST', {}).catch(() => {});
  }
});

/* ---------------- 诊断日志（移动端常开，写到服务端排查用） ---------------- */

const DIAG = { on: false, verbose: false, sid: '', q: [], timer: null, last: {} };

(function initDiag() {
  const touch = ('ontouchstart' in window) || (navigator.maxTouchPoints > 0);
  DIAG.verbose = /(^|[?&])diag=1/.test(location.search);
  DIAG.on = touch || DIAG.verbose;
  DIAG.sid = Math.random().toString(36).slice(2, 8);
})();

// 触摸设备只上报真问题（报错、布局错位），不再把每次视口变化都写服务器；
// 要完整轨迹就在地址后加 ?diag=1
const DIAG_ALWAYS = { err: 1, rej: 1, bad: 1 };

function diagRect(sel) {
  const el = document.querySelector(sel);
  if (!el) return null;
  const r = el.getBoundingClientRect();
  return [Math.round(r.left), Math.round(r.top), Math.round(r.width), Math.round(r.height)];
}

function diagSnap() {
  const vv = window.visualViewport;
  const ta = document.querySelector('#input');
  const se = document.scrollingElement || document.documentElement;
  return {
    vw: window.innerWidth,
    vh: window.innerHeight,
    oh: window.outerHeight,
    ah: (window.screen && screen.availHeight) || 0,
    dh: document.documentElement.clientHeight,
    hh: Math.round(document.documentElement.getBoundingClientRect().height),
    bh: Math.round(document.body.getBoundingClientRect().height),
    vv: vv ? [Math.round(vv.width), Math.round(vv.height), Math.round(vv.offsetTop), Number(vv.scale.toFixed(2))] : null,
    st: Math.round(se.scrollTop || 0),
    kb: getComputedStyle(document.documentElement).getPropertyValue('--kb').trim(),
    app: diagRect('.app'),
    chat: diagRect('.chat-view'),
    msgs: diagRect('.msgs'),
    comp: diagRect('.composer'),
    ta: ta ? [Math.round(ta.getBoundingClientRect().height), ta.scrollHeight, ta.selectionStart] : null,
    ae: (document.activeElement && (document.activeElement.id || document.activeElement.tagName)) || ''
  };
}

function diag(ev, extra) {
  if (!DIAG.on) return;
  if (!DIAG.verbose && !DIAG_ALWAYS[ev]) return;
  const now = Date.now();
  if (DIAG.last[ev] && now - DIAG.last[ev] < 250) return;
  DIAG.last[ev] = now;
  DIAG.q.push(Object.assign({ e: ev, t: now }, diagSnap(), extra || {}));
  if (DIAG.q.length > 160) DIAG.q.shift();
  if (!DIAG.timer) DIAG.timer = setTimeout(function () { diagFlush(false); }, 1600);
}

function diagFlush(beacon) {
  clearTimeout(DIAG.timer);
  DIAG.timer = null;
  if (!DIAG.q.length) return;
  const body = JSON.stringify({ sid: DIAG.sid, events: DIAG.q.splice(0) });
  try {
    if (beacon && navigator.sendBeacon) {
      navigator.sendBeacon(BASE + '/api/diag', new Blob([body], { type: 'application/json' }));
    } else {
      fetch(BASE + '/api/diag', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: body,
        keepalive: true,
        cache: 'no-store'
      }).catch(function () {});
    }
  } catch (e) { /* 诊断失败不影响聊天 */ }
}

(async function boot() {
  $('#me-av').src = avatarSrc(S.me) || ICON;
  $('#me-name').textContent = displayName(S.me);
  renderDrawer();
  await loadConvs(true);
  await loadFriends();
  await loadAnns();
  // ---- 移动端键盘 ----
  // 两种内核，两套机制，必须分开处理：
  //   安卓 adjustResize：键盘一弹，布局视口跟着缩，CSS 的 100% 就是对的，
  //                      JS 再写高度只会写进一个和真实可见区不一致的数——之前就是这里翻车；
  //   iOS / adjustPan：布局视口不动，可见区被盖住，才需要 JS 把 app 高度改成可视高度。
  // 判据：布局视口比可视视口高出 60px 以上 = 键盘是「盖」上去的，此时才接管。
  const vv = window.visualViewport;
  const root = document.documentElement;
  let applied = 'css';
  window.syncViewport = () => {
    const lh = Math.round(window.innerHeight || 0);      // 布局视口
    const vh = vv ? Math.round(vv.height || 0) : lh;     // 可视视口
    const top = vv ? Math.round(vv.offsetTop || 0) : 0;
    const covered = lh - vh;
    const overlay = lh > 0 && vh >= 80 && covered >= 60;
    if (!overlay) {
      // 交回 CSS：清掉 JS 写过的值，刷新那一下永远落在这条分支
      if (applied !== 'css') {
        applied = 'css';
        root.style.removeProperty('--app-h');
        root.style.removeProperty('--vv-top');
        if (document.body.classList.contains('chat-open')) scrollBottom(true);
        checkLayout();
      }
      diag('sync-css', { lh, vh, covered });
      return;
    }
    const key = vh + ':' + top;
    if (key === applied) return;
    applied = key;
    root.style.setProperty('--app-h', vh + 'px');
    root.style.setProperty('--vv-top', top + 'px');
    if (document.body.classList.contains('chat-open')) scrollBottom(true);
    checkLayout();
    diag('sync-kb', { lh, vh, top, covered });
  };
  // 布局对不对，只有落在「看得见那块矩形」里才算对
  function checkLayout() {
    const app = document.querySelector('.app');
    if (!app) return;
    const r = app.getBoundingClientRect();
    const vh = Math.round((vv ? vv.height : window.innerHeight) || 0);
    const top = Math.round(vv ? vv.offsetTop || 0 : 0);
    const comp = document.body.classList.contains('chat-open') ? document.querySelector('.composer') : null;
    const cr = comp && comp.getBoundingClientRect();
    const off = Math.abs(r.top - top) > 3 || Math.abs(r.bottom - (top + vh)) > 3;
    const cut = cr && cr.height > 0 && (cr.bottom > top + vh + 3 || cr.top < top - 3);
    if (off || cut) {
      diag('bad', {
        ah: Math.round(r.height), at: Math.round(r.top), ab: Math.round(r.bottom),
        vh, top, cb: cr ? Math.round(cr.bottom) : 0
      });
    }
  }
  // 输入框上限按「4 行」算，跟视口高度脱钩：矮屏上也不会被压成一条缝
  function taCap() {
    const ta = $('#input');
    if (!ta) return;
    const cs = getComputedStyle(ta);
    const fs = parseFloat(cs.fontSize) || 15;
    const lh = parseFloat(cs.lineHeight) || Math.round(fs * 1.4);
    const pad = (parseFloat(cs.paddingTop) || 0) + (parseFloat(cs.paddingBottom) || 0);
    const cap = Math.round(lh * 4 + pad + 2);
    root.style.setProperty('--ta-max', cap + 'px');
    if (ta.value) autoGrow(ta);
  }
  taCap();
  if (vv) {
    vv.addEventListener('resize', window.syncViewport);
    vv.addEventListener('scroll', window.syncViewport);
  }
  window.addEventListener('resize', window.syncViewport);
  window.addEventListener('orientationchange', () => setTimeout(() => { taCap(); window.syncViewport(); }, 280));
  window.syncViewport();
  // 老内核偶尔吞事件：低频对一次表，值没变就不写，不会闪
  setInterval(() => { if (!document.hidden) window.syncViewport(); }, 800);

  window.addEventListener('error', (e) => diag('err', {
    msg: String(e.message || '').slice(0, 160),
    ln: e.lineno,
  }));
  window.addEventListener('unhandledrejection', (e) => diag('rej', {
    msg: String((e.reason && e.reason.message) || e.reason || '').slice(0, 160),
  }));
  document.addEventListener('visibilitychange', () => {
    diag('vis', { s: document.visibilityState });
    if (document.visibilityState === 'hidden') diagFlush(true);
  });
  window.addEventListener('pagehide', () => { diag('hide'); diagFlush(true); });
  setTimeout(() => diag('boot', {
    ua: navigator.userAgent,
    dpr: window.devicePixelRatio,
    scr: [screen.width, screen.height],
    sa: navigator.standalone ? 1 : 0,
  }), 60);
  setTimeout(() => diag('t1'), 1200);
  setTimeout(() => diag('t3'), 3200);

  const inputEl = $('#input');
  if (inputEl) {
    let composing = false;
    const grow = () => {
      // 输入法正在组词时别碰高度：改样式会让安卓 IME 丢组合串，拼音就「打不出来」了
      if (composing) return;
      autoGrow(inputEl);
    };
    inputEl.addEventListener('compositionstart', () => { composing = true; diag('comp-start'); });
    inputEl.addEventListener('compositionend', () => {
      composing = false;
      diag('comp-end');
      setTimeout(grow, 0);
    });
    inputEl.addEventListener('input', () => {
      diag('input');
      grow();
      sendTyping(!!inputEl.value.trim());
      if (S.cur && S.cur.kind === 'group' && /(^|\s)@$/.test(inputEl.value)) openAtPop();
      else closeAtPop();
    });
    inputEl.addEventListener('focus', () => {
      diag('focus');
      closeTray();
      taCap();
      // 键盘动画结束前 vv 是中间值，补几次校正
      [120, 320, 600].forEach((d) => setTimeout(() => window.syncViewport && window.syncViewport(), d));
    });
    inputEl.addEventListener('blur', () => {
      diag('blur');
      setTimeout(() => window.syncViewport && window.syncViewport(), 280);
    });
  }
  const stInput = $('#st-file');
  if (stInput) stInput.addEventListener('change', onStickerPicked);
  const msgsBox = $('#msgs');
  if (msgsBox) {
    msgsBox.addEventListener('scroll', () => {
      if (Date.now() - menuOpenedAt > 260) closeMsgMenu();
    }, { passive: true });
  }
  const imgInput = $('#img-file');
  if (imgInput) imgInput.addEventListener('change', onImagePicked);
  connectSSE();
  initPush().finally(() => {
    let tries = 0;
    const tick = () => {
      if (document.querySelector('.ann-bubble')) {
        if (++tries < 5) setTimeout(tick, 4000);
        return;
      }
      maybeAskPush();
    };
    setTimeout(tick, 1600);
  });
  setTimeout(popAnnouncement, 700);

  // 通知点进来会带 ?conv=<id>，直接打开那条会话
  const convParam = new URLSearchParams(location.search).get('conv');
  if (convParam && /^\d+$/.test(convParam)) {
    openConv(Number(convParam)).catch(() => {});
    try { history.replaceState(null, '', BASE + '/'); } catch (e) {}
  }
  if (window.innerWidth > 760) {
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
        "cover": (user["cover"] if "cover" in user.keys() else "") or "",
        "email": user["email"] or "",
        "role": user["role"],
        "is_admin": user["role"] == "admin",
        "is_sub": int(user["is_sub"] or 0),
    }
    js = "const ME=" + j(me) + ";\n" + APP_JS + "\n"
    body = APP_BODY.replace("__BASE__", base or "")
    return _doc("心夏通讯", body, extra_js=js, base=base)


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
.mini.danger{color:var(--danger);border-color:#eec4b8;background:#fdf3ee}
.mini.ok{color:var(--brand-d);border-color:#c8ebd6;background:#f8f2e6}
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
    <input id="nu-pass" type="password" placeholder="密码，至少 6 位">
    <input id="nu-email" type="email" placeholder="邮箱，可留空">
    <select id="nu-role" style="padding:10px 12px;border:1px solid #eadfcc;border-radius:9px;background:#fbf7ef">
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
    return _doc("管理后台 · 心夏通讯", body, extra_css=ADMIN_CSS, extra_js=js, base=base)
