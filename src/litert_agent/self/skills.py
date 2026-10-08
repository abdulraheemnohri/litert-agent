"""Safe self-skill lifecycle with persistent version history and quarantine.

Self-generated skills never bypass security policy or approval.
"""
import json
import time


class SelfSkillManager:
    def __init__(self, registry, validator, evolution, db=None):
        self.registry, self.validator, self.evolution, self.db = registry, validator, evolution, db
        self.proposals = {}
        self.versions = {}
        self.quarantined = set()
        self._load_persistent_state()

    def _load_persistent_state(self):
        if not self.db:
            return
        for row in self.db.execute_read(
            "SELECT skill_name,version,skill_json FROM self_skill_versions ORDER BY created_at"
        ):
            self.versions.setdefault(row[0], []).append(json.loads(row[2]))
        for row in self.db.execute_read("SELECT skill_name FROM self_skill_quarantine"):
            self.quarantined.add(row[0])
            if self.registry.find(row[0]):
                self.registry.disable(row[0])

    def discover(self, task_description):
        return self.registry.recommend(task_description)

    def propose(self, name, description, tools, reason):
        skill = {"name": name, "description": description, "tools": tools, "source": "self", "version": "0.1.0"}
        ok, msg = self.validator.validate(skill)
        if not ok:
            raise ValueError(msg)
        proposal = self.evolution.propose("skill", reason, ["create:" + name])
        data = {"skill": skill, "proposal": proposal.__dict__, "status": "PROPOSED"}
        self.proposals[name] = data
        return data

    def validate(self, name):
        p = self.proposals.get(name)
        if not p:
            return False, "proposal not found"
        return self.validator.validate(p["skill"])

    def approve(self, name):
        p = self.proposals.get(name)
        if not p:
            raise KeyError(name)
        ok, msg = self.validate(name)
        if not ok:
            raise ValueError(msg)
        p["status"] = "APPROVED"
        return p

    def register(self, name):
        p = self.proposals.get(name)
        if not p or p.get("status") != "APPROVED":
            raise PermissionError("explicit approval required")
        self.registry.register(p["skill"])
        skill = dict(p["skill"])
        self.versions.setdefault(name, []).append(skill)
        if self.db:
            self.db.execute_write(
                "UPDATE self_skill_versions SET active=0 WHERE skill_name=?", (name,)
            )
            self.db.execute_write(
                "INSERT INTO self_skill_versions (id,skill_name,version,skill_json,created_at,active) "
                "VALUES (?,?,?,?,?,1)",
                (f"{name}:{skill.get('version','0.1.0')}:{time.time_ns()}",
                 name, skill.get("version","0.1.0"), json.dumps(skill, sort_keys=True), time.time()),
            )
        p["status"] = "REGISTERED"
        return p

    def version(self, name):
        return list(self.versions.get(name, []))

    def rollback(self, name):
        history = self.versions.get(name, [])
        if len(history) < 2:
            return False, "no previous version"
        history.pop()
        previous = dict(history[-1])
        self.registry.register(previous)
        if self.db:
            self.db.execute_write("UPDATE self_skill_versions SET active=0 WHERE skill_name=?", (name,))
            self.db.execute_write(
                "INSERT INTO self_skill_versions (id,skill_name,version,skill_json,created_at,active) "
                "VALUES (?,?,?,?,?,1)",
                (f"{name}:{previous.get('version','0.0.0')}:{time.time_ns()}",
                 name, previous.get("version","0.0.0"), json.dumps(previous, sort_keys=True), time.time()),
            )
        return True, previous

    def quarantine(self, name, reason="repeated skill failure"):
        if self.registry.find(name):
            self.registry.disable(name)
        self.quarantined.add(name)
        if self.db:
            self.db.execute_write(
                "INSERT OR REPLACE INTO self_skill_quarantine (skill_name,reason,created_at) VALUES (?,?,?)",
                (name, reason[:2000], time.time()),
            )
        return {"name": name, "status": "QUARANTINED", "reason": reason}

    def restore(self, name):
        if name not in self.quarantined:
            return False
        self.quarantined.discard(name)
        self.registry.enable(name)
        if self.db:
            self.db.execute_write("DELETE FROM self_skill_quarantine WHERE skill_name=?", (name,))
        return True
