"""Dashboard route serving the PokeAMI Control Panel SPA.

Single HTML page with inline CSS/JS, no external dependencies.
"""

from fastapi import APIRouter, Request
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

  /* Results overlay */
  .results-overlay {
    position: absolute; inset: 0; z-index: 10;
    background: rgba(26,29,35,0.97);
    display: flex; flex-direction: column;
    overflow: hidden; border-radius: 8px;
  }
  .results-overlay.hidden { display: none; }
  .results-header {
    display: flex; align-items: center; padding: 14px 18px 10px;
    border-bottom: 1px solid var(--border); flex-shrink: 0;
  }
  .results-header h3 { flex: 1; font-size: 1rem; font-weight: 600; }
  .results-close {
    background: none; border: 1px solid var(--border); color: var(--muted);
    border-radius: 4px; padding: 4px 10px; cursor: pointer; font-size: 0.8rem;
  }
  .results-close:hover { border-color: var(--red); color: var(--red); }
  .results-body { flex: 1; overflow-y: auto; padding: 14px 18px; }

  /* Tabs */
  .tab-bar {
    display: flex; gap: 4px; padding: 0 0 12px; flex-wrap: wrap; flex-shrink: 0;
  }
  .tab {
    padding: 5px 12px; font-size: 0.78rem; border: 1px solid var(--border);
    border-radius: 4px; cursor: pointer; background: var(--bg); color: var(--muted);
  }
  .tab:hover { border-color: var(--cyan); color: var(--text); }
  .tab.active { border-color: var(--cyan); color: var(--cyan); background: var(--panel); }

  /* Results table */
  .results-table { width: 100%; border-collapse: collapse; font-size: 0.8rem; }
  .results-table th {
    text-align: left; padding: 6px 10px; color: var(--muted); font-weight: 500;
    border-bottom: 1px solid var(--border); font-size: 0.75rem;
    text-transform: uppercase; letter-spacing: 0.5px;
  }
  .results-table td {
    padding: 5px 10px; border-bottom: 1px solid rgba(51,56,64,0.5);
  }
  .results-table tr:hover td { background: rgba(66,165,245,0.05); }
  .results-summary {
    display: flex; gap: 18px; padding: 10px 0 14px; font-size: 0.8rem; color: var(--muted);
  }
  .results-summary strong { color: var(--text); }

  /* Quality badges */
  .quality-badge {
    font-size: 0.7rem; padding: 2px 6px; border-radius: 3px;
    font-weight: 500; display: inline-block;
  }
  .quality-badge.valid { background: rgba(76,175,80,0.2); color: var(--green); }
  .quality-badge.estimated { background: rgba(255,152,0,0.2); color: var(--amber); }
  .quality-badge.suspect { background: rgba(244,67,54,0.2); color: var(--red); }
  .quality-badge.raw { background: rgba(136,136,136,0.2); color: var(--muted); }

  /* Promise tracker */
  .promise-tracker {
    background: var(--panel); border: 1px solid var(--border);
    border-radius: 8px; padding: 16px; margin-bottom: 16px;
  }
  .promise-row { display: flex; align-items: center; gap: 12px; margin-bottom: 10px; }
  .promise-row .label { color: var(--muted); font-size: 0.78rem; min-width: 100px; }
  .promise-row .value { font-size: 0.85rem; }
  .promise-status {
    font-size: 0.75rem; padding: 3px 10px; border-radius: 10px;
    font-weight: 600; display: inline-block; text-transform: uppercase; letter-spacing: 0.5px;
  }
  .promise-status.pending { background: rgba(66,165,245,0.2); color: var(--blue); }
  .promise-status.inprogress { background: rgba(255,152,0,0.2); color: var(--amber); }
  .promise-status.completed { background: rgba(76,175,80,0.2); color: var(--green); }
  .promise-status.partial { background: rgba(255,152,0,0.2); color: var(--amber); }
  .promise-status.failed { background: rgba(244,67,54,0.2); color: var(--red); }
  .progress-bar {
    flex: 1; height: 8px; background: var(--bg); border-radius: 4px; overflow: hidden;
  }
  .progress-bar-fill {
    height: 100%; background: var(--green); border-radius: 4px;
    transition: width 0.4s ease;
  }
  .meter-result-row {
    display: flex; align-items: center; gap: 10px; padding: 6px 0;
    border-bottom: 1px solid rgba(51,56,64,0.4); font-size: 0.8rem;
  }
  .meter-result-row .mrid { color: var(--muted); font-family: 'Cascadia Code', monospace; font-size: 0.75rem; }
  .meter-status-icon { width: 18px; text-align: center; }
  .spinner { display: inline-block; width: 14px; height: 14px; border: 2px solid var(--border); border-top-color: var(--cyan); border-radius: 50%; animation: spin 0.8s linear infinite; }
  @keyframes spin { to { transform: rotate(360deg); } }
  .promise-readings-label { font-size: 0.85rem; color: var(--muted); margin: 16px 0 10px; font-weight: 500; }

  /* Diagram area needs relative for overlay positioning */
  .diagram-area { position: relative; }
