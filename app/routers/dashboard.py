"""Dashboard route serving the PokeAMI Control Panel SPA.

Single HTML page with inline CSS/JS, no external dependencies.
"""

from fastapi import APIRouter
from fastapi.responses import HTMLResponse

router = APIRouter(tags=["Dashboard"])

DASHBOARD_HTML = """\
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>PokeAMI Control Panel</title>
<style>
  :root {
    --bg: #1a1d23;
    --panel: #23272e;
    --border: #333840;
    --text: #e0e0e0;
    --muted: #888;
    --green: #4caf50;
    --red: #f44336;
    --amber: #ff9800;
    --blue: #42a5f5;
    --cyan: #26c6da;
  }
  * { margin: 0; padding: 0; box-sizing: border-box; }
  body {
    font-family: 'Segoe UI', system-ui, -apple-system, sans-serif;
    background: var(--bg); color: var(--text);
    display: grid;
    grid-template-columns: 1fr 320px;
    grid-template-rows: auto 1fr 200px;
    height: 100vh; overflow: hidden;
  }
  header {
    grid-column: 1 / -1;
    background: var(--panel); border-bottom: 1px solid var(--border);
    padding: 10px 20px; display: flex; align-items: center; gap: 16px;
  }
  header h1 { font-size: 1.2rem; font-weight: 600; }
  header h1 span { color: var(--cyan); }
  .status-badge {
    margin-left: auto; font-size: 0.8rem; padding: 4px 10px;
    border-radius: 12px; background: var(--green); color: #fff;
  }
  .status-badge.error { background: var(--red); }

  /* Diagram area */
  .diagram-area {
    grid-column: 1; grid-row: 2;
    overflow: auto; padding: 20px;
    display: flex; align-items: center; justify-content: center;
  }
  svg.pipeline { width: 100%; max-width: 1100px; height: auto; }
  svg.pipeline text { fill: var(--text); font-family: inherit; }
  svg.pipeline .node-rect {
    fill: var(--panel); stroke: var(--border); stroke-width: 1.5; rx: 8;
  }
  svg.pipeline .node-rect:hover { stroke: var(--cyan); }
  svg.pipeline .arrow { stroke: var(--muted); stroke-width: 1.5; fill: none; marker-end: url(#arrowhead); }
  .dot { r: 6; }
  .dot.on { fill: var(--green); }
  .dot.off { fill: var(--red); }
  .node-label { font-size: 13px; font-weight: 600; text-anchor: middle; }
  .node-sub { font-size: 10px; fill: var(--muted) !important; text-anchor: middle; }
  .svg-btn {
    font-size: 11px; padding: 3px 8px; border: 1px solid var(--border);
    border-radius: 4px; cursor: pointer; color: var(--text);
    background: var(--bg); margin: 0 2px;
  }
  .svg-btn:hover { border-color: var(--cyan); }
  .svg-btn.stop { border-color: var(--red); color: var(--red); }
  .svg-btn.start { border-color: var(--green); color: var(--green); }

  /* Sidebar */
  .sidebar {
    grid-column: 2; grid-row: 2;
    background: var(--panel); border-left: 1px solid var(--border);
    display: flex; flex-direction: column; overflow: hidden;
  }
  .sidebar h2 { font-size: 0.9rem; padding: 12px 14px 8px; color: var(--muted); text-transform: uppercase; letter-spacing: 1px; }
  .sidebar .field { padding: 4px 14px; }
  .sidebar label { display: block; font-size: 0.75rem; color: var(--muted); margin-bottom: 2px; }
  .sidebar input, .sidebar select {
    width: 100%; padding: 6px 8px; font-size: 0.85rem;
    background: var(--bg); color: var(--text); border: 1px solid var(--border);
    border-radius: 4px; outline: none;
  }
  .sidebar input:focus, .sidebar select:focus { border-color: var(--cyan); }
  .meter-card {
    margin: 8px 14px; padding: 10px; background: var(--bg);
    border: 1px solid var(--border); border-radius: 6px; font-size: 0.8rem;
    flex: 1; overflow-y: auto;
  }
  .meter-card .row { display: flex; justify-content: space-between; padding: 3px 0; }
  .meter-card .row .k { color: var(--muted); }
  .sidebar .actions { padding: 8px 14px; display: flex; gap: 6px; }
  .sidebar .actions button {
    flex: 1; padding: 7px 0; font-size: 0.8rem; border: 1px solid var(--border);
    border-radius: 4px; cursor: pointer; background: var(--bg); color: var(--text);
  }
  .sidebar .actions button:hover { border-color: var(--cyan); color: var(--cyan); }

  /* Event log */
  .event-log {
    grid-column: 1 / -1; grid-row: 3;
    background: var(--panel); border-top: 1px solid var(--border);
    display: flex; flex-direction: column; overflow: hidden;
  }
  .event-log h2 {
    font-size: 0.8rem; padding: 8px 14px 4px; color: var(--muted);
    text-transform: uppercase; letter-spacing: 1px; flex-shrink: 0;
  }
  .log-list {
    flex: 1; overflow-y: auto; padding: 0 14px 8px;
    font-family: 'Cascadia Code', 'Fira Code', monospace; font-size: 0.78rem;
  }
  .log-entry { padding: 2px 0; display: flex; gap: 10px; }
  .log-entry .ts { color: var(--muted); white-space: nowrap; }
  .log-entry .comp { color: var(--cyan); min-width: 110px; }
  .log-entry.warn .comp { color: var(--amber); }
  .log-entry.error .comp { color: var(--red); }
  .log-entry .msg { flex: 1; }
</style>
</head>
<body>

<header>
  <h1><span>Poke</span>AMI Control Panel</h1>
  <div class="status-badge" id="overallStatus">Loading...</div>
</header>

<!-- Diagram -->
<div class="diagram-area">
<svg class="pipeline" viewBox="0 0 1100 320" xmlns="http://www.w3.org/2000/svg">
  <defs>
    <marker id="arrowhead" markerWidth="8" markerHeight="6" refX="8" refY="3" orient="auto">
      <polygon points="0 0, 8 3, 0 6" fill="#888"/>
    </marker>
  </defs>

  <!-- Arrows -->
  <path class="arrow" d="M 165 105 L 200 105"/>
  <path class="arrow" d="M 330 105 L 365 105"/>
  <path class="arrow" d="M 495 105 L 530 105"/>
  <path class="arrow" d="M 660 105 L 695 105"/>
  <!-- MDM branches to Analytics below -->
  <path class="arrow" d="M 760 140 L 760 170"/>
  <path class="arrow" d="M 825 105 L 860 105"/>
  <path class="arrow" d="M 990 105 L 1025 105"/>

  <!-- Node: MeterPark -->
  <rect class="node-rect" x="30" y="50" width="135" height="110"/>
  <circle class="dot" id="dot-meter_park" cx="55" cy="70" r="6"/>
  <text class="node-label" x="97" y="92">MeterPark</text>
  <text class="node-sub" x="97" y="108">Fleet generation</text>
  <foreignObject x="38" y="120" width="120" height="30">
    <div xmlns="http://www.w3.org/1999/xhtml" style="display:flex;justify-content:center;gap:4px">
      <button class="svg-btn stop" onclick="stopComponent('meter_park')">Stop</button>
      <button class="svg-btn start" onclick="startComponent('meter_park')">Start</button>
    </div>
  </foreignObject>

  <!-- Node: DataGenerator -->
  <rect class="node-rect" x="200" y="50" width="130" height="110"/>
  <circle class="dot" id="dot-data_generator" cx="225" cy="70" r="6"/>
  <text class="node-label" x="265" y="92">DataGen</text>
  <text class="node-sub" x="265" y="108">Time-series</text>
  <foreignObject x="208" y="120" width="115" height="30">
    <div xmlns="http://www.w3.org/1999/xhtml" style="display:flex;justify-content:center;gap:4px">
      <button class="svg-btn stop" onclick="stopComponent('data_generator')">Stop</button>
      <button class="svg-btn start" onclick="startComponent('data_generator')">Start</button>
    </div>
  </foreignObject>

  <!-- Node: Headend -->
  <rect class="node-rect" x="365" y="50" width="130" height="110"/>
  <circle class="dot" id="dot-headend" cx="390" cy="70" r="6"/>
  <text class="node-label" x="430" y="92">Headend</text>
  <text class="node-sub" x="430" y="108">Gridstream HES</text>
  <foreignObject x="373" y="120" width="115" height="30">
    <div xmlns="http://www.w3.org/1999/xhtml" style="display:flex;justify-content:center;gap:4px">
      <button class="svg-btn stop" onclick="stopComponent('headend')">Stop</button>
      <button class="svg-btn start" onclick="startComponent('headend')">Start</button>
    </div>
  </foreignObject>

  <!-- Node: MDM -->
  <rect class="node-rect" x="530" y="50" width="130" height="110"/>
  <circle class="dot" id="dot-mdm" cx="555" cy="70" r="6"/>
  <text class="node-label" x="595" y="92">MDM</text>
  <text class="node-sub" x="595" y="108">VEE pipeline</text>
  <foreignObject x="538" y="120" width="115" height="30">
    <div xmlns="http://www.w3.org/1999/xhtml" style="display:flex;justify-content:center;gap:4px">
      <button class="svg-btn stop" onclick="stopComponent('mdm')">Stop</button>
      <button class="svg-btn start" onclick="startComponent('mdm')">Start</button>
    </div>
  </foreignObject>

  <!-- Node: Analytics -->
  <rect class="node-rect" x="695" y="170" width="130" height="100"/>
  <circle class="dot" id="dot-analytics" cx="720" cy="190" r="6"/>
  <text class="node-label" x="760" y="212">Analytics</text>
  <text class="node-sub" x="760" y="228">Gridstream</text>
  <foreignObject x="703" y="240" width="115" height="30">
    <div xmlns="http://www.w3.org/1999/xhtml" style="display:flex;justify-content:center;gap:4px">
      <button class="svg-btn stop" onclick="stopComponent('analytics')">Stop</button>
      <button class="svg-btn start" onclick="startComponent('analytics')">Start</button>
    </div>
  </foreignObject>

  <!-- Node: DeliveryManager -->
  <rect class="node-rect" x="695" y="50" width="130" height="110"/>
  <circle class="dot" id="dot-delivery_manager" cx="720" cy="70" r="6"/>
  <text class="node-label" x="760" y="92">Delivery</text>
  <text class="node-sub" x="760" y="108">Promise Mgr</text>
  <foreignObject x="703" y="120" width="115" height="30">
    <div xmlns="http://www.w3.org/1999/xhtml" style="display:flex;justify-content:center;gap:4px">
      <button class="svg-btn stop" onclick="stopComponent('delivery_manager')">Stop</button>
      <button class="svg-btn start" onclick="startComponent('delivery_manager')">Start</button>
    </div>
  </foreignObject>

  <!-- Node: REST API (no controls - always on) -->
  <rect class="node-rect" x="860" y="50" width="130" height="110" style="stroke:var(--cyan)"/>
  <circle class="dot on" cx="885" cy="70" r="6"/>
  <text class="node-label" x="925" y="92">REST API</text>
  <text class="node-sub" x="925" y="108">FastAPI</text>

</svg>
</div>

<!-- Sidebar -->
<div class="sidebar">
  <h2>Controls</h2>
  <div class="field">
    <label for="apiKey">API Key</label>
    <input type="text" id="apiKey" value="dev-api-key-change-me"/>
  </div>
  <h2>Meter Selector</h2>
  <div class="field">
    <label for="meterSelect">Select Meter</label>
    <select id="meterSelect"><option value="">Loading...</option></select>
  </div>
  <div class="meter-card" id="meterCard">
    <div style="color:var(--muted);text-align:center;padding:20px">Select a meter</div>
  </div>
  <div class="actions">
    <button onclick="getReadings()">Get Readings</button>
    <button onclick="onDemandRead()">On-Demand Read</button>
  </div>
</div>

<!-- Event Log -->
<div class="event-log">
  <h2>Event Log</h2>
  <div class="log-list" id="logList"></div>
</div>

<script>
const API = '/api/v1';
let pollTimer = null;
let allMeters = [];

function apiKey() { return document.getElementById('apiKey').value; }

async function pollStatus() {
  try {
    const r = await fetch(API + '/simulator/status');
    if (!r.ok) throw new Error(r.status);
    const data = await r.json();
    // Update dots
    for (const [name, enabled] of Object.entries(data.components)) {
      const dot = document.getElementById('dot-' + name);
      if (dot) {
        dot.classList.toggle('on', enabled);
        dot.classList.toggle('off', !enabled);
      }
    }
    // Overall status
    const allOn = Object.values(data.components).every(v => v);
    const badge = document.getElementById('overallStatus');
    badge.textContent = allOn ? 'All Systems Online' : 'Degraded';
    badge.className = 'status-badge' + (allOn ? '' : ' error');
    // Events
    renderEvents(data.events);
  } catch (e) {
    document.getElementById('overallStatus').textContent = 'Connection Error';
    document.getElementById('overallStatus').className = 'status-badge error';
  }
}

function renderEvents(events) {
  const el = document.getElementById('logList');
  el.innerHTML = events.map(e =>
    `<div class="log-entry ${e.level}">` +
    `<span class="ts">${e.ts.replace('T',' ').substring(0,19)}</span>` +
    `<span class="comp">${e.component}</span>` +
    `<span class="msg">${e.message}</span></div>`
  ).reverse().join('');
}

async function stopComponent(name) {
  try {
    const r = await fetch(API + '/simulator/' + name + '/stop', {
      method: 'POST', headers: {'X-API-Key': apiKey()}
    });
    if (!r.ok) { const d = await r.json(); alert(d.detail || 'Error'); }
    pollStatus();
  } catch(e) { alert('Error: ' + e.message); }
}

async function startComponent(name) {
  try {
    const r = await fetch(API + '/simulator/' + name + '/start', {
      method: 'POST', headers: {'X-API-Key': apiKey()}
    });
    if (!r.ok) { const d = await r.json(); alert(d.detail || 'Error'); }
    pollStatus();
  } catch(e) { alert('Error: ' + e.message); }
}

async function loadMeters() {
  try {
    const r = await fetch(API + '/meters?limit=100', {
      headers: {'X-API-Key': apiKey()}
    });
    if (!r.ok) return;
    const data = await r.json();
    allMeters = data.items || [];
    const sel = document.getElementById('meterSelect');
    sel.innerHTML = '<option value="">-- Select Meter --</option>' +
      allMeters.map(m =>
        `<option value="${m.mrid}">${m.serial_number} (${m.model})</option>`
      ).join('');
  } catch(e) { console.error('loadMeters', e); }
}

document.getElementById('meterSelect').addEventListener('change', function() {
  selectMeter(this.value);
});

function selectMeter(mrid) {
  const card = document.getElementById('meterCard');
  if (!mrid) {
    card.innerHTML = '<div style="color:var(--muted);text-align:center;padding:20px">Select a meter</div>';
    return;
  }
  const m = allMeters.find(x => x.mrid === mrid);
  if (!m) return;
  card.innerHTML = [
    row('mRID', m.mrid.substring(0,8) + '...'),
    row('Serial', m.serial_number),
    row('Model', m.model),
    row('Type', m.meter_type),
    row('Status', m.status),
    row('Firmware', m.firmware_version),
    row('Phase', m.phase_code),
    row('Comm', m.comm_module.comm_type),
    row('Signal', m.comm_module.signal_strength + ' dBm'),
    row('Form', m.form_number),
    row('Rated', (m.rated_power_w/1000) + ' kW'),
  ].join('');
}

function row(k, v) { return `<div class="row"><span class="k">${k}</span><span>${v}</span></div>`; }

async function getReadings() {
  const mrid = document.getElementById('meterSelect').value;
  if (!mrid) { alert('Select a meter first'); return; }
  try {
    const r = await fetch(API + '/meters/' + mrid + '/readings?limit=5', {
      headers: {'X-API-Key': apiKey()}
    });
    if (!r.ok) { alert('Error ' + r.status); return; }
    const data = await r.json();
    const count = (data.items || []).reduce((s, mr) =>
      s + mr.interval_blocks.reduce((s2, b) => s2 + b.interval_readings.length, 0), 0);
    // Log an event client-side (will show on next poll)
    await fetch(API + '/simulator/status');  // trigger refresh
    alert('Retrieved ' + count + ' interval readings for ' + (data.items||[]).length + ' reading types');
  } catch(e) { alert('Error: ' + e.message); }
}

async function onDemandRead() {
  const mrid = document.getElementById('meterSelect').value;
  if (!mrid) { alert('Select a meter first'); return; }
  try {
    const r = await fetch(API + '/delivery-promises', {
      method: 'POST',
      headers: {'X-API-Key': apiKey(), 'Content-Type': 'application/json'},
      body: JSON.stringify({meter_mrids: [mrid]})
    });
    if (!r.ok) { alert('Error ' + r.status); return; }
    const data = await r.json();
    alert('Delivery promise created: ' + data.promise_id + '\\nStatus: ' + data.status);
  } catch(e) { alert('Error: ' + e.message); }
}

// Init
loadMeters();
pollStatus();
pollTimer = setInterval(pollStatus, 3000);
</script>
</body>
</html>
"""


@router.get("/dashboard", response_class=HTMLResponse)
async def dashboard() -> HTMLResponse:
    """Serve the PokeAMI Control Panel dashboard."""
    return HTMLResponse(content=DASHBOARD_HTML)
