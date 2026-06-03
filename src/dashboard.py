"""
Flask Web Dashboard
Provides a live web UI showing report status, run history,
and a download button — so Railway can serve a public URL.
"""
import os
import threading
from datetime import datetime
from pathlib import Path

from flask import Flask, jsonify, render_template_string, send_file

from src.config import REPORTS_DIR
from src.utils.logger import get_logger

logger = get_logger(__name__)
app = Flask(__name__)

# Track pipeline state in memory
pipeline_state = {
    "status":      "idle",       # idle | running | done | error
    "last_run":    None,
    "last_report": None,
    "message":     "No report generated yet.",
    "runs":        [],
}


# ─────────────────────────────────────────────────────────────────────────────
# HTML Template
# ─────────────────────────────────────────────────────────────────────────────

DASHBOARD_HTML = """
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Automated Report System</title>
<style>
  * { margin: 0; padding: 0; box-sizing: border-box; }
  body {
    font-family: 'Segoe UI', sans-serif;
    background: #0f1117;
    color: #e2e8f0;
    min-height: 100vh;
  }
  header {
    background: linear-gradient(135deg, #1a237e, #283593);
    padding: 28px 40px;
    border-bottom: 3px solid #42a5f5;
  }
  header h1 { font-size: 1.8rem; font-weight: 700; color: #fff; }
  header p  { color: #90caf9; margin-top: 4px; font-size: 0.95rem; }
  .container { max-width: 960px; margin: 0 auto; padding: 36px 24px; }

  .cards {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
    gap: 20px;
    margin-bottom: 36px;
  }
  .card {
    background: #1e2130;
    border: 1px solid #2d3250;
    border-radius: 12px;
    padding: 24px;
    text-align: center;
  }
  .card .label { font-size: 0.78rem; color: #94a3b8; text-transform: uppercase; letter-spacing: 1px; }
  .card .value { font-size: 1.6rem; font-weight: 700; margin-top: 8px; color: #42a5f5; }
  .card .value.green  { color: #4caf50; }
  .card .value.yellow { color: #ffc107; }
  .card .value.red    { color: #ef5350; }

  .section {
    background: #1e2130;
    border: 1px solid #2d3250;
    border-radius: 12px;
    padding: 28px;
    margin-bottom: 24px;
  }
  .section h2 {
    font-size: 1.1rem;
    font-weight: 600;
    color: #90caf9;
    margin-bottom: 20px;
    border-bottom: 1px solid #2d3250;
    padding-bottom: 12px;
  }

  .btn {
    display: inline-block;
    padding: 12px 28px;
    border-radius: 8px;
    font-size: 0.95rem;
    font-weight: 600;
    cursor: pointer;
    border: none;
    transition: opacity 0.2s;
  }
  .btn:hover { opacity: 0.85; }
  .btn-primary  { background: #1a237e; color: #fff; }
  .btn-success  { background: #2e7d32; color: #fff; }
  .btn-disabled { background: #374151; color: #6b7280; cursor: not-allowed; }

  .status-badge {
    display: inline-block;
    padding: 4px 14px;
    border-radius: 20px;
    font-size: 0.82rem;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.5px;
  }
  .badge-idle    { background: #374151; color: #9ca3af; }
  .badge-running { background: #1565c0; color: #90caf9; }
  .badge-done    { background: #1b5e20; color: #a5d6a7; }
  .badge-error   { background: #7f1d1d; color: #fca5a5; }

  table { width: 100%; border-collapse: collapse; }
  th { text-align: left; padding: 10px 14px; font-size: 0.8rem;
       color: #64748b; text-transform: uppercase; letter-spacing: 0.5px;
       border-bottom: 1px solid #2d3250; }
  td { padding: 12px 14px; font-size: 0.9rem; border-bottom: 1px solid #1a1f2e; }
  tr:last-child td { border-bottom: none; }

  .spinner {
    display: inline-block;
    width: 14px; height: 14px;
    border: 2px solid #3b82f6;
    border-top-color: transparent;
    border-radius: 50%;
    animation: spin 0.8s linear infinite;
    margin-right: 8px;
    vertical-align: middle;
  }
  @keyframes spin { to { transform: rotate(360deg); } }

  .message-box {
    background: #111827;
    border-left: 3px solid #42a5f5;
    padding: 14px 18px;
    border-radius: 6px;
    font-size: 0.88rem;
    color: #94a3b8;
    margin-top: 16px;
  }
  a { color: #42a5f5; text-decoration: none; }
  a:hover { text-decoration: underline; }
</style>
</head>
<body>
<header>
  <h1>📊 Automated Report Generation System</h1>
  <p>Python · Pandas · REST API · openpyxl — Weekly Business Intelligence</p>
</header>

<div class="container">

  <!-- Status Cards -->
  <div class="cards">
    <div class="card">
      <div class="label">Status</div>
      <div class="value" id="status-text">—</div>
    </div>
    <div class="card">
      <div class="label">Total Reports</div>
      <div class="value green" id="total-reports">0</div>
    </div>
    <div class="card">
      <div class="label">Last Run</div>
      <div class="value" id="last-run" style="font-size:1rem; margin-top:12px;">—</div>
    </div>
    <div class="card">
      <div class="label">Schedule</div>
      <div class="value" style="font-size:1rem; margin-top:12px;">{{ schedule }}</div>
    </div>
  </div>

  <!-- Actions -->
  <div class="section">
    <h2>⚡ Actions</h2>
    <button class="btn btn-primary" id="run-btn" onclick="triggerReport()">
      ▶ Run Report Now
    </button>
    &nbsp;&nbsp;
    <a id="download-btn" class="btn btn-disabled" href="#" onclick="return false;">
      ⬇ Download Latest Report
    </a>
    <div class="message-box" id="message">{{ message }}</div>
  </div>

  <!-- Run History -->
  <div class="section">
    <h2>📋 Run History</h2>
    <table>
      <thead>
        <tr>
          <th>#</th>
          <th>Timestamp</th>
          <th>Status</th>
          <th>Duration</th>
          <th>Report File</th>
        </tr>
      </thead>
      <tbody id="history-body">
        <tr><td colspan="5" style="color:#4b5563; text-align:center; padding:24px;">No runs yet</td></tr>
      </tbody>
    </table>
  </div>

  <!-- Tech Stack -->
  <div class="section">
    <h2>🛠 Tech Stack</h2>
    <table>
      <tr><td style="color:#94a3b8; width:180px;">Language</td><td>Python 3.11</td></tr>
      <tr><td style="color:#94a3b8;">Data Processing</td><td>Pandas, NumPy</td></tr>
      <tr><td style="color:#94a3b8;">Report Generation</td><td>openpyxl (9-sheet Excel workbook)</td></tr>
      <tr><td style="color:#94a3b8;">REST API</td><td>requests with retry logic & graceful fallback</td></tr>
      <tr><td style="color:#94a3b8;">Scheduling</td><td>schedule library — configurable day/time</td></tr>
      <tr><td style="color:#94a3b8;">Deployment</td><td>Docker · Railway · GitHub Actions</td></tr>
      <tr><td style="color:#94a3b8;">Testing</td><td>pytest · 20+ unit tests · CI/CD</td></tr>
    </table>
  </div>

</div>

<script>
  function updateUI(data) {
    // Status badge
    const badges = { idle:'badge-idle', running:'badge-running', done:'badge-done', error:'badge-error' };
    const labels = { idle:'Idle', running:'Running…', done:'Done', error:'Error' };
    const el = document.getElementById('status-text');
    el.innerHTML = `<span class="status-badge ${badges[data.status]}">${labels[data.status]}</span>`;

    document.getElementById('total-reports').textContent = data.runs.length;
    document.getElementById('last-run').textContent = data.last_run || '—';
    document.getElementById('message').textContent = data.message;

    // Download button
    const dlBtn = document.getElementById('download-btn');
    if (data.last_report) {
      dlBtn.href = '/download';
      dlBtn.className = 'btn btn-success';
      dlBtn.onclick = null;
    }

    // Run button
    const runBtn = document.getElementById('run-btn');
    if (data.status === 'running') {
      runBtn.innerHTML = '<span class="spinner"></span>Generating…';
      runBtn.className = 'btn btn-disabled';
      runBtn.disabled = true;
    } else {
      runBtn.innerHTML = '▶ Run Report Now';
      runBtn.className = 'btn btn-primary';
      runBtn.disabled = false;
    }

    // History table
    const tbody = document.getElementById('history-body');
    if (data.runs.length === 0) {
      tbody.innerHTML = '<tr><td colspan="5" style="color:#4b5563;text-align:center;padding:24px;">No runs yet</td></tr>';
    } else {
      tbody.innerHTML = data.runs.slice().reverse().map((r, i) => `
        <tr>
          <td>${data.runs.length - i}</td>
          <td>${r.timestamp}</td>
          <td><span class="status-badge ${r.success ? 'badge-done' : 'badge-error'}">${r.success ? 'Success' : 'Failed'}</span></td>
          <td>${r.duration}s</td>
          <td style="font-size:0.82rem; color:#64748b;">${r.filename || '—'}</td>
        </tr>`).join('');
    }
  }

  function triggerReport() {
    fetch('/run', { method: 'POST' })
      .then(r => r.json())
      .then(d => { if (d.status) poll(); });
  }

  function poll() {
    fetch('/status').then(r => r.json()).then(data => {
      updateUI(data);
      if (data.status === 'running') setTimeout(poll, 2000);
    });
  }

  // Initial load + auto-refresh every 10s
  poll();
  setInterval(poll, 10000);
</script>
</body>
</html>
"""