</style>
</head>
<body>

<header>
  <h1><span>Poke</span>AMI Control Panel</h1>
  <div class="status-badge" id="overallStatus">Loading...</div>
</header>

<!-- Diagram -->
<div class="diagram-area">
<div id="resultsOverlay" class="results-overlay hidden">
  <div class="results-header">
    <h3 id="resultsTitle">Results</h3>
    <button class="results-close" onclick="hideResults()">Close</button>
  </div>
  <div class="results-body" id="resultsBody"></div>
</div>
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
const API = '{{API_BASE}}';
let pollTimer = null;
let allMeters = [];
let readingTypesCache = {};
let promisePollTimer = null;

function apiKey() { return document.getElementById('apiKey').value; }

async function pollStatus() {
  try {
    const r = await fetch(API + '/simulator/status');
    if (!r.ok) throw new Error(r.status);
    const data = await r.json();
    for (const [name, enabled] of Object.entries(data.components)) {
      const dot = document.getElementById('dot-' + name);
      if (dot) {
        dot.classList.toggle('on', enabled);
        dot.classList.toggle('off', !enabled);
      }
    }
    const allOn = Object.values(data.components).every(v => v);
    const badge = document.getElementById('overallStatus');
    badge.textContent = allOn ? 'All Systems Online' : 'Degraded';
    badge.className = 'status-badge' + (allOn ? '' : ' error');
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

async function loadReadingTypes() {
  try {
    const r = await fetch(API + '/reading-types', {
      headers: {'X-API-Key': apiKey()}
    });
    if (!r.ok) return;
    const data = await r.json();
    (data.items || []).forEach(rt => { readingTypesCache[rt.mrid] = rt; });
  } catch(e) { console.error('loadReadingTypes', e); }
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

/* ---------- Results overlay helpers ---------- */

function showResults(title, html) {
  document.getElementById('resultsTitle').textContent = title;
  document.getElementById('resultsBody').innerHTML = html;
  document.getElementById('resultsOverlay').classList.remove('hidden');
}

function hideResults() {
  document.getElementById('resultsOverlay').classList.add('hidden');
  document.getElementById('resultsBody').innerHTML = '';
  if (promisePollTimer) { clearTimeout(promisePollTimer); promisePollTimer = null; }
}

function readingTypeName(mrid) {
  const rt = readingTypesCache[mrid];
  if (!rt) return mrid.substring(0, 8) + '...';
  return rt.name + ' (' + rt.unit + ')';
}

function qualityBadge(qualityList) {
  if (!qualityList || qualityList.length === 0) return '<span class="quality-badge raw">raw</span>';
  const q = qualityList[0].quality_type;
  if (q === 'validated') return '<span class="quality-badge valid">validated</span>';
  if (q === 'estimated') return '<span class="quality-badge estimated">estimated</span>';
  if (q === 'suspect' || q === 'missing') return '<span class="quality-badge suspect">' + q + '</span>';
  return '<span class="quality-badge raw">' + q + '</span>';
}

function formatTs(ts) {
  return ts.replace('T', ' ').substring(0, 19);
}

function renderReadingsTable(meterReadings) {
  if (!meterReadings || meterReadings.length === 0) {
    return '<div style="color:var(--muted);padding:20px;text-align:center">No readings available</div>';
  }

  // Build tabs — one per reading type
  const tabs = meterReadings.map((mr, i) => {
    const name = readingTypeName(mr.reading_type_mrid);
    const cls = i === 0 ? 'tab active' : 'tab';
    return `<button class="${cls}" data-tab="${i}" onclick="switchTab(this)">${name}</button>`;
  }).join('');

  // Build tab content panels
  const panels = meterReadings.map((mr, i) => {
    const allReadings = mr.interval_blocks.flatMap(b => b.interval_readings);
    const rt = readingTypesCache[mr.reading_type_mrid];
    const unit = rt ? rt.unit : '';
    const display = i === 0 ? '' : 'display:none;';

    // Summary
    const total = allReadings.length;
    const validated = mr.is_validated ? 'Yes' : 'No';
    const period = mr.time_period
      ? formatTs(mr.time_period.start) + ' to ' + formatTs(mr.time_period.end)
      : '-';
    const summary = `<div class="results-summary">
      <span>Readings: <strong>${total}</strong></span>
      <span>Period: <strong>${period}</strong></span>
      <span>VEE Validated: <strong>${validated}</strong></span>
    </div>`;

    // Table rows (show last 20)
    const displayed = allReadings.slice(-20);
    const rows = displayed.map(r =>
      `<tr>
        <td>${formatTs(r.timestamp)}</td>
        <td style="text-align:right;font-family:'Cascadia Code',monospace">${r.value.toFixed(2)}</td>
        <td>${unit}</td>
        <td>${qualityBadge(r.quality)}</td>
      </tr>`
    ).join('');

    return `<div class="tab-panel" data-panel="${i}" style="${display}">
      ${summary}
      <table class="results-table">
        <thead><tr><th>Timestamp</th><th style="text-align:right">Value</th><th>Unit</th><th>Quality</th></tr></thead>
        <tbody>${rows}</tbody>
      </table>
    </div>`;
  }).join('');

  return `<div class="tab-bar">${tabs}</div>${panels}`;
}

function switchTab(btn) {
  const idx = btn.dataset.tab;
  const overlay = document.getElementById('resultsBody');
  overlay.querySelectorAll('.tab').forEach(t => t.classList.remove('active'));
  btn.classList.add('active');
  overlay.querySelectorAll('.tab-panel').forEach(p => {
    p.style.display = p.dataset.panel === idx ? '' : 'none';
  });
}

function renderPromiseTracker(promise) {
  const pct = promise.meters_total > 0
    ? Math.round((promise.meters_collected / promise.meters_total) * 100) : 0;
  const statusCls = promise.status.toLowerCase().replace('_', '');

  const meterRows = (promise.meter_results || []).map(mr => {
    let icon;
    if (mr.status === 'collected') icon = '<span style="color:var(--green)">&#10003;</span>';
    else if (mr.status === 'failed') icon = '<span style="color:var(--red)">&#10007;</span>';
    else icon = '<span class="spinner"></span>';

    const statusText = mr.status;
    const failReason = mr.failure_reason ? ` — ${mr.failure_reason}` : '';

    return `<div class="meter-result-row">
      <span class="meter-status-icon">${icon}</span>
      <span class="mrid">${mr.meter_mrid.substring(0,12)}...</span>
      <span>${statusText}${failReason}</span>
    </div>`;
  }).join('');

  const eta = formatTs(promise.estimated_delivery);

  return `<div class="promise-tracker">
    <div class="promise-row">
      <span class="label">Promise ID</span>
      <span class="value" style="font-family:'Cascadia Code',monospace;font-size:0.78rem">${promise.promise_id.substring(0,12)}...</span>
    </div>
    <div class="promise-row">
      <span class="label">Status</span>
      <span class="promise-status ${statusCls}">${promise.status}</span>
    </div>
    <div class="promise-row">
      <span class="label">ETA</span>
      <span class="value">${eta}</span>
    </div>
    <div class="promise-row">
      <span class="label">Progress</span>
      <span class="value" style="margin-right:8px">${promise.meters_collected}/${promise.meters_total}</span>
      <div class="progress-bar"><div class="progress-bar-fill" style="width:${pct}%"></div></div>
    </div>
    ${meterRows}
  </div>`;
}

/* ---------- Get Readings (rewritten) ---------- */

async function getReadings() {
  const mrid = document.getElementById('meterSelect').value;
  if (!mrid) { alert('Select a meter first'); return; }
  try {
    showResults('Loading readings...', '<div style="color:var(--muted);padding:20px;text-align:center"><span class="spinner"></span> Fetching...</div>');
    const r = await fetch(API + '/meters/' + mrid + '/readings?limit=20', {
      headers: {'X-API-Key': apiKey()}
    });
    if (!r.ok) { hideResults(); alert('Error ' + r.status); return; }
    const data = await r.json();
    const items = data.items || [];

    // Resolve reading type names if cache is empty
    if (Object.keys(readingTypesCache).length === 0) await loadReadingTypes();

    const meter = allMeters.find(x => x.mrid === mrid);
    const title = 'Readings — ' + (meter ? meter.serial_number : mrid.substring(0, 8));
    const html = renderReadingsTable(items);
    showResults(title, html);
  } catch(e) { hideResults(); alert('Error: ' + e.message); }
}

/* ---------- On-Demand Read (rewritten) ---------- */

async function onDemandRead() {
  const mrid = document.getElementById('meterSelect').value;
  if (!mrid) { alert('Select a meter first'); return; }
  try {
    showResults('Creating delivery promise...', '<div style="color:var(--muted);padding:20px;text-align:center"><span class="spinner"></span> Submitting request...</div>');

    // Resolve reading type names if cache is empty
    if (Object.keys(readingTypesCache).length === 0) await loadReadingTypes();

    const r = await fetch(API + '/delivery-promises', {
      method: 'POST',
      headers: {'X-API-Key': apiKey(), 'Content-Type': 'application/json'},
      body: JSON.stringify({meter_mrids: [mrid]})
    });
    if (!r.ok) { hideResults(); alert('Error ' + r.status); return; }
    const promise = await r.json();

    const meter = allMeters.find(x => x.mrid === mrid);
    const title = 'On-Demand Read — ' + (meter ? meter.serial_number : mrid.substring(0, 8));
    showResults(title, renderPromiseTracker(promise));
    pollPromise(promise.promise_id, title);
  } catch(e) { hideResults(); alert('Error: ' + e.message); }
}

function pollPromise(promiseId, title) {
  promisePollTimer = setTimeout(async () => {
    try {
      const r = await fetch(API + '/delivery-promises/' + promiseId, {
        headers: {'X-API-Key': apiKey()}
      });
      if (!r.ok) return;
      const promise = await r.json();
      const terminal = ['completed', 'partial', 'failed'];
      const isDone = terminal.includes(promise.status);

      let html = renderPromiseTracker(promise);
      if (isDone) {
        // Collect all readings from meter results
        const allReadings = (promise.meter_results || [])
          .filter(mr => mr.readings && mr.readings.length > 0)
          .flatMap(mr => mr.readings);
        if (allReadings.length > 0) {
          html += '<div class="promise-readings-label">Collected Readings</div>';
          html += renderReadingsTable(allReadings);
        }
        if (promise.failure_summary) {
          html += '<div style="color:var(--red);font-size:0.8rem;margin-top:10px">Failures: ' + promise.failure_summary + '</div>';
        }
      }
      showResults(title, html);

      if (!isDone) pollPromise(promiseId, title);
    } catch(e) { console.error('pollPromise', e); }
  }, 2000);
}

// Init
loadMeters();
loadReadingTypes();
pollStatus();
pollTimer = setInterval(pollStatus, 3000);
</script>
</body>
</html>
"""


@router.get("/dashboard", response_class=HTMLResponse)
async def dashboard(request: Request) -> HTMLResponse:
    """Serve the PokeAMI Control Panel dashboard."""
    api_base = getattr(request.app.state, "api_base", "/api/v1")
    html = DASHBOARD_HTML.replace("{{API_BASE}}", api_base)
    return HTMLResponse(content=html)
