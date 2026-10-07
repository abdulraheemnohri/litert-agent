// LiteRT Agent Web UI client
const page = document.getElementById('main').dataset.page;
const content = document.getElementById('content');

async function api(path) {
  const res = await fetch(path);
  if (!res.ok) throw new Error('API ' + res.status);
  return res.json();
}

function esc(s) {
  return String(s ?? '').replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
}

function badge(status) {
  const cls = {COMPLETED:'ok', PASS:'ok', PENDING:'info', RUNNING:'info', FAILED:'danger', BLOCK:'danger', ASK:'warn'}[status] || 'info';
  return '<span class="badge ' + cls + '">' + esc(status) + '</span>';
}

function card(title, body) {
  return '<div class="card"><h3>' + esc(title) + '</h3>' + body + '</div>';
}
function emptyState(msg) {
  return '<div class="card"><div class="loading">' + esc(msg) + '</div></div>';
}

function sendChat() {
  const input = document.getElementById('chat-input');
  const msg = input.value.trim();
  if (!msg) return;
  const box = document.getElementById('chat-box');
  box.insertAdjacentHTML('beforeend', '<div class="msg user"><b>You:</b> ' + esc(msg) + '</div>');
  input.value = '';
  box.insertAdjacentHTML('beforeend', '<div class="msg agent"><b>Agent:</b> <span class="loading">working…</span></div>');
  box.scrollTop = box.scrollHeight;
  fetch('/api/chat', {method: 'POST', headers: {'Content-Type': 'application/json'}, body: JSON.stringify({message: msg})})
    .then(r => r.json())
    .then(data => {
      box.lastElementChild.innerHTML = '<b>Agent:</b> ' + esc(data.reply);
      box.scrollTop = box.scrollHeight;
    })
    .catch(e => {
      box.lastElementChild.innerHTML = '<b>Agent:</b> <span class="error-text">Error: ' + esc(e.message) + '</span>';
    });
}

