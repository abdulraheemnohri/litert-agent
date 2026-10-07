// LiteRT Agent Web UI client — renders every page against the local agent API.
const page = document.getElementById('main').dataset.page;
const content = document.getElementById('content');

async function api(path, options) {
  const res = await fetch(path, options);
  if (!res.ok) throw new Error('API ' + res.status);
  return res.json();
}

async function post(path, body) {
  return api(path, {
    method: 'POST',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify(body || {}),
  });
}

function esc(s) {
  return String(s ?? '').replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
}

function badge(status) {
  const cls = {COMPLETED:'ok', PASS:'ok', READY:'ok', RUNNING:'info', PENDING:'info',
               IDLE:'info', FAILED:'danger', BLOCK:'danger', DENIED:'danger', ASK:'warn'}[status] || 'info';
  return '<span class="badge ' + cls + '">' + esc(status) + '</span>';
}

function card(title, body) {
  return '<div class="card"><h3>' + esc(title) + '</h3>' + body + '</div>';
}

function emptyState(msg) {
  return '<div class="card"><div class="loading">' + esc(msg) + '</div></div>';
}

function table(headers, rows) {
  return '<table><tr>' + headers.map(h => '<th>' + esc(h) + '</th>').join('') + '</tr>' +
    rows.map(r => '<tr>' + r.map(c => '<td>' + c + '</td>').join('') + '</tr>').join('') + '</table>';
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
  post('/api/chat', {message: msg})
    .then(data => {
      box.lastElementChild.innerHTML = '<b>Agent:</b> ' + esc(data.reply);
      box.scrollTop = box.scrollHeight;
    })
    .catch(e => {
      box.lastElementChild.innerHTML = '<b>Agent:</b> <span class="error-text">Error: ' + esc(e.message) + '</span>';
      box.scrollTop = box.scrollHeight;
    });
}

function createTask(ev) {
  ev.preventDefault();
  const goal = document.getElementById('task-goal').value.trim();
  if (!goal) return;
  post('/api/tasks', {goal: goal})
    .then(() => { location.reload(); })
    .catch(e => alert('Error: ' + e.message));
}

function addJob(ev) {
  ev.preventDefault();
  const name = document.getElementById('job-name').value.trim();
  const desc = document.getElementById('job-desc').value.trim();
  if (!name || !desc) return;
  post('/api/scheduler', {name: name, task_description: desc})
    .then(() => { location.reload(); })
    .catch(e => alert('Error: ' + e.message));
}

function runJob(jobId) {
  post('/api/scheduler/' + jobId + '/run')
    .then(() => alert('Job queued for execution.'))
    .catch(e => alert('Error: ' + e.message));
}

function restoreCheckpoint(cpId) {
  post('/api/checkpoints/' + cpId + '/restore')
    .then(r => alert(r.restored ? 'Checkpoint restored.' : 'Checkpoint not found.'))
    .catch(e => alert('Error: ' + e.message));
}

function decideApproval(approvalId, decision) {
  post('/api/approvals/' + approvalId + '/approve', {decision: decision})
    .then(r => {
      if (r && r.error) { alert('Error: ' + r.error); return; }
      location.reload();
    })
    .catch(e => alert('Error: ' + e.message));
}

function runDiagnostics() {
  const box = document.getElementById('diag-box');
  box.innerHTML = '<div class="loading">Running diagnostics…</div>';
  api('/api/diagnostics')
    .then(data => {
      const rows = Object.entries(data.checks).map(([k, v]) => [esc(k), badge(String(v).startsWith('PASS') ? 'PASS' : String(v)) + ' <small>' + esc(v) + '</small>']);
      box.innerHTML = card('Diagnostics', table(['Check', 'Result'], rows));
    })
    .catch(e => { box.innerHTML = emptyState('Error: ' + e.message); });
}

