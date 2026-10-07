"""Built-in skills shipped with the agent."""

BUILTIN_SKILLS = [
    {
        "name": "coding",
        "description": "Write, extend and refactor code following project conventions.",
        "version": "1.0.0",
        "tools": ["filesystem", "terminal", "git", "python"],
    },
    {
        "name": "debugging",
        "description": "Diagnose failures, trace root causes and apply minimal fixes.",
        "version": "1.0.0",
        "tools": ["terminal", "filesystem", "python"],
    },
    {
        "name": "research",
        "description": "Gather sources, extract findings and record research memory.",
        "version": "1.0.0",
        "tools": ["http", "browser", "search"],
    },
    {
        "name": "git",
        "description": "Branching, commits, diffs and checkpointing before changes.",
        "version": "1.0.0",
        "tools": ["git", "filesystem"],
    },
    {
        "name": "filesystem",
        "description": "Safe file operations within allowed roots.",
        "version": "1.0.0",
        "tools": ["filesystem"],
    },
    {
        "name": "terminal",
        "description": "Run shell commands with timeouts and output limits.",
        "version": "1.0.0",
        "tools": ["terminal"],
    },
    {
        "name": "system-diagnostics",
        "description": "Inspect OS, resources and LiteRT-LM availability.",
        "version": "1.0.0",
        "tools": ["terminal"],
    },
    {
        "name": "documentation",
        "description": "Write and update project documentation.",
        "version": "1.0.0",
        "tools": ["filesystem"],
    },
    {
        "name": "testing",
        "description": "Run test suites, interpret failures and verify fixes.",
        "version": "1.0.0",
        "tools": ["terminal", "python"],
    },
    {
        "name": "project-bootstrap",
        "description": "Scaffold new projects with sane defaults.",
        "version": "1.0.0",
        "tools": ["filesystem", "git", "terminal"],
    },
]