# ─────────────────────────────────────────────────────────────────────────────
# Routes
# ─────────────────────────────────────────────────────────────────────────────

@app.route("/")
def index():
    from src.config import SCHEDULE_DAY, SCHEDULE_TIME
    return render_template_string(
        DASHBOARD_HTML,
        schedule=f"Every {SCHEDULE_DAY.capitalize()} @ {SCHEDULE_TIME}",
        message=pipeline_state["message"],
    )


@app.route("/status")
def status():
    return jsonify(pipeline_state)


@app.route("/run", methods=["POST"])
def run_report():
    if pipeline_state["status"] == "running":
        return jsonify({"status": "already_running"})

    thread = threading.Thread(target=_run_pipeline_background, daemon=True)
    thread.start()
    return jsonify({"status": "started"})


@app.route("/download")
def download():
    if not pipeline_state["last_report"]:
        return "No report available", 404
    path = Path(pipeline_state["last_report"])
    if not path.exists():
        return "Report file not found", 404
    return send_file(str(path), as_attachment=True, download_name=path.name)


@app.route("/health")
def health():
    return jsonify({"status": "ok", "timestamp": datetime.now().isoformat()})


# ─────────────────────────────────────────────────────────────────────────────
# Background pipeline runner
# ─────────────────────────────────────────────────────────────────────────────

