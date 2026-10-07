"""HTML page rendering for the Web UI."""

from pathlib import Path

BASE_DIR = Path(__file__).parent

NAV_ITEMS = [
    ("dashboard", "Dashboard"),
    ("chat", "Chat"),
    ("agent", "Agent"),
    ("tasks", "Tasks"),
    ("scheduler", "Scheduler"),
    ("workers", "Workers"),
    ("memory", "Memory"),
    ("skills", "Skills"),
    ("tools", "Tools"),
    ("approvals", "Approvals"),
    ("checkpoints", "Checkpoints"),
    ("logs", "Logs"),
    ("system", "System"),
    ("diagnostics", "Diagnostics"),
    ("self", "Self-X"),
    ("settings", "Settings"),
]

PAGE_TITLES = {name: title for name, title in NAV_ITEMS}


def _nav(active: str) -> str:
    links = []
    for name, title in NAV_ITEMS:
        cls = ' class="active"' if name == active else ""
        links.append(f'<a href="/{name}"{cls}>{title}</a>')
    return "\n".join(links)


def render_page(page: str) -> str:
    title = PAGE_TITLES.get(page, page.title())
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>LiteRT Agent — {title}</title>
<link rel="stylesheet" href="/static/css/style.css">
</head>
<body>
<header class="topbar">
  <div class="brand">⚡ LiteRT Agent</div>
  <div class="status-pill"><span class="dot" id="conn-dot"></span><span id="conn-text">connecting…</span></div>
  <div class="model-badge" id="model-badge">Model: LiteRT-LM (local)</div>
</header>
<div class="layout">
  <nav class="sidebar">
{_nav(page)}
  </nav>
  <main id="main" data-page="{page}">
    <h1>{title}</h1>
    <div id="content"><div class="loading">Loading…</div></div>
  </main>
</div>
<footer class="statusbar">Agent runtime: local-first · LiteRT-LM only · v0.1.0</footer>
<script src="/static/js/app.js"></script>
</body>
</html>"""