const renderers = {
  dashboard: async () => {
    const [status, health] = await Promise.all([api('/api/status'), api('/api/health')]);
    const r = health.resources;
    return '<div class="grid">' +
      card('Agent', '<div class="metric">' + esc(status.started ? 'RUNNING' : 'IDLE') + '</div><small>autonomy level ' + status.autonomy_level + '</small>') +
      card('Model (LiteRT-LM)', '<div class="metric">' + (health.model && health.model.checks && health.model.checks.model === 'READY' ? 'Ready' : 'Not detected') + '</div>') +
      card('CPU', '<div class="metric">' + r.cpu_percent + '%</div>') +
      card('Memory', '<div class="metric">' + r.memory.available_gb + ' GB<small> free of ' + r.memory.total_gb + ' GB</small></div>') +
      card('Disk', '<div class="metric">' + r.disk.free_gb + ' GB<small> free</small></div>') +
      '</div>' +
      card('Live Events', '<div id="events"><div class="loading">waiting for events…</div></div>');
  },
  chat: async () => {
    return card('Chat', '<div id="chat-box" style="height:300px;overflow:auto;border:1px solid var(--border);border-radius:8px;padding:10px;margin-bottom:10px;background:var(--panel2)"></div>' +
      '<div style="display:flex;gap:8px"><input id="chat-input" placeholder="Ask the agent..." style="flex:1;padding:10px;border-radius:8px;border:1px solid var(--border);background:var(--panel2);color:var(--text)" onkeydown="if(event.key===\'Enter\')sendChat()"><button onclick="sendChat()">Send</button></div>');
  },
  agent: async () => {
    const [status, health] = await Promise.all([api('/api/status'), api('/api/health')]);
    return card('Agent', '<table>' +
      '<tr><td>Name</td><td>' + esc(status.agent) + '</td></tr>' +
      '<tr><td>State</td><td>' + esc(status.started ? 'RUNNING' : 'IDLE') + '</td></tr>' +
      '<tr><td>Autonomy</td><td>level ' + status.autonomy_level + '</td></tr>' +
      '<tr><td>Safe mode</td><td>' + esc(status.safe_mode) + '</td></tr>' +
      '<tr><td>Offline</td><td>' + esc(status.offline_mode) + '</td></tr>' +
      '<tr><td>Model</td><td>' + esc(status.model_provider) + ' (LiteRT-LM only)</td></tr>' +
      '<tr><td>Health</td><td>' + esc((health.model && health.model.status) || 'UNKNOWN') + '</td></tr>' +
      '</table>');
  },
  tasks: async () => {
    const data = await api('/api/tasks');
    if (!data.tasks.length) return emptyState('No tasks yet.');
    let rows = data.tasks.map(t => '<tr><td>' + esc(t.id.slice(0,8)) + '</td><td>' + esc(t.description) + '</td><td>' + badge(t.status) + '</td><td>' + esc(t.created_at) + '</td></tr>').join('');
    return card('Tasks', '<table><tr><th>ID</th><th>Goal</th><th>Status</th><th>Created</th></tr>' + rows + '</table>');
  },
  memory: async () => {
    const data = await api('/api/memory');
    if (!data.memories.length) return emptyState('No memories recorded yet.');
    let rows = data.memories.map(m => '<tr><td>' + esc(m.category) + '</td><td>' + esc(m.content) + '</td><td>' + esc(m.importance) + '</td><td>' + esc(m.created_at) + '</td></tr>').join('');
    return card('Memory', '<table><tr><th>Category</th><th>Content</th><th>Importance</th><th>Created</th></tr>' + rows + '</table>');
  },
  skills: async () => {
    const data = await api('/api/skills');
    return '<div class="grid">' + data.skills.map(s =>
      card(s.name, esc(s.description) + '<br><small>tools: ' + esc((s.tools || []).join(', ')) + ' · v' + esc(s.version) + '</small><br>' + (s.enabled ? badge('COMPLETED').replace('COMPLETED','enabled') : badge('FAILED').replace('FAILED','disabled')))
    ).join('') + '</div>';
  },
  tools: async () => {
    const data = await api('/api/tools');
    let rows = data.tools.map(t => '<tr><td>' + esc(t.name) + '</td><td>' + esc(t.description) + '</td><td>' + badge(t.permission_level) + '</td></tr>').join('');
    return card('Tools', '<table><tr><th>Tool</th><th>Description</th><th>Permission</th></tr>' + rows + '</table>');
  },
  approvals: async () => {
    const data = await api('/api/approvals');
    if (!data.approvals.length) return emptyState('No pending approvals.');
    return data.approvals.map(a => card('Approval ' + esc(a.id.slice(0,8)), esc(a.tool) + '.' + esc(a.action) + ' ' + badge(a.status || 'ASK')));
  },
  checkpoints: async () => {
    const data = await api('/api/checkpoints');
    if (!data.checkpoints.length) return emptyState('No checkpoints yet.');
    let rows = data.checkpoints.map(c => '<tr><td>' + esc(c.id.slice(0,8)) + '</td><td>' + esc(c.description) + '</td><td>' + esc(c.created_at) + '</td></tr>').join('');
    return card('Checkpoints', '<table><tr><th>ID</th><th>Description</th><th>Created</th></tr>' + rows + '</table>');
  },
  logs: async () => {
    const data = await api('/api/logs');
    if (!data.logs.length) return emptyState('No logs recorded yet.');
    return card('Logs', data.logs.map(l => '<div class="log-line">[' + esc(l.created_at) + '] ' + esc(l.type) + ' — ' + esc(l.payload) + '</div>').join(''));
  },
  system: async () => {
    const data = await api('/api/system');
    const c = data.capabilities, r = data.resources;
    let rows = [
      ['OS', c.os], ['Python', c.python_version], ['Git', c.has_git ? 'installed' : 'missing'],
      ['LiteRT-LM CLI', c.has_litert_lm ? 'installed' : 'missing'], ['Playwright', c.has_playwright ? 'installed' : 'missing'],
      ['CPU', r.cpu_percent + '%'], ['RAM', r.memory.used_percent + '% used'],
      ['Disk', r.disk.used_percent + '% used'],
    ].map(x => '<tr><td>' + esc(x[0]) + '</td><td>' + esc(x[1]) + '</td></tr>').join('');
    return card('System', '<table>' + rows + '</table>');
  },
  settings: async () => {
    const data = await api('/api/settings');
    return card('Configuration', '<pre style="font-size:12px;white-space:pre-wrap">' + esc(JSON.stringify(data.config, null, 2)) + '</pre>');
  },
};

(async () => {
  try {
    content.innerHTML = await (renderers[page] || (async () => emptyState('Unknown page')))();
  } catch (e) {
    content.innerHTML = emptyState('Error: ' + e.message);
  }
  const proto = location.protocol === 'https:' ? 'wss' : 'ws';
  const ws = new WebSocket(proto + '://' + location.host + '/ws/events');
  ws.onopen = () => { document.getElementById('conn-dot').classList.add('on'); document.getElementById('conn-text').textContent = 'agent connected'; };
  ws.onclose = () => { document.getElementById('conn-dot').classList.remove('on'); document.getElementById('conn-text').textContent = 'disconnected'; };
  ws.onmessage = (ev) => {
    const box = document.getElementById('events');
    if (box) {
      if (box.querySelector('.loading')) box.innerHTML = '';
      const line = document.createElement('div');
      line.className = 'log-line';
      line.textContent = ev.data;
      box.prepend(line);
    }
  };
})();
