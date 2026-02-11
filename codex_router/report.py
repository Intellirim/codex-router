"""HTML report generator for codex-router usage statistics."""

import os
import tempfile
from datetime import datetime, timezone


def _base_style():
    return """
    :root {
        --bg: #0d1117; --card: #161b22; --border: #30363d;
        --text: #e6edf3; --muted: #8b949e;
        --green: #3fb950; --red: #f85149; --blue: #58a6ff;
        --purple: #bc8cff; --orange: #d29922;
    }
    * { margin:0; padding:0; box-sizing:border-box; }
    body {
        font-family: -apple-system,BlinkMacSystemFont,'Segoe UI',Helvetica,Arial,sans-serif;
        background:var(--bg); color:var(--text); line-height:1.6;
        padding:2rem; max-width:1100px; margin:0 auto;
    }
    .header { text-align:center; margin-bottom:2rem; padding-bottom:1.5rem; border-bottom:1px solid var(--border); }
    .header h1 { font-size:1.8rem; margin-bottom:0.3rem; }
    .header .subtitle { color:var(--muted); font-size:0.95rem; }
    .cards { display:grid; grid-template-columns:repeat(auto-fit,minmax(200px,1fr)); gap:1rem; margin-bottom:2rem; }
    .card { background:var(--card); border:1px solid var(--border); border-radius:8px; padding:1.2rem; }
    .card .label { color:var(--muted); font-size:0.8rem; text-transform:uppercase; letter-spacing:0.05em; margin-bottom:0.3rem; }
    .card .value { font-size:1.5rem; font-weight:600; }
    .card .value.pass { color:var(--green); }
    .card .value.warn { color:var(--orange); }
    .section { background:var(--card); border:1px solid var(--border); border-radius:8px; padding:1.5rem; margin-bottom:1.5rem; }
    .section h2 { font-size:1.1rem; margin-bottom:1rem; padding-bottom:0.5rem; border-bottom:1px solid var(--border); }
    table { width:100%; border-collapse:collapse; font-size:0.85rem; }
    th { text-align:left; color:var(--muted); font-weight:500; padding:0.5rem 0.8rem; border-bottom:1px solid var(--border); font-size:0.75rem; text-transform:uppercase; }
    td { padding:0.5rem 0.8rem; border-bottom:1px solid var(--border); }
    tr:last-child td { border-bottom:none; }
    .mono { font-family:'SF Mono',Monaco,Consolas,monospace; font-size:0.82rem; }
    .badge { display:inline-block; padding:0.15rem 0.5rem; border-radius:4px; font-size:0.72rem; font-weight:500; }
    .bar-bg { background:var(--bg); border-radius:4px; height:12px; width:100%; overflow:hidden; }
    .bar { height:12px; border-radius:4px; }
    .footer { text-align:center; color:var(--muted); font-size:0.8rem; margin-top:2rem; padding-top:1rem; border-top:1px solid var(--border); }
    .footer a { color:var(--blue); text-decoration:none; }
    """


def generate_html(stats, days=7, config_info=None):
    """Generate HTML report for usage statistics.

    Args:
        stats: Dict with total_requests, total_tokens, total_cost, and optionally by_model
        days: Number of days covered
        config_info: Optional dict with default_model, budget, etc.
    """
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
    total_requests = stats.get("total_requests", 0)
    total_tokens = stats.get("total_tokens", 0)
    total_cost = stats.get("total_cost", 0.0)
    by_model = stats.get("by_model", {})

    # Model breakdown rows
    model_rows = ""
    if by_model:
        max_cost = max(m.get("cost", 0) for m in by_model.values()) or 1
        for model, data in sorted(by_model.items(), key=lambda x: -x[1].get("cost", 0)):
            cost = data.get("cost", 0)
            tokens = data.get("tokens", 0)
            requests = data.get("requests", 0)
            pct = (cost / total_cost * 100) if total_cost > 0 else 0
            bar_width = (cost / max_cost * 100) if max_cost > 0 else 0
            model_rows += f"""
            <tr>
                <td class="mono" style="font-weight:600">{model}</td>
                <td>{requests}</td>
                <td class="mono">{tokens:,}</td>
                <td class="mono">${cost:.3f}</td>
                <td>
                    <div class="bar-bg"><div class="bar" style="width:{bar_width}%;background:var(--blue)"></div></div>
                </td>
                <td style="color:var(--muted)">{pct:.1f}%</td>
            </tr>"""

    budget_html = ""
    if config_info and config_info.get("budget"):
        budget = config_info["budget"]
        used_pct = min((total_cost / budget * 100), 100) if budget > 0 else 0
        bar_color = "var(--green)" if used_pct < 70 else "var(--orange)" if used_pct < 90 else "var(--red)"
        budget_html = f"""
        <div class="section">
            <h2>Budget</h2>
            <p style="margin-bottom:0.5rem">Used ${total_cost:.2f} of ${budget:.2f} ({used_pct:.1f}%)</p>
            <div class="bar-bg"><div class="bar" style="width:{used_pct}%;background:{bar_color}"></div></div>
        </div>"""

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>codex-router Usage Report</title>
<style>{_base_style()}</style>
</head>
<body>

<div class="header">
    <h1>codex-router Usage Report</h1>
    <div class="subtitle">Last {days} days &mdash; {now}</div>
</div>

<div class="cards">
    <div class="card">
        <div class="label">Total Requests</div>
        <div class="value">{total_requests}</div>
    </div>
    <div class="card">
        <div class="label">Total Tokens</div>
        <div class="value" style="font-size:1.2rem">{total_tokens:,}</div>
    </div>
    <div class="card">
        <div class="label">Total Cost</div>
        <div class="value {"warn" if total_cost > 10 else "pass"}">${total_cost:.2f}</div>
    </div>
    <div class="card">
        <div class="label">Avg Cost/Request</div>
        <div class="value" style="font-size:1.2rem">${(total_cost/total_requests if total_requests else 0):.3f}</div>
    </div>
</div>

{budget_html}

{"<div class='section'><h2>Cost by Model</h2><table><thead><tr><th>Model</th><th>Requests</th><th>Tokens</th><th>Cost</th><th>Usage</th><th>%</th></tr></thead><tbody>" + model_rows + "</tbody></table></div>" if model_rows else "<div class='section'><h2>Cost by Model</h2><p style='color:var(--muted)'>No usage data yet.</p></div>"}

<div class="footer">
    <p>Generated by <a href="https://pypi.org/project/codex-router/">codex-router</a> &mdash; Multi-model AI orchestration</p>
</div>

</body>
</html>"""
    return html


def export_html(stats, days=7, config_info=None, output_path=None):
    """Generate and save HTML report, return file path."""
    html = generate_html(stats, days, config_info)
    if not output_path:
        output_path = os.path.join(tempfile.gettempdir(), "codex-router-report.html")
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(html)
    return output_path