const renderers = {
  dashboard: async () => {
    const [status, health] = await Promise.all([api('/api/status'), api('/api/health')]);
    const r = health.resources;
    return '<div class="grid">' +
      card('Agent', '<div class="metric">' + esc(status.started ? 'RUNNING' : 'IDLE') + '</div><small>autonomy level ' + esc(status.autonomy_level) + '</small>') +
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
    return card('Agent', table(['Property', 'Value'], [
      ['Name', esc(status.agent)],
      ['State', badge(status.started ? 'RUNNING' : 'IDLE')],
      ['Autonomy level', esc(status.autonomy_level)],
      ['Safe mode', esc(status.safe_mode)],
      ['Offline mode', esc(status.offline_mode)],
      ['Model provider', esc(status.model_provider) + ' (LiteRT-LM only)'],
      ['Queue size', esc(status.queue_size)],
      ['Health', esc((health.model && health.model.status) || 'UNKNOWN')],
    ]));
  },
  tasks: async () => {
    const data = await api('/api/tasks');
    const form = card('New Task', '<form onsubmit="createTask(event)"><div style="display:flex;gap:8px">' +
      '<input id="task-goal" placeholder="Describe the task for the agent..." style="flex:1;padding:10px;border-radius:8px;border:1px solid var(--border);background:var(--panel2);color:var(--text)">' +
      '<button type="submit">Create</button></div></form>');
    if (!data.tasks.length) return form + emptyState('No tasks yet.');
    const rows = data.tasks.map(t => [esc(t.id.slice(0, 8)), esc(t.description), badge(t.status), esc(t.created_at)]);
    return form + card('Tasks', table(['ID', 'Goal', 'Status', 'Created'], rows));
  },
  scheduler: async () => {
    const data = await api('/api/scheduler');
    const form = card('Add Job', '<form onsubmit="addJob(event)">' +
      '<input id="job-name" placeholder="Job name" style="width:100%;padding:10px;margin-bottom:8px;border-radius:8px;border:1px solid var(--border);background:var(--panel2);color:var(--text)">' +
      '<input id="job-desc" placeholder="Task description" style="width:100%;padding:10px;margin-bottom:8px;border-radius:8px;border:1px solid var(--border);background:var(--panel2);color:var(--text)">' +
      '<button type="submit">Add Job</button></form>');
    if (!data.jobs.length) return form + emptyState('No scheduled jobs yet.');
    const rows = data.jobs.map(j => [esc(j.id.slice(0, 8)), esc(j.name), esc(j.task_description), badge(j.status),
      '<button class="ghost" onclick="runJob(\'' + j.id + '\')">Run Now</button>']);
    return form + card('Jobs <small>queue: ' + data.queue_size + ' · worker: ' + (data.worker_running ? 'running' : 'idle') + '</small>',
      table(['ID', 'Name', 'Task', 'Status', ''], rows));
  },
  workers: async () => {
    const data = await api('/api/workers');
    return '<div class="grid">' + data.workers.map(w =>
      card(w.role, '<div class="metric">' + badge(w.status) + '</div>' +
        '<small>completed: ' + esc(w.completed_jobs) + ' · queue: ' + esc(w.queue_size) + '</small>')
    ).join('') + '</div>';
  },
  memory: async () => {
    const data = await api('/api/memory');
    if (!data.memories.length) return emptyState('No memories recorded yet.');
    const rows = data.memories.map(m => [esc(m.category), esc(m.content), esc(m.importance), esc(m.created_at)]);
    return card('Memory', table(['Category', 'Content', 'Importance', 'Created'], rows));
  },
  skills: async () => {
    const data = await api('/api/skills');
    return '<div class="grid">' + data.skills.map(s =>
      card(s.name, esc(s.description) + '<br><small>tools: ' + esc((s.tools || []).join(', ')) + ' · v' + esc(s.version) + '</small><br>' + badge(s.enabled ? 'COMPLETED' : 'PENDING'))
    ).join('') + '</div>';
  },
  tools: async () => {
    const data = await api('/api/tools');
    const rows = data.tools.map(t => [esc(t.name), esc(t.description), badge(t.permission_level)]);
    return card('Tools', table(['Tool', 'Description', 'Permission'], rows));
  },
  approvals: async () => {
    const data = await api('/api/approvals');
    const pending = data.approvals.map(a => card('Approval ' + esc(String(a.id).slice(0, 8)),
      '<p><b>' + esc(a.tool) + '.' + esc(a.action) + '</b> — ' + esc(a.reason) + '</p>' +
      '<p><small>risk: ' + esc(a.risk) + ' · status: ' + esc(a.status) + '</small></p>' +
      '<div style="display:flex;gap:8px">' +
      '<button onclick="decideApproval(\'' + a.id + '\', \'allow_once\')">Allow Once</button>' +
      '<button class="ghost" onclick="decideApproval(\'' + a.id + '\', \'allow\')">Allow Session</button>' +
      '<button class="danger" onclick="decideApproval(\'' + a.id + '\', \'deny\')">Deny</button>' +
      '</div>')).join('') || emptyState('No pending approvals.');
    const hist = data.history && data.history.length
      ? card('History', table(['ID', 'Tool', 'Decision', 'Decided'],
          data.history.map(h => [esc(String(h.id).slice(0, 8)), esc(h.tool + '.' + h.action), badge(h.status === 'DENY' ? 'DENIED' : 'COMPLETED'), esc(h.decided_at || '')])))
      : '';
    return pending + hist;
  },
  checkpoints: async () => {
    const data = await api('/api/checkpoints');
    if (!data.checkpoints.length) return emptyState('No checkpoints yet.');
    const rows = data.checkpoints.map(c => [esc(String(c.id).slice(0, 8)), esc(c.description || c.name || ''), esc(c.created_at),
      '<button class="ghost" onclick="restoreCheckpoint(\'' + c.id + '\')">Restore</button>']);
    return card('Checkpoints', table(['ID', 'Description', 'Created', ''], rows));
  },
  logs: async () => {
    const data = await api('/api/logs');
    if (!data.logs.length) return emptyState('No logs recorded yet.');
    return card('Logs', data.logs.map(l => '<div class="log-line">[' + esc(l.created_at) + '] ' + esc(l.type) + ' — ' + esc(l.payload) + '</div>').join(''));
  },
  system: async () => {
    const data = await api('/api/system');
    const c = data.capabilities, r = data.resources;
    const rows = [
      ['OS', c.os], ['Python', c.python_version], ['Git', c.has_git ? 'installed' : 'missing'],
      ['LiteRT-LM CLI', c.has_litert_lm ? 'installed' : 'missing'], ['Playwright', c.has_playwright ? 'installed' : 'missing'],
      ['CPU', r.cpu_percent + '%'], ['RAM', r.memory.used_percent + '% used'],
      ['Disk', r.disk.used_percent + '% used'],
    ].map(x => [esc(x[0]), esc(x[1])]);
    return card('System', table(['Component', 'Status / Value'], rows));
  },
  diagnostics: async () => {
    return card('Diagnostics', '<p>Run the built-in self-diagnostics: database, skills registry, model and runtime checks.</p>' +
      '<button onclick="runDiagnostics()">Run Diagnostics</button>') +
      '<div id="diag-box"></div>';
  },
  self: async () => {
    const data = await api('/api/self');
    const d = data.diagnostics || {};
    const rows = Object.entries(d.checks || {}).map(([k, v]) => [esc(k), badge(v ? 'PASS' : 'WARN')]);
    const maintenance = (data.maintenance || []).map(x => '<li><b>' + esc(x.action) + '</b> — ' + esc(x.reason) + '</li>').join('') || '<li>No maintenance proposals.</li>';
    return '<div class="grid">' +
      card('Identity', '<div class="metric">' + esc(data.identity.name) + '</div><small>' + esc(data.identity.mission) + '</small>') +
      card('Resources', '<div class="metric">' + esc(data.resources.memory_percent) + '% RAM</div><small>' + esc(data.resources.cpu_percent) + '% CPU · ' + esc(data.resources.disk_percent) + '% disk</small>') +
      card('Provider', '<div class="metric">LiteRT-LM CLI</div><small>No fallback backend</small>') +
      '</div>' + card('Diagnostics', table(['Check', 'Status'], rows)) +
      card('Bounded Maintenance', '<ul>' + maintenance + '</ul>');
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
  // websocket
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