def _run_pipeline_background():
    from src.core.data_processor import load_and_process_all
    from src.core.report_builder import build_report
    from src.api.api_client import fetch_external_kpis

    pipeline_state["status"]  = "running"
    pipeline_state["message"] = "Pipeline running — loading data…"
    start = datetime.now()

    try:
        data       = load_and_process_all()
        pipeline_state["message"] = "Data loaded — fetching API data…"

        benchmarks = fetch_external_kpis()
        if benchmarks:
            data["benchmarks"] = benchmarks
        pipeline_state["message"] = "Building Excel report…"

        report_path = build_report(data)
        elapsed     = round((datetime.now() - start).total_seconds(), 1)

        pipeline_state["status"]      = "done"
        pipeline_state["last_report"] = str(report_path)
        pipeline_state["last_run"]    = datetime.now().strftime("%Y-%m-%d %H:%M")
        pipeline_state["message"]     = f"✅ Report generated in {elapsed}s — ready to download."
        pipeline_state["runs"].append({
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "success":   True,
            "duration":  elapsed,
            "filename":  Path(report_path).name,
        })
        logger.info("Report generated: %s", report_path)

    except Exception as exc:
        elapsed = round((datetime.now() - start).total_seconds(), 1)
        pipeline_state["status"]  = "error"
        pipeline_state["message"] = f"❌ Pipeline failed: {exc}"
        pipeline_state["runs"].append({
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "success":   False,
            "duration":  elapsed,
            "filename":  None,
        })
        logger.exception("Pipeline failed: %s", exc)
