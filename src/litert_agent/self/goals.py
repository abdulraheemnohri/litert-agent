"""Persistent bounded autonomous goals and curiosity queue."""
from __future__ import annotations

import time
import uuid


class GoalManager:
    PRIORITIES = {"CRITICAL": 5, "HIGH": 4, "NORMAL": 3, "LOW": 2, "BACKGROUND": 1}
    STATUSES = {"PENDING","ACTIVE","PAUSED","COMPLETED","FAILED","CANCELLED"}

    def __init__(self, db):
        self.db = db

    def create(self, title: str, description: str, priority: str = "NORMAL",
               parent_id: str | None = None, goal_type: str = "user") -> dict:
        priority = priority.upper()
        if priority not in self.PRIORITIES:
            raise ValueError("invalid priority")
        gid = str(uuid.uuid4())
        self.db.execute_write(
            "INSERT INTO self_goals (id,title,description,priority,status,parent_id,goal_type,progress,created_at) "
            "VALUES (?,?,?,?,?,?,?,?,?)",
            (gid,title[:300],description[:6000],priority,"PENDING",parent_id,goal_type,0.0,time.time()),
        )
        return self.get(gid)

    def get(self, goal_id: str):
        rows = self.db.execute_read(
            "SELECT id,title,description,priority,status,parent_id,goal_type,progress,created_at,updated_at "
            "FROM self_goals WHERE id=?", (goal_id,))
        if not rows: return None
        r=rows[0]
        return {"id":r[0],"title":r[1],"description":r[2],"priority":r[3],"status":r[4],
                "parent_id":r[5],"goal_type":r[6],"progress":r[7],"created_at":r[8],"updated_at":r[9]}

    def list(self, status: str | None = None, limit: int = 100):
        q="SELECT id,title,description,priority,status,parent_id,goal_type,progress,created_at,updated_at FROM self_goals"
        params=[]
        if status:
            q+=" WHERE status=?"; params.append(status)
        q+=" ORDER BY CASE priority WHEN 'CRITICAL' THEN 5 WHEN 'HIGH' THEN 4 WHEN 'NORMAL' THEN 3 WHEN 'LOW' THEN 2 ELSE 1 END DESC, created_at DESC LIMIT ?"
        params.append(limit)
        rows=self.db.execute_read(q,tuple(params))
        return [{"id":r[0],"title":r[1],"description":r[2],"priority":r[3],"status":r[4],
                 "parent_id":r[5],"goal_type":r[6],"progress":r[7],"created_at":r[8],"updated_at":r[9]} for r in rows]

    def add_dependency(self, goal_id: str, depends_on_goal_id: str):
        if goal_id == depends_on_goal_id:
            raise ValueError("goal cannot depend on itself")
        if not self.get(goal_id) or not self.get(depends_on_goal_id):
            raise KeyError("goal dependency target not found")
        self.db.execute_write(
            "INSERT OR IGNORE INTO goal_dependencies (goal_id,depends_on_goal_id) VALUES (?,?)",
            (goal_id, depends_on_goal_id),
        )
        return self.dependencies(goal_id)

    def dependencies(self, goal_id: str) -> list[dict]:
        rows = self.db.execute_read(
            "SELECT g.id,g.title,g.status,g.progress FROM goal_dependencies d "
            "JOIN self_goals g ON g.id=d.depends_on_goal_id WHERE d.goal_id=?",
            (goal_id,),
        )
        return [{"id":r[0],"title":r[1],"status":r[2],"progress":r[3]} for r in rows]

    def is_ready(self, goal_id: str) -> bool:
        goal = self.get(goal_id)
        if not goal:
            raise KeyError(goal_id)
        return all(d["status"] == "COMPLETED" for d in self.dependencies(goal_id))

    def update(self, goal_id: str, status: str | None = None, progress: float | None = None):
        if status and status not in self.STATUSES: raise ValueError("invalid status")
        if progress is not None: progress=max(0.0,min(1.0,float(progress)))
        current=self.get(goal_id)
        if not current: raise KeyError(goal_id)
        self.db.execute_write(
            "UPDATE self_goals SET status=?,progress=?,updated_at=? WHERE id=?",
            (status or current["status"], progress if progress is not None else current["progress"], time.time(), goal_id),
        )
        return self.get(goal_id)

    def enqueue_curiosity(self, topic: str, reason: str, priority: str = "LOW") -> dict:
        cid=str(uuid.uuid4())
        self.db.execute_write(
            "INSERT INTO curiosity_queue (id,topic,reason,priority,status,created_at) VALUES (?,?,?,?,?,?)",
            (cid,topic[:500],reason[:4000],priority.upper(),"PENDING",time.time()),
        )
        return {"id":cid,"topic":topic,"reason":reason,"priority":priority.upper(),"status":"PENDING"}

    def peek_curiosity(self):
        rows=self.db.execute_read(
            "SELECT id,topic,reason,priority,status,created_at FROM curiosity_queue "
            "WHERE status='PENDING' ORDER BY CASE priority WHEN 'CRITICAL' THEN 5 WHEN 'HIGH' THEN 4 WHEN 'NORMAL' THEN 3 WHEN 'LOW' THEN 2 ELSE 1 END DESC, created_at ASC LIMIT 1"
        )
        if not rows: return None
        r=rows[0]
        return {"id":r[0],"topic":r[1],"reason":r[2],"priority":r[3],"status":r[4],"created_at":r[5]}

    def pop_curiosity(self):
        rows=self.db.execute_read(
            "SELECT id,topic,reason,priority,status,created_at FROM curiosity_queue "
            "WHERE status='PENDING' ORDER BY CASE priority WHEN 'CRITICAL' THEN 5 WHEN 'HIGH' THEN 4 WHEN 'NORMAL' THEN 3 WHEN 'LOW' THEN 2 ELSE 1 END DESC, created_at ASC LIMIT 1"
        )
        if not rows: return None
        r=rows[0]
        self.db.execute_write("UPDATE curiosity_queue SET status='CLAIMED',claimed_at=? WHERE id=?",(time.time(),r[0]))
        return {"id":r[0],"topic":r[1],"reason":r[2],"priority":r[3],"status":"CLAIMED","created_at":r[5]}

    def expire_stale(self, max_age_seconds: float = 2592000) -> int:
        cutoff=time.time()-max_age_seconds
        rows=self.db.execute_read("SELECT id FROM knowledge_expiry WHERE last_verified < ?",(cutoff,))
        for r in rows:
            self.db.execute_write("UPDATE knowledge_expiry SET status='STALE' WHERE id=?",(r[0],))
        return len(rows)


    def complete_curiosity(self, curiosity_id: str) -> bool:
        self.db.execute_write(
            "UPDATE curiosity_queue SET status='COMPLETED',completed_at=? WHERE id=?",
            (time.time(), curiosity_id),
        )
        return True

    def generate_curiosity_from_stale(self, max_age_seconds: float = 2592000, limit: int = 10) -> int:
        stale = self.expire_stale(max_age_seconds)
        rows = self.db.execute_read(
            "SELECT memory_key FROM knowledge_expiry WHERE status='STALE' "
            "ORDER BY updated_at ASC LIMIT ?", (limit,)
        )
        created = 0
        for (topic,) in rows:
            exists = self.db.execute_read(
                "SELECT id FROM curiosity_queue WHERE topic=? AND status IN ('PENDING','CLAIMED') LIMIT 1",
                (topic,),
            )
            if not exists:
                self.enqueue_curiosity(topic, "Knowledge is stale and needs verification", "LOW")
                created += 1
        return created
