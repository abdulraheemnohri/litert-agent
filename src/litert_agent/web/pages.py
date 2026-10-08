"""HTML shell and navigation for the LiteRT Agent control plane."""

from html import escape

NAV_GROUPS = [
    ("Operate", [
        ("dashboard", "Dashboard"),
        ("chat", "Chat"),
        ("agent", "Agent"),
        ("tasks", "Tasks"),
        ("plans", "Plans"),
        ("live", "Live Execution"),
    ]),
    ("Build", [
        ("memory", "Memory"),
        ("skills", "Skills"),
        ("tools", "Tools"),
        ("workers", "Workers"),
        ("browser", "Browser"),
        ("research", "Research"),
        ("goals", "Goals"),
    ]),
    ("Control", [
        ("scheduler", "Scheduler"),
        ("approvals", "Approvals"),
        ("security", "Security"),
        ("checkpoints", "Checkpoints"),
        ("audit", "Audit Log"),
        ("logs", "Logs"),
    ]),
    ("System", [
        ("system", "System"),
        ("model", "Model"),
        ("diagnostics", "Diagnostics"),
        ("settings", "Settings"),
        ("self", "Self-X"),
    ]),
]

PAGES = [name for _, items in NAV_GROUPS for name, _ in items]
PAGE_TITLES = {name: title for _, items in NAV_GROUPS for name, title in items}


def _nav(active: str) -> str:
    groups = []
    for group, items in NAV_GROUPS:
        links = "".join(
            f'<a href="/{escape(name)}" class="nav-link{" active" if name == active else ""}" '
            f'data-page="{escape(name)}"><span class="nav-icon">{escape(title[:1])}</span>{escape(title)}</a>'
            for name, title in items
        )
        groups.append(f'<div class="nav-group"><div class="nav-label">{escape(group)}</div>{links}</div>')
    return "".join(groups)


def render_page(page: str) -> str:
    title = PAGE_TITLES.get(page, page.title())
    return f"""<!doctype html>
<html lang="en" data-theme="dark">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover">
<meta name="theme-color" content="#090c12">
<title>LiteRT Agent · {escape(title)}</title>
<link rel="stylesheet" href="/static/css/style.css">
</head>
<body>
<div class="app-shell">
  <aside class="sidebar" id="sidebar">
    <div class="brand"><span class="brand-mark">L</span><div><strong>LiteRT Agent</strong><small>Autonomous Control Plane</small></div></div>
    <button class="mobile-close" onclick="toggleSidebar()">×</button>
    <nav class="nav">{_nav(page)}</nav>
    <div class="sidebar-footer"><span class="status-dot" id="side-dot"></span><span id="side-status">Connecting</span></div>
  </aside>
  <div class="app-main">
    <header class="topbar">
      <button class="icon-btn menu-btn" onclick="toggleSidebar()" aria-label="Open navigation">☰</button>
      <div class="breadcrumbs"><span>LiteRT Agent</span><b>/</b><strong>{escape(title)}</strong></div>
      <div class="top-actions">
        <span class="model-chip">● LiteRT-LM CLI</span>
        <button class="icon-btn" onclick="refreshPage()" title="Refresh">↻</button>
        <button class="icon-btn" onclick="toggleTheme()" title="Theme">◐</button>
      </div>
    </header>
    <main id="main" data-page="{escape(page)}">
      <div class="page-head"><div><div class="eyebrow">LOCAL · SELF-HOSTED · POLICY CONTROLLED</div><h1>{escape(title)}</h1></div><div id="page-actions"></div></div>
      <div id="toast-region" class="toast-region"></div>
      <section id="content"><div class="skeleton"></div><div class="skeleton short"></div></section>
    </main>
    <footer class="statusbar"><span>Local-first</span><span>·</span><span>LiteRT-LM only</span><span>·</span><span id="runtime-status">runtime connecting…</span><span class="grow"></span><span>v0.1.0</span></footer>
  </div>
</div>
<script src="/static/js/app.js"></script>
</body>
</html>"""
