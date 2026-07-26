<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>AURA X · Command Center</title>
  <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700;800&family=JetBrains+Mono:wght@400;700&display=swap" rel="stylesheet">
  <style>
    * { margin: 0; padding: 0; box-sizing: border-box; }
    body {
      font-family: 'Inter', sans-serif;
      background: #0a0a12;
      color: #e8edf5;
      min-height: 100vh;
      padding: 24px;
      background-image: radial-gradient(circle at 20% 20%, rgba(30, 30, 80, 0.3), transparent 50%),
                        radial-gradient(circle at 80% 80%, rgba(80, 20, 60, 0.2), transparent 50%);
    }
    ::-webkit-scrollbar { width: 4px; }
    ::-webkit-scrollbar-track { background: #1a1a26; }
    ::-webkit-scrollbar-thumb { background: #4f8cff; border-radius: 10px; }

    .container { max-width: 1100px; margin: 0 auto; }

    /* HEADER */
    .header {
      display: flex;
      align-items: center;
      justify-content: space-between;
      flex-wrap: wrap;
      gap: 16px;
      padding: 16px 0 20px 0;
      border-bottom: 1px solid rgba(255,255,255,0.05);
      margin-bottom: 28px;
    }
    .logo {
      font-family: 'JetBrains Mono', monospace;
      font-weight: 800;
      font-size: 24px;
      letter-spacing: -0.5px;
    }
    .logo .x { color: #4f8cff; }
    .logo .sujal { color: #ffffff; }
    .logo .badge {
      font-size: 10px;
      font-weight: 400;
      color: rgba(255,255,255,0.2);
      background: rgba(255,255,255,0.04);
      padding: 2px 12px;
      border-radius: 40px;
      margin-left: 8px;
      border: 1px solid rgba(255,255,255,0.03);
    }
    .header-stats {
      display: flex;
      gap: 28px;
      align-items: center;
      flex-wrap: wrap;
    }
    .hstat {
      display: flex;
      flex-direction: column;
      align-items: center;
    }
    .hstat .num {
      font-family: 'JetBrains Mono', monospace;
      font-weight: 600;
      font-size: 20px;
      line-height: 1.2;
    }
    .hstat .num.cyan { color: #4f8cff; }
    .hstat .num.green { color: #34c759; }
    .hstat .num.amber { color: #ff9f0a; }
    .hstat .lbl {
      font-size: 9px;
      text-transform: uppercase;
      letter-spacing: 1.5px;
      color: rgba(255,255,255,0.2);
      font-weight: 500;
      margin-top: 2px;
    }
    .btn-primary {
      background: #4f8cff;
      border: none;
      color: #0a0a12;
      font-weight: 700;
      font-size: 13px;
      padding: 10px 24px;
      border-radius: 40px;
      cursor: pointer;
      transition: all 0.25s;
      font-family: 'Inter', sans-serif;
      box-shadow: 0 4px 20px rgba(79,140,255,0.15);
    }
    .btn-primary:hover {
      background: #3a7ae6;
      transform: translateY(-1px);
      box-shadow: 0 8px 30px rgba(79,140,255,0.25);
    }
    .btn-danger {
      background: #ff453a;
      color: #fff;
    }
    .btn-danger:hover { background: #e0352b; }
    .btn-success {
      background: #34c759;
      color: #0a0a12;
    }
    .btn-success:hover { background: #2db84d; }

    /* CARDS */
    .grid {
      display: grid;
      grid-template-columns: repeat(auto-fill, minmax(260px, 1fr));
      gap: 16px;
      margin-top: 12px;
    }
    .card {
      background: rgba(18, 18, 34, 0.6);
      backdrop-filter: blur(8px);
      border: 1px solid rgba(255,255,255,0.04);
      border-radius: 16px;
      padding: 18px 20px;
      transition: all 0.3s ease;
    }
    .card:hover {
      border-color: rgba(79,140,255,0.15);
      transform: translateY(-3px);
      box-shadow: 0 12px 40px rgba(0,0,0,0.4);
    }
    .card-top {
      display: flex;
      align-items: center;
      gap: 10px;
      margin-bottom: 10px;
    }
    .status-dot {
      width: 8px;
      height: 8px;
      border-radius: 50%;
      flex-shrink: 0;
    }
    .status-dot.on {
      background: #34c759;
      box-shadow: 0 0 12px #34c75966;
      animation: pulse 2s infinite;
    }
    .status-dot.cooldown {
      background: #ff9f0a;
      box-shadow: 0 0 12px #ff9f0a66;
      animation: pulse 2s infinite;
    }
    .status-dot.off { background: #3a3a4c; }
    @keyframes pulse {
      0% { opacity: 1; }
      50% { opacity: 0.3; }
      100% { opacity: 1; }
    }
    .card-name {
      font-weight: 600;
      font-size: 15px;
      flex: 1;
      color: #fff;
    }
    .card-time {
      font-family: 'JetBrains Mono', monospace;
      font-size: 10px;
      color: rgba(255,255,255,0.15);
    }
    .card-stats {
      display: flex;
      gap: 14px;
      font-size: 13px;
      font-weight: 500;
      margin-bottom: 12px;
      color: rgba(255,255,255,0.4);
    }
    .card-stats strong { color: #fff; font-weight: 600; }
    .card-actions {
      display: flex;
      gap: 4px;
      flex-wrap: wrap;
    }
    .btn-sm {
      font-family: 'Inter', sans-serif;
      font-weight: 500;
      font-size: 10px;
      padding: 4px 12px;
      border-radius: 40px;
      border: none;
      cursor: pointer;
      transition: all 0.2s;
    }
    .btn-sm-start { background: #34c759; color: #0a0a12; }
    .btn-sm-start:hover { background: #2db84d; }
    .btn-sm-stop { background: #ff453a; color: #fff; }
    .btn-sm-stop:hover { background: #e0352b; }
    .btn-sm-edit {
      background: rgba(255,255,255,0.04);
      color: rgba(255,255,255,0.3);
      border: 1px solid rgba(255,255,255,0.03);
    }
    .btn-sm-edit:hover { background: rgba(255,255,255,0.08); color: #fff; }
    .btn-sm-logs {
      background: rgba(79,140,255,0.06);
      color: #4f8cff;
      border: 1px solid rgba(79,140,255,0.04);
    }
    .btn-sm-logs:hover { background: rgba(79,140,255,0.12); }
    .btn-sm-del {
      background: rgba(255,69,58,0.04);
      color: #ff453a;
      border: 1px solid rgba(255,69,58,0.03);
      padding: 4px 8px;
    }
    .btn-sm-del:hover { background: rgba(255,69,58,0.1); }
    .btn-sm-expand {
      background: transparent;
      color: rgba(255,255,255,0.08);
      border: none;
      font-size: 14px;
      cursor: pointer;
    }
    .card-detail {
      margin-top: 12px;
      padding-top: 12px;
      border-top: 1px solid rgba(255,255,255,0.04);
      display: none;
      font-size: 11px;
      color: rgba(255,255,255,0.25);
    }
    .card-detail.open { display: block; }
    .gc-pill {
      display: inline-block;
      background: rgba(255,255,255,0.03);
      border: 1px solid rgba(255,255,255,0.03);
      padding: 2px 10px;
      border-radius: 40px;
      margin: 2px 4px 2px 0;
      font-size: 10px;
      color: rgba(255,255,255,0.2);
    }
    .detail-line { padding: 2px 0; }
    .last-action-text { color: #4f8cff; font-weight: 500; }

    /* LOGS */
    .log-panel {
      display: none;
      margin-top: 8px;
      background: rgba(0,0,0,0.2);
      border-radius: 12px;
      overflow: hidden;
    }
    .log-panel.open { display: block; }
    .log-header {
      display: flex;
      justify-content: space-between;
      padding: 4px 12px;
      background: rgba(0,0,0,0.15);
      font-size: 9px;
      color: rgba(255,255,255,0.1);
      border-bottom: 1px solid rgba(255,255,255,0.02);
    }
    .log-live { color: #34c759; display: flex; align-items: center; gap: 4px; font-weight: 500; }
    .log-live::before {
      content: '';
      width: 4px;
      height: 4px;
      background: #34c759;
      border-radius: 50%;
      display: inline-block;
      animation: live-pulse 1.5s infinite;
    }
    @keyframes live-pulse {
      0% { opacity: 1; }
      50% { opacity: 0.2; }
      100% { opacity: 1; }
    }
    .log-box {
      height: 120px;
      overflow-y: auto;
      padding: 6px 12px;
      font-family: 'JetBrains Mono', monospace;
      font-size: 9px;
      line-height: 1.8;
      color: rgba(255,255,255,0.15);
    }
    .log-line { color: rgba(255,255,255,0.15); }
    .log-line.ok { color: #34c759; }
    .log-line.err { color: #ff453a; }
    .log-line.warn { color: #ff9f0a; }
    .log-line.info { color: #4f8cff; }

    /* EMPTY */
    .empty {
      text-align: center;
      padding: 60px 20px;
      color: rgba(255,255,255,0.06);
    }
    .empty-icon { font-size: 36px; margin-bottom: 12px; opacity: 0.2; }
    .empty-text { font-size: 13px; color: rgba(255,255,255,0.08); }

    /* MODAL */
    .modal-overlay {
      display: none;
      position: fixed;
      inset: 0;
      background: rgba(6,8,15,0.8);
      backdrop-filter: blur(20px);
      z-index: 999;
      align-items: center;
      justify-content: center;
    }
    .modal-overlay.open { display: flex; }
    .modal {
      background: #14141e;
      border: 1px solid rgba(255,255,255,0.04);
      border-radius: 20px;
      padding: 28px 32px;
      width: 680px;
      max-width: 96vw;
      max-height: 90vh;
      overflow-y: auto;
      box-shadow: 0 40px 100px rgba(0,0,0,0.8);
    }
    .modal-title { font-size: 20px; font-weight: 700; color: #fff; margin-bottom: 20px; letter-spacing: -0.5px; }
    .modal-title .hl { color: #4f8cff; }
    .form-section { margin-bottom: 18px; }
    .form-section-title {
      font-size: 9px;
      text-transform: uppercase;
      letter-spacing: 1.5px;
      color: rgba(255,255,255,0.15);
      margin-bottom: 8px;
      font-weight: 600;
    }
    .form-grid {
      display: grid;
      grid-template-columns: 1fr 1fr;
      gap: 10px;
    }
    .form-group { display: flex; flex-direction: column; gap: 3px; }
    .form-group.full { grid-column: 1 / -1; }
    label {
      font-size: 10px;
      color: rgba(255,255,255,0.2);
      font-weight: 500;
      text-transform: uppercase;
      letter-spacing: 0.5px;
    }
    input, textarea, select {
      background: rgba(0,0,0,0.3);
      border: 1px solid rgba(255,255,255,0.04);
      color: #fff;
      padding: 8px 12px;
      border-radius: 10px;
      font-family: 'Inter', sans-serif;
      font-size: 12px;
      transition: all 0.2s;
      outline: none;
      width: 100%;
    }
    input:focus, textarea:focus { border-color: #4f8cff; box-shadow: 0 0 0 3px rgba(79,140,255,0.04); }
    textarea { resize: vertical; min-height: 48px; }

    .fetch-row { display: flex; gap: 8px; align-items: flex-end; }
    .btn-fetch {
      background: rgba(79,140,255,0.04);
      border: 1px solid rgba(79,140,255,0.06);
      color: #4f8cff;
      padding: 8px 16px;
      border-radius: 40px;
      font-weight: 500;
      cursor: pointer;
      transition: all 0.2s;
      white-space: nowrap;
      font-size: 11px;
    }
    .btn-fetch:hover { background: #4f8cff; color: #0a0a12; }
    #fetch-status { font-size: 10px; color: rgba(255,255,255,0.1); margin-top: 4px; }

    .gc-picker { margin-top: 8px; display: none; }
    .gc-list {
      display: flex;
      flex-direction: column;
      gap: 4px;
      max-height: 140px;
      overflow-y: auto;
    }
    .gc-item {
      display: flex;
      align-items: center;
      gap: 8px;
      padding: 6px 10px;
      background: rgba(0,0,0,0.15);
      border-radius: 10px;
      border: 1px solid rgba(255,255,255,0.02);
      cursor: pointer;
      transition: 0.2s;
      font-size: 12px;
    }
    .gc-item:hover { border-color: rgba(255,255,255,0.04); }
    .gc-item.selected { border-color: #4f8cff; background: rgba(79,140,255,0.02); }
    .gc-item input[type=checkbox] { width: 14px; height: 14px; accent-color: #4f8cff; cursor: pointer; }
    .gc-item-name { flex: 1; color: rgba(255,255,255,0.6); }
    .gc-item-id { font-size: 9px; color: rgba(255,255,255,0.08); }

    .msgs-wrap { display: flex; flex-direction: column; gap: 4px; }
    .msg-row { display: flex; gap: 4px; align-items: flex-start; }
    .msg-row textarea { flex: 1; }
    .btn-icon {
      background: rgba(255,255,255,0.02);
      border: none;
      color: rgba(255,255,255,0.08);
      padding: 6px 10px;
      border-radius: 10px;
      cursor: pointer;
      font-size: 12px;
    }
    .btn-icon:hover { background: rgba(255,69,58,0.08); color: #ff453a; }

    .modal-footer {
      display: flex;
      justify-content: flex-end;
      gap: 8px;
      margin-top: 18px;
      padding-top: 14px;
      border-top: 1px solid rgba(255,255,255,0.03);
    }
    .btn-save {
      background: #4f8cff;
      border: none;
      color: #0a0a12;
      font-weight: 700;
      padding: 10px 28px;
      border-radius: 40px;
      cursor: pointer;
      transition: 0.3s;
      font-size: 13px;
    }
    .btn-save:hover { background: #3a7ae6; transform: scale(1.02); }
    .btn-cancel {
      background: rgba(255,255,255,0.02);
      border: 1px solid rgba(255,255,255,0.03);
      color: rgba(255,255,255,0.2);
      padding: 10px 20px;
      border-radius: 40px;
      cursor: pointer;
      transition: 0.3s;
      font-size: 13px;
    }
    .btn-cancel:hover { background: rgba(255,255,255,0.04); }

    @media (max-width: 700px) {
      .header { flex-direction: column; align-items: stretch; text-align: center; }
      .header-stats { justify-content: center; }
      .grid { grid-template-columns: 1fr; }
      .form-grid { grid-template-columns: 1fr; }
      .form-group.full { grid-column: auto; }
      .fetch-row { flex-wrap: wrap; }
    }
  </style>
</head>
<body>
<div class="container">
  <div class="header">
    <div class="logo"><span class="x">x</span><span class="sujal">SUJAL</span><span class="badge">X</span></div>
    <div class="header-stats">
      <div class="hstat"><div class="num cyan" id="h-accounts">0</div><div class="lbl">Accounts</div></div>
      <div class="hstat"><div class="num green" id="h-running">0</div><div class="lbl">Running</div></div>
      <div class="hstat"><div class="num amber" id="h-sent">0</div><div class="lbl">Sent</div></div>
      <button class="btn-primary" onclick="openAddModal()">+ New Account</button>
    </div>
  </div>

  <div class="grid" id="accounts-wrap"></div>
</div>

<!-- MODAL -->
<div class="modal-overlay" id="modal">
<div class="modal">
  <div class="modal-title"><span class="hl">✦</span> <span id="modal-title">Add Account</span></div>

  <div class="form-section">
    <div class="form-section-title">Credentials</div>
    <div class="form-grid">
      <div class="form-group"><label>Name</label><input type="text" id="f-name" placeholder="e.g. Main Bot" /></div>
      <div class="form-group"><label>Session ID</label><input type="text" id="f-sid" placeholder="sessionid" autocomplete="off" /></div>
      <div class="form-group"><label>CSRF Token</label><input type="text" id="f-csrf" placeholder="csrftoken (optional)" /></div>
      <div class="form-group full"><label>Proxy (optional)</label><input type="text" id="f-proxy" placeholder="http://user:pass@ip:port" /></div>
    </div>
  </div>

  <div class="form-section">
    <div class="form-section-title">Group Chats (Max 5)</div>
    <div class="fetch-row">
      <div class="form-group" style="flex:1"><label>Fetch Groups</label></div>
      <button class="btn-fetch" onclick="fetchGroups()">⚡ Fetch GCs</button>
    </div>
    <div id="fetch-status"></div>
    <div class="gc-picker" id="gc-picker">
      <div class="gc-list" id="gc-list"></div>
      <div style="margin-top:4px;font-size:10px;color:rgba(255,255,255,0.08);"><span id="gc-count">0</span> / 5 selected</div>
    </div>
    <div class="form-group" style="margin-top:8px;">
      <label>Or enter manually (one per line)</label>
      <textarea id="f-groups" rows="3" placeholder="1234567890&#10;0987654321"></textarea>
    </div>
    <div class="form-group">
      <label>Group Names (same order, one per line, optional)</label>
      <textarea id="f-gnames" rows="3" placeholder="Group1&#10;Group2"></textarea>
    </div>
  </div>

  <div class="form-section">
    <div class="form-section-title">NC Titles (Rotate)</div>
    <div class="form-group"><input type="text" id="f-titles" placeholder="Title1, Title2, Title3" /></div>
  </div>

  <div class="form-section">
    <div class="form-section-title">Messages (---MSG--- separated)</div>
    <div class="msgs-wrap" id="msgs-wrap"></div>
    <button class="btn-fetch" style="width:100%;justify-content:center;margin-top:4px;" onclick="addMsgField()">+ Add Message</button>
  </div>

  <div class="form-section">
    <div class="form-section-title">Delays & Cooldowns</div>
    <div class="form-grid">
      <div class="form-group"><label>Min Delay (s)</label><input type="number" id="f-msg-min" value="2" step="0.5" /></div>
      <div class="form-group"><label>Max Delay (s)</label><input type="number" id="f-msg-max" value="5" step="0.5" /></div>
      <div class="form-group"><label>NC every N msgs (0=start only)</label><input type="number" id="f-nc-every-msgs" value="0" /></div>
      <div class="form-group"><label>Cooldown after N msgs</label><input type="number" id="f-cooldown-after" value="0" /></div>
      <div class="form-group"><label>Cooldown Duration (min)</label><input type="number" id="f-cooldown-dur" value="5" /></div>
    </div>
  </div>

  <div class="modal-footer">
    <button class="btn-cancel" onclick="closeModal()">Cancel</button>
    <button class="btn-save" onclick="saveAccount()">Save</button>
  </div>
</div>
</div>

<script>
let accounts = {};
let editingId = null;
let fetchedGroups = [];
let selectedGCs = [];

// ── FETCH GROUPS ──────────────────────────────────────────────
async function fetchGroups() {
  const sid = document.getElementById('f-sid').value.trim();
  if (!sid) { alert('Enter Session ID first'); return; }
  const proxy = document.getElementById('f-proxy').value.trim();
  const statusEl = document.getElementById('fetch-status');
  statusEl.textContent = '⚡ Fetching...';
  statusEl.style.color = '#ff9f0a';
  try {
    const r = await fetch('/api/fetch-groups', {
      method: 'POST',
      headers: {'Content-Type':'application/json'},
      body: JSON.stringify({session_id: sid, acc_id: editingId || 'fetch_temp', proxy: proxy})
    });
    const d = await r.json();
    if (d.groups && d.groups.length > 0) {
      fetchedGroups = d.groups;
      statusEl.textContent = `✅ ${d.groups.length} GCs found`;
      statusEl.style.color = '#34c759';
      renderGCPicker();
    } else {
      statusEl.textContent = '⚠️ No GCs found';
      statusEl.style.color = '#ff9f0a';
    }
  } catch(e) {
    statusEl.textContent = `❌ Error: ${e.message}`;
    statusEl.style.color = '#ff453a';
  }
}

function renderGCPicker() {
  const picker = document.getElementById('gc-picker');
  const list = document.getElementById('gc-list');
  picker.style.display = 'block';
  list.innerHTML = '';
  fetchedGroups.forEach(g => {
    const isSelected = selectedGCs.some(s => s.id === g.id);
    const item = document.createElement('div');
    item.className = 'gc-item' + (isSelected ? ' selected' : '');
    item.innerHTML = `
      <input type="checkbox" ${isSelected ? 'checked' : ''} data-id="${g.id}" data-name="${g.name}"/>
      <span class="gc-item-name">${g.name}</span>
      <span class="gc-item-id">${g.id}</span>
    `;
    const cb = item.querySelector('input');
    cb.addEventListener('change', () => toggleGC(g.id, g.name, cb, item));
    list.appendChild(item);
  });
  updateGCCount();
}

function toggleGC(id, name, cb, item) {
  if (cb.checked) {
    if (selectedGCs.length >= 5) {
      cb.checked = false;
      alert('Max 5 GCs allowed');
      return;
    }
    selectedGCs.push({id, name});
    item.classList.add('selected');
  } else {
    selectedGCs = selectedGCs.filter(s => s.id !== id);
    item.classList.remove('selected');
  }
  updateGCCount();
}

function updateGCCount() {
  document.getElementById('gc-count').textContent = selectedGCs.length;
}

// ── MESSAGES ───────────────────────────────────────────────
function addMsgField(val = '') {
  const wrap = document.getElementById('msgs-wrap');
  const row = document.createElement('div');
  row.className = 'msg-row';
  row.innerHTML = `
    <textarea placeholder="Type your message..." rows="3">${val}</textarea>
    <button class="btn-icon" onclick="this.parentElement.remove()">✕</button>
  `;
  wrap.appendChild(row);
}

function getMsgs() {
  return [...document.querySelectorAll('#msgs-wrap textarea')]
    .map(t => t.value.trim()).filter(Boolean);
}

function setMsgs(raw) {
  document.getElementById('msgs-wrap').innerHTML = '';
  const parts = raw.split('---MSG---').map(s => s.trim()).filter(Boolean);
  if (parts.length === 0) { addMsgField(); return; }
  parts.forEach(p => addMsgField(p));
}

// ── MODAL ──────────────────────────────────────────────────
function openAddModal() {
  editingId = null;
  fetchedGroups = [];
  selectedGCs = [];
  document.getElementById('modal-title').textContent = 'Add Account';
  document.getElementById('f-name').value = '';
  document.getElementById('f-sid').value = '';
  document.getElementById('f-csrf').value = '';
  document.getElementById('f-proxy').value = '';
  document.getElementById('f-titles').value = '';
  document.getElementById('f-msg-min').value = '2';
  document.getElementById('f-msg-max').value = '5';
  document.getElementById('f-nc-every-msgs').value = '0';
  document.getElementById('f-cooldown-after').value = '0';
  document.getElementById('f-cooldown-dur').value = '5';
  document.getElementById('f-groups').value = '';
  document.getElementById('f-gnames').value = '';
  document.getElementById('gc-picker').style.display = 'none';
  document.getElementById('gc-list').innerHTML = '';
  document.getElementById('gc-count').textContent = '0';
  document.getElementById('fetch-status').textContent = '';
  setMsgs('');
  document.getElementById('modal').classList.add('open');
}

function openEditModal(id) {
  editingId = id;
  const acc = accounts[id];
  selectedGCs = [];
  const savedGroups = acc.groups ? acc.groups.split('\n').filter(Boolean) : [];
  const savedNames  = acc.group_names ? acc.group_names.split('\n').filter(Boolean) : [];
  savedGroups.forEach((gid, i) => {
    selectedGCs.push({id: gid.trim(), name: savedNames[i] || gid.trim()});
  });
  fetchedGroups = [];

  document.getElementById('modal-title').textContent = 'Edit Account';
  document.getElementById('f-name').value = acc.name || '';
  document.getElementById('f-sid').value = acc.session_id || '';
  document.getElementById('f-csrf').value = acc.csrf_token || '';
  document.getElementById('f-proxy').value = acc.proxy || '';
  document.getElementById('f-titles').value = acc.nc_titles || '';
  document.getElementById('f-msg-min').value = acc.msg_delay_min || '2';
  document.getElementById('f-msg-max').value = acc.msg_delay_max || '5';
  document.getElementById('f-nc-every-msgs').value = acc.nc_every_msgs || '0';
  document.getElementById('f-cooldown-after').value = acc.cooldown_after || '0';
  document.getElementById('f-cooldown-dur').value = acc.cooldown_dur || '5';
  document.getElementById('f-groups').value = savedGroups.join('\n');
  document.getElementById('f-gnames').value = savedNames.join('\n');
  document.getElementById('fetch-status').textContent = '';

  if (selectedGCs.length > 0) {
    fetchedGroups = selectedGCs.map(s => ({id: s.id, name: s.name}));
    renderGCPicker();
  } else {
    document.getElementById('gc-picker').style.display = 'none';
  }
  setMsgs(acc.messages || acc.message || '');
  document.getElementById('modal').classList.add('open');
}

function closeModal() {
  document.getElementById('modal').classList.remove('open');
  editingId = null;
}

// ── SAVE ───────────────────────────────────────────────────
async function saveAccount() {
  const msgs = getMsgs();
  if (!msgs.length) { alert('Add at least one message'); return; }

  // ─── GROUPS: Manual or Fetched ──────────────────────────
  let finalGroups = selectedGCs;
  if (finalGroups.length === 0) {
    const manualGroups = document.getElementById('f-groups').value.trim();
    const manualNames = document.getElementById('f-gnames').value.trim();
    if (manualGroups) {
      const gids = manualGroups.split('\n').filter(Boolean);
      const gnames = manualNames ? manualNames.split('\n').filter(Boolean) : [];
      finalGroups = gids.map((id, i) => ({
        id: id.trim(),
        name: gnames[i] ? gnames[i].trim() : id.trim()
      }));
    }
  }

  const body = {
    name:            document.getElementById('f-name').value.trim(),
    session_id:      document.getElementById('f-sid').value.trim(),
    csrf_token:      document.getElementById('f-csrf').value.trim(),
    proxy:           document.getElementById('f-proxy').value.trim(),
    groups:          finalGroups.map(s => s.id).join('\n'),
    group_names:     finalGroups.map(s => s.name).join('\n'),
    nc_titles:       document.getElementById('f-titles').value.trim(),
    messages:        msgs.join('---MSG---'),
    msg_delay_min:   parseFloat(document.getElementById('f-msg-min').value),
    msg_delay_max:   parseFloat(document.getElementById('f-msg-max').value),
    nc_every_msgs:   parseInt(document.getElementById('f-nc-every-msgs').value),
    cooldown_after:  parseInt(document.getElementById('f-cooldown-after').value),
    cooldown_dur:    parseFloat(document.getElementById('f-cooldown-dur').value),
  };

  if (!body.name) { alert('Enter account name'); return; }
  if (!body.session_id && !editingId) { alert('Session ID required'); return; }

  const url    = editingId ? `/api/accounts/${editingId}` : '/api/accounts';
  const method = editingId ? 'PUT' : 'POST';
  const r = await fetch(url, {method, headers:{'Content-Type':'application/json'}, body: JSON.stringify(body)});
  const d = await r.json();
  if (d.success) { closeModal(); loadAccounts(); }
  else alert(d.error || 'Save failed');
}

// ── CONTROLS ───────────────────────────────────────────────
async function startBot(id) {
  const r = await fetch(`/api/accounts/${id}/start`, {method:'POST'});
  const d = await r.json();
  if (!d.success) alert(d.error || 'Start failed');
}

async function stopBot(id) {
  await fetch(`/api/accounts/${id}/stop`, {method:'POST'});
}

async function deleteAcc(id) {
  if (!confirm('Delete this account?')) return;
  await fetch(`/api/accounts/${id}`, {method:'DELETE'});
  loadAccounts();
}

function toggleLogs(id) {
  const el = document.getElementById(`log-panel-${id}`);
  if (el) el.classList.toggle('open');
}

function toggleDetail(id) {
  const el = document.getElementById(`detail-${id}`);
  if (el) el.classList.toggle('open');
}

// ── RENDER ─────────────────────────────────────────────────
function fmtTime(secs) {
  if (!secs || secs < 0) return '--:--:--';
  const h = Math.floor(secs/3600);
  const m = Math.floor((secs%3600)/60);
  const s = Math.floor(secs%60);
  return `${String(h).padStart(2,'0')}:${String(m).padStart(2,'0')}:${String(s).padStart(2,'0')}`;
}

function renderAccounts(data) {
  const wrap = document.getElementById('accounts-wrap');
  const ids = Object.keys(data);

  if (ids.length === 0) {
    wrap.innerHTML = `<div class="empty"><div class="empty-icon">◆</div><div class="empty-text">No accounts yet.<br>Click "New Account" to start.</div></div>`;
    return;
  }

  let totalRunning = 0, totalSent = 0;
  ids.forEach(id => {
    const st = data[id].status || {};
    if (st.running) totalRunning++;
    totalSent += st.sent || 0;
  });
  document.getElementById('h-accounts').textContent = ids.length;
  document.getElementById('h-running').textContent  = totalRunning;
  document.getElementById('h-sent').textContent     = totalSent;

  ids.forEach(id => {
    const acc = data[id];
    const st  = acc.status || {};
    const isRunning = st.running;
    const isCooldown = st.cooldown;
    const runtime = st.runtime_secs ? fmtTime(st.runtime_secs) : '--:--:--';
    const cooldownStr = st.cooldown && st.cooldown_remaining > 0
      ? ' 😴 ' + fmtTime(st.cooldown_remaining)
      : (isCooldown ? ' 🔄 CD' : '');
    const dotCls = isCooldown ? 'cooldown' : (isRunning ? 'on' : 'off');
    const gcNames = acc.group_names ? acc.group_names.split('\n').filter(Boolean) : [];

    let existing = document.getElementById(`card-${id}`);
    if (!existing) {
      existing = document.createElement('div');
      existing.className = 'card';
      existing.id = `card-${id}`;
      wrap.appendChild(existing);
    }

    const existingLogPanel = document.getElementById(`log-panel-${id}`);
    const logOpen = existingLogPanel ? existingLogPanel.classList.contains('open') : false;
    const detailOpen = document.getElementById(`detail-${id}`)?.classList.contains('open') || false;

    existing.innerHTML = `
      <div class="card-top">
        <div class="status-dot ${dotCls}"></div>
        <div class="card-name">${acc.name || id} ${cooldownStr}</div>
        <div class="card-time">${runtime}</div>
      </div>
      <div class="card-stats">
        <span><strong>${st.sent||0}</strong> sent</span>
        <span><strong>${st.failed||0}</strong> failed</span>
        <span><strong>${st.nc_done||0}</strong> NC</span>
      </div>
      <div class="card-actions">
        ${isRunning
          ? `<button class="btn-sm btn-sm-stop" onclick="stopBot('${id}')">Stop</button>`
          : `<button class="btn-sm btn-sm-start" onclick="startBot('${id}')">Start</button>`}
        <button class="btn-sm btn-sm-logs" onclick="toggleLogs('${id}')">Logs</button>
        <button class="btn-sm btn-sm-edit" onclick="openEditModal('${id}')">Edit</button>
        <button class="btn-sm btn-sm-del" onclick="deleteAcc('${id}')">✕</button>
        <button class="btn-sm btn-sm-expand" onclick="toggleDetail('${id}')">⌃</button>
      </div>
      <div class="card-detail ${detailOpen ? 'open' : ''}" id="detail-${id}">
        ${gcNames.length ? `<div>${gcNames.map(n=>`<span class="gc-pill">${n}</span>`).join('')}</div>` : ''}
        <div class="detail-line"><strong>Delay:</strong> ${acc.msg_delay_min||2}s – ${acc.msg_delay_max||5}s</div>
        ${acc.cooldown_after > 0 ? `<div class="detail-line"><strong>Cooldown:</strong> ${acc.cooldown_after} → ${acc.cooldown_dur}min</div>` : ''}
        ${acc.nc_titles ? `<div class="detail-line"><strong>NC Titles:</strong> ${acc.nc_titles.split(',').length}</div>` : ''}
        <div class="last-action-text">❯ ${st.last_action||'Idle'}</div>
        <div class="log-panel ${logOpen ? 'open' : ''}" id="log-panel-${id}">
          <div class="log-header">
            <span>Console</span>
            <span class="log-live">LIVE</span>
          </div>
          <div class="log-box" id="log-box-${id}"></div>
        </div>
      </div>
    `;
  });

  wrap.querySelectorAll('.card').forEach(el => {
    if (!data[el.id.replace('card-','')]) el.remove();
  });
}

function colorLog(line) {
  if (line.includes('✅') || line.includes('✓')) return 'ok';
  if (line.includes('❌') || line.includes('failed') || line.includes('Failed')) return 'err';
  if (line.includes('⚠️')) return 'warn';
  if (line.includes('🔄') || line.includes('Round')) return 'info';
  if (line.includes('💤') || line.includes('⏭') || line.includes('😴')) return 'info';
  return '';
}

// ── POLL ───────────────────────────────────────────────────
async function loadAccounts() {
  try {
    const r = await fetch('/api/accounts');
    accounts = await r.json();
    renderAccounts(accounts);
  } catch(e) { console.error('Load error', e); }
}

async function pollLogs() {
  const openPanels = document.querySelectorAll('.log-panel.open');
  for (const panel of openPanels) {
    const id = panel.id.replace('log-panel-','');
    try {
      const r = await fetch(`/api/accounts/${id}/logs`);
      const d = await r.json();
      const box = document.getElementById(`log-box-${id}`);
      if (box && d.logs) {
        const currentCount = box.querySelectorAll('.log-line').length;
        if (currentCount === 0) {
          box.innerHTML = d.logs.map(l => `<div class="log-line ${colorLog(l)}">${l}</div>`).join('');
          box.scrollTop = box.scrollHeight;
        } else if (d.logs.length > currentCount) {
          const atBottom = box.scrollHeight - box.scrollTop - box.clientHeight < 40;
          const newLines = d.logs.slice(currentCount);
          newLines.forEach(l => {
            const div = document.createElement('div');
            div.className = `log-line ${colorLog(l)}`;
            div.textContent = l;
            box.appendChild(div);
          });
          if (atBottom) box.scrollTop = box.scrollHeight;
        }
      }
    } catch(e) {}
  }
}

// ── INIT ────────────────────────────────────────────────────
loadAccounts();
setInterval(loadAccounts, 4000);
setInterval(pollLogs, 1500);

document.getElementById('modal').addEventListener('click', function(e) {
  if (e.target === this) closeModal();
});
</script>
</body>
</html>
