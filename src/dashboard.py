# -*- coding: utf-8 -*-
"""
Web dashboard for AI Coding Companion.
Self-contained HTML page served at http://127.0.0.1:9599/
"""

DASHBOARD_HTML = r"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>AI Coding Companion</title>
<style>
*{margin:0;padding:0;box-sizing:border-box}
body{font-family:'Segoe UI',system-ui,sans-serif;background:#0f1117;color:#e1e4e8;min-height:100vh}
.header{background:#161b22;border-bottom:1px solid #30363d;padding:16px 24px;display:flex;align-items:center;gap:12px}
.header h1{font-size:18px;font-weight:600}
.dot{width:10px;height:10px;border-radius:50%;display:inline-block}
.dot.on{background:#3fb950;box-shadow:0 0 6px #3fb950}
.dot.off{background:#f85149}
.nav{background:#161b22;border-bottom:1px solid #30363d;padding:0 24px;display:flex;gap:0}
.nav button{padding:10px 16px;background:0;border:0;color:#8b949e;cursor:pointer;font-size:14px;border-bottom:2px solid transparent;transition:all .2s}
.nav button:hover{color:#e1e4e8}
.nav button.active{color:#e1e4e8;border-bottom-color:#58a6ff}
.main{padding:24px;max-width:900px;margin:0 auto}
.card{background:#161b22;border:1px solid #30363d;border-radius:8px;padding:20px;margin-bottom:16px}
.card h2{font-size:15px;margin-bottom:12px;color:#8b949e;text-transform:uppercase;letter-spacing:.5px}
.row{display:flex;gap:12px;align-items:center;margin-bottom:8px}
.tag{padding:2px 8px;border-radius:12px;font-size:12px;font-weight:500}
.tag.work{background:#1a3a2a;color:#3fb950}
.tag.wait{background:#3a2a1a;color:#d29922}
.tag.done{background:#1a2a3a;color:#58a6ff}
.tag.idle{background:#2a2a2a;color:#8b949e}
.logs{font-family:'Cascadia Code','Fira Code',monospace;font-size:12px;line-height:1.6;max-height:400px;overflow-y:auto;background:#0d1117;border-radius:6px;padding:12px}
.logs .line{margin-bottom:2px}
.logs .time{color:#484f58;margin-right:8px}
.logs .perm{color:#d29922}
.logs .done{color:#3fb950}
.logs .info{color:#58a6ff}
.logs .err{color:#f85149}
textarea{width:100%;min-height:200px;background:#0d1117;color:#e1e4e8;border:1px solid #30363d;border-radius:6px;padding:12px;font-family:monospace;font-size:13px;resize:vertical}
input{background:#0d1117;color:#e1e4e8;border:1px solid #30363d;border-radius:6px;padding:8px 12px;font-size:13px;width:100%}
.btn{padding:8px 16px;border-radius:6px;border:0;cursor:pointer;font-size:13px;font-weight:500;transition:all .2s}
.btn.primary{background:#238636;color:#fff}
.btn.primary:hover{background:#2ea043}
.btn.danger{background:#da3633;color:#fff}
.btn.danger:hover{background:#f85149}
.btn.outline{background:0;border:1px solid #30363d;color:#8b949e}
.btn.outline:hover{color:#e1e4e8;border-color:#8b949e}
.flex{display:flex;gap:8px;align-items:center}
.grid2{display:grid;grid-template-columns:1fr 1fr;gap:16px}
.label{font-size:12px;color:#8b949e;margin-bottom:4px}
.value{font-size:20px;font-weight:600}
.hidden{display:none}
.toast{position:fixed;bottom:24px;right:24px;padding:12px 20px;border-radius:8px;font-size:14px;animation:slideIn .3s ease;z-index:999}
.toast.ok{background:#238636;color:#fff}
.toast.err{background:#da3633;color:#fff}
@keyframes slideIn{from{transform:translateY(20px);opacity:0}to{transform:translateY(0);opacity:1}}
@media(max-width:600px){.grid2{grid-template-columns:1fr}.main{padding:12px}}
</style>
</head>
<body>

<div class="header">
  <span class="dot on" id="statusDot"></span>
  <h1>AI Coding Companion</h1>
  <span style="font-size:13px;color:#8b949e" id="versionTag">v3.0</span>
  <span class="flex" style="margin-left:auto;gap:8px">
    <span style="font-size:12px;color:#484f58" id="clock"></span>
  </span>
</div>

<div class="nav">
  <button class="active" data-page="dashboard">仪表盘</button>
  <button data-page="config">配置</button>
  <button data-page="logs">日志</button>
</div>

<div class="main">

  <!-- Dashboard -->
  <div id="page-dashboard">
    <div class="grid2">
      <div class="card">
        <h2>状态</h2>
        <div class="value" id="sessCount">-</div>
        <div class="label">活跃会话</div>
      </div>
      <div class="card">
        <h2>端口</h2>
        <div class="value">9599</div>
        <div class="label">本地监听</div>
      </div>
    </div>
    <div class="card">
      <h2>会话详情</h2>
      <div id="sessionList">加载中...</div>
    </div>
  </div>

  <!-- Config -->
  <div id="page-config" class="hidden">
    <div class="card">
      <h2>编辑配置</h2>
      <textarea id="configEditor" spellcheck="false"></textarea>
      <div class="flex" style="margin-top:12px">
        <button class="btn primary" id="btnSaveConfig">保存配置</button>
        <button class="btn outline" id="btnReloadConfig">重新加载</button>
        <span id="configMsg" style="font-size:12px;color:#8b949e"></span>
      </div>
    </div>
  </div>

  <!-- Logs -->
  <div id="page-logs" class="hidden">
    <div class="card">
      <h2>实时日志</h2>
      <div class="logs" id="logContainer">加载中...</div>
    </div>
  </div>

</div>

<script>
const POLL_MS = 3000;
let currentPage = 'dashboard';

// Navigation
document.querySelectorAll('.nav button').forEach(btn => {
  btn.addEventListener('click', () => {
    document.querySelectorAll('.nav button').forEach(b => b.classList.remove('active'));
    btn.classList.add('active');
    currentPage = btn.dataset.page;
    document.querySelectorAll('[id^="page-"]').forEach(p => p.classList.add('hidden'));
    document.getElementById('page-' + currentPage).classList.remove('hidden');
    if (currentPage === 'config') loadConfig();
    if (currentPage === 'logs') loadLogs();
  });
});

// Clock
setInterval(() => {
  document.getElementById('clock').textContent = new Date().toLocaleTimeString('zh-CN');
}, 1000);

// Poll status
async function poll() {
  try {
    const r = await fetch('/api/status');
    const d = await r.json();
    document.getElementById('statusDot').className = 'dot ' + (d.status === 'running' ? 'on' : 'off');
    document.getElementById('sessCount').textContent = d.sessions.length;
    const list = document.getElementById('sessionList');
    if (!d.sessions.length) {
      list.innerHTML = '<span style="color:#484f58">暂无活跃会话</span>';
    } else {
      list.innerHTML = d.sessions.map(s => {
        const cls = {working:'work',waiting_user:'wait',done:'done'}[s.state] || 'idle';
        return `<div class="row"><span class="tag ${cls}">${s.state}</span><span>${s.name}</span><span style="color:#484f58;font-size:12px">${s.duration}</span></div>`;
      }).join('');
    }
    document.getElementById('versionTag').textContent = d.version || 'v3.0';
  } catch(e) {
    document.getElementById('statusDot').className = 'dot off';
    document.getElementById('sessCount').textContent = '离线';
  }
}

// Load config
async function loadConfig() {
  try {
    const r = await fetch('/api/config');
    const d = await r.json();
    document.getElementById('configEditor').value = d.yaml || '';
  } catch(e) {
    document.getElementById('configEditor').value = '# 加载失败';
  }
}

// Save config
document.getElementById('btnSaveConfig').addEventListener('click', async () => {
  const yaml = document.getElementById('configEditor').value;
  try {
    const r = await fetch('/api/config', {
      method: 'POST',
      headers: {'Content-Type': 'application/json'},
      body: JSON.stringify({yaml})
    });
    const d = await r.json();
    const msg = document.getElementById('configMsg');
    msg.textContent = d.ok ? '✓ 已保存' : '✗ ' + (d.error || '保存失败');
    msg.style.color = d.ok ? '#3fb950' : '#f85149';
    if (d.ok) setTimeout(() => msg.textContent = '', 3000);
  } catch(e) {
    const msg = document.getElementById('configMsg');
    msg.textContent = '✗ 保存失败';
    msg.style.color = '#f85149';
  }
});

document.getElementById('btnReloadConfig').addEventListener('click', loadConfig);

// Load logs
async function loadLogs() {
  try {
    const r = await fetch('/api/logs');
    const d = await r.json();
    const container = document.getElementById('logContainer');
    container.innerHTML = d.lines.map(l =>
      `<div class="line"><span class="time">${l.time}</span><span class="${l.cls}">${l.text}</span></div>`
    ).join('');
    container.scrollTop = container.scrollHeight;
  } catch(e) {
    document.getElementById('logContainer').innerHTML = '<span style="color:#f85149">加载失败</span>';
  }
}

// Initial load
poll();
setInterval(poll, POLL_MS);
</script>
</body>
</html>"""
