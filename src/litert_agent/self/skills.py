"""Safe self-skill lifecycle: discover, propose, validate, approve, register."""
class SelfSkillManager:
    """Safe self-skill lifecycle with version history and quarantine."""
    def __init__(self, registry, validator, evolution):
        self.registry, self.validator, self.evolution = registry, validator, evolution
        self.proposals = {}
        self.versions = {}
        self.quarantined = set()

    def discover(self, task_description):
        return self.registry.recommend(task_description)

    def propose(self, name, description, tools, reason):
        skill = {"name": name, "description": description, "tools": tools, "source": "self", "version": "0.1.0"}
        ok, msg = self.validator.validate(skill)
        if not ok: raise ValueError(msg)
        proposal = self.evolution.propose("skill", reason, ["create:" + name])
        data = {"skill": skill, "proposal": proposal.__dict__, "status": "PROPOSED"}
        self.proposals[name] = data
        return data

    def validate(self, name):
        p = self.proposals.get(name)
        if not p: return False, "proposal not found"
        return self.validator.validate(p["skill"])

    def approve(self, name):
        p = self.proposals.get(name)
        if not p: raise KeyError(name)
        ok, msg = self.validate(name)
        if not ok: raise ValueError(msg)
        p["status"] = "APPROVED"
        return p

    def register(self, name):
        p = self.proposals.get(name)
        if not p or p.get("status") != "APPROVED": raise PermissionError("explicit approval required")
        self.registry.register(p["skill"])
        name = p["skill"]["name"]
        self.versions.setdefault(name, []).append(dict(p["skill"]))
        p["status"] = "REGISTERED"
        return p


    def version(self, name):
        return list(self.versions.get(name, []))

    def rollback(self, name):
        history = self.versions.get(name, [])
        if len(history) < 2:
            return False, "no previous version"
        history.pop()
        self.registry.register(dict(history[-1]))
        return True, dict(history[-1])

    def quarantine(self, name, reason="repeated skill failure"):
        if self.registry.find(name):
            self.registry.disable(name)
        self.quarantined.add(name)
        return {"name": name, "status": "QUARANTINED", "reason": reason}

    def restore(self, name):
        if name not in self.quarantined:
            return False
        self.quarantined.discard(name)
        self.registry.enable(name)
        return True
