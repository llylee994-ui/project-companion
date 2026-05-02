# -*- coding: utf-8 -*-
"""Web dashboard HTML for AI Coding Sentinel. Access at http://127.0.0.1:9599/"""

DASHBOARD_HTML = r"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>AI Coding Sentinel</title>
<style>
:root{--bg:#0d1117;--card:#161b22;--border:#30363d;--text:#c9d1d9;--muted:#8b949e;--accent:#58a6ff;--perm:#f0883e;--done:#3fb950;--err:#f85149}
*{box-sizing:border-box;margin:0;padding:0}
body{background:var(--bg);color:var(--text);font:14px/1.6 -apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif;max-width:1024px;margin:0 auto;padding:24px 20px}
h1{font-size:20px;font-weight:600}
h1 .dot{display:inline-block;width:8px;height:8px;border-radius:50%;margin-right:8px}
h1 .dot.on{background:var(--done);box-shadow:0 0 6px var(--done)}
h1 .dot.off{background:var(--err)}
.sub{color:var(--muted);font-size:12px;margin:4px 0 20px}
.tabs{display:flex;gap:0;margin-bottom:20px;border-bottom:1px solid var(--border)}
.tabs button{padding:8px 16px;background:0;border:0;color:var(--muted);cursor:pointer;font-size:13px;border-bottom:2px solid transparent;transition:.2s}
.tabs button:hover{color:var(--text)}
.tabs button.on{color:var(--text);border-bottom-color:var(--accent)}
.card{background:var(--card);border:1px solid var(--border);border-radius:8px;padding:16px;margin-bottom:16px}
.card h2{font-size:13px;font-weight:600;color:var(--muted);text-transform:uppercase;letter-spacing:.5px;margin-bottom:12px}
.kv{display:flex;gap:24px;flex-wrap:wrap}
.kv-item{min-width:100px}
.kv-val{font-size:22px;font-weight:600}
.kv-lbl{font-size:11px;color:var(--muted);margin-top:2px}
.tag{padding:1px 8px;border-radius:10px;font-size:11px}
.tag.perm{background:#3c1f0a;color:var(--perm)}
.tag.done{background:#0d3320;color:var(--done)}
.tag.info{background:#1c2128;color:var(--muted)}
.sessions{margin-top:8px}
.sess{display:flex;justify-content:space-between;align-items:center;padding:6px 0;border-bottom:1px solid rgba(48,54,61,.3)}
.sess:last-child{border-bottom:0}
.logs{font:12px/1.5 'Cascadia Code','Consolas',monospace;max-height:400px;overflow-y:auto;background:#0d1117;border-radius:6px;padding:10px}
.logs::-webkit-scrollbar{width:6px}
.logs::-webkit-scrollbar-thumb{background:var(--border);border-radius:3px}
.log-line{padding:2px 0;border-bottom:1px solid rgba(48,54,61,.2)}
.log-time{color:var(--muted);margin-right:10px}
.log-text.perm{color:var(--perm)}
.log-text.done{color:var(--done)}
.log-text.info{color:var(--muted)}
.log-text.err{color:var(--err)}
textarea{width:100%;min-height:220px;background:#0d1117;color:var(--text);border:1px solid var(--border);border-radius:6px;padding:12px;font:13px/1.5 'Cascadia Code','Consolas',monospace;resize:vertical}
textarea:focus{outline:none;border-color:var(--accent)}
.btn-row{display:flex;gap:8px;margin-top:12px}
button{padding:6px 16px;border-radius:6px;font-size:12px;cursor:pointer;font-weight:500}
.btn-go{background:var(--accent);color:#fff;border:1px solid var(--accent)}
.btn-go:hover{opacity:.9}
.btn-ghost{background:0;color:var(--text);border:1px solid var(--border)}
.btn-ghost:hover{background:#21262d}
.msg{font-size:12px;margin-top:8px;min-height:18px}
.msg.ok{color:var(--done)}
.msg.err{color:var(--err)}
.hidden{display:none}
</style>
</head>
<body>

<h1><span class="dot on" id="dot"></span>AI Coding Sentinel <span style="font-size:14px;color:var(--muted);font-weight:400" id="ver"></span></h1>
<p class="sub">Claude Code 监控 &middot; 飞书/微信通知 &middot; 实时日志 &middot; <a href="http://127.0.0.1:9599/health" style="color:var(--accent)" target=_blank>健康检查</a></p>

<div class="tabs">
  <button class="on" data-tab="status">仪表盘</button>
  <button data-tab="logs">日志</button>
  <button data-tab="config">配置</button>
</div>

<!-- Status -->
<div id="tab-status">
  <div class="card">
    <div class="kv">
      <div class="kv-item"><div class="kv-val" id="sessNum">-</div><div class="kv-lbl">活跃会话</div></div>
      <div class="kv-item"><div class="kv-val">:9599</div><div class="kv-lbl">本地端口</div></div>
      <div class="kv-item"><div class="kv-val" id="connStatus">--</div><div class="kv-lbl">连接状态</div></div>
    </div>
  </div>
  <div class="card">
    <h2>会话详情</h2>
    <div class="sessions" id="sessions">加载中...</div>
  </div>
</div>

<!-- Logs -->
<div id="tab-logs" class="hidden">
  <div class="card">
    <h2>实时日志 (每 3s 刷新)</h2>
    <div class="logs" id="logBox"></div>
  </div>
</div>

<!-- Config -->
<div id="tab-config" class="hidden">
  <div class="card">
    <h2>编辑 config.yaml</h2>
    <textarea id="confEditor" spellcheck="false"></textarea>
    <div class="btn-row">
      <button class="btn-go" id="saveBtn">保存</button>
      <button class="btn-ghost" id="loadBtn">重新加载</button>
    </div>
    <div class="msg" id="confMsg"></div>
  </div>
</div>

<script>
const API='http://127.0.0.1:9599';

// Tabs
document.querySelectorAll('.tabs button').forEach(b=>{
  b.onclick=()=>{
    document.querySelectorAll('.tabs button').forEach(x=>x.className='');
    b.className='on';
    ['status','logs','config'].forEach(t=>document.getElementById('tab-'+t).classList.add('hidden'));
    document.getElementById('tab-'+b.dataset.tab).classList.remove('hidden');
    if(b.dataset.tab==='logs') loadLogs();
    if(b.dataset.tab==='config') loadConfig();
  };
});

async function poll(){
  try{
    let r=await fetch(API+'/api/status');
    let d=await r.json();
    document.getElementById('dot').className='dot on';
    document.getElementById('ver').textContent='v'+(d.version||'3.0');
    document.getElementById('sessNum').textContent=d.sessions.length;
    document.getElementById('connStatus').textContent=d.status;
    let s=document.getElementById('sessions');
    if(!d.sessions.length)s.innerHTML='<div class="sess"><span style="color:var(--muted)">暂无活跃会话</span></div>';
    else s.innerHTML=d.sessions.map(x=>`<div class="sess"><span>${x.name}</span><span class="tag ${x.state==='waiting_user'?'perm':x.state==='done'?'done':'info'}">${x.state}</span></div>`).join('');
  }catch(e){
    document.getElementById('dot').className='dot off';
    document.getElementById('connStatus').textContent='离线';
  }
}

async function loadLogs(){
  try{let r=await fetch(API+'/api/logs');let d=await r.json();
    let el=document.getElementById('logBox');
    el.innerHTML=d.lines.length?d.lines.map(l=>`<div class="log-line"><span class="log-time">${l.time}</span><span class="log-text ${l.cls}">${l.text}</span></div>`).join(''):'<div class="log-line"><span class="log-text info">等待事件...</span></div>';
    el.scrollTop=el.scrollHeight;
  }catch(e){}
}

async function loadConfig(){
  try{let r=await fetch(API+'/api/config');let d=await r.json();document.getElementById('confEditor').value=d.yaml||'';}catch(e){}
}

document.getElementById('saveBtn').onclick=async()=>{
  let y=document.getElementById('confEditor').value;let m=document.getElementById('confMsg');
  try{let r=await fetch(API+'/api/config',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({yaml:y})});let d=await r.json();
    if(d.ok){m.className='msg ok';m.textContent='已保存 (重启 daemon 生效)';}else{m.className='msg err';m.textContent='错误: '+d.error;}
  }catch(e){m.className='msg err';m.textContent='保存失败';}
};
document.getElementById('loadBtn').onclick=loadConfig;

poll();setInterval(poll,3000);
loadConfig();
</script>
</body>
</html>"""
