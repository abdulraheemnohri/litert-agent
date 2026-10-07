# Skills

## Built-in
coding, debugging, research, git, filesystem, terminal, system-diagnostics, documentation, testing, project-bootstrap.

## API
- `SkillLoader.load_all()` — built-ins + database skills
- `SkillRegistry` — register/unregister/find/enable/disable, usage + success-rate tracking, `recommend(task)`
- `SkillValidator.validate(skill)` — required fields, name format, allowed tools

New skills must pass validation before registration. Security policy always applies on top of skill tool calls.
