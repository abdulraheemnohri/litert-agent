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

    def pop_curiosity(self):
        rows=self.db.execute_read(
            "SELECT id,topic,reason,priority,status,created_at FROM curiosity_queue "
            "WHERE status='PENDING' ORDER BY CASE priority WHEN 'CRITICAL' THEN 5 WHEN 'HIGH' THEN 4 WHEN 'NORMAL' THEN 3 WHEN 'LOW' THEN 2 ELSE 1 END DESC, created_at ASC LIMIT 1"
        )
        if not rows: return None
        r=rows[0]
        self.db.execute_write("UPDATE curiosity_queue SET status='CLAIMED' WHERE id=?",(r[0],))
        return {"id":r[0],"topic":r[1],"reason":r[2],"priority":r[3],"status":"CLAIMED","created_at":r[5]}

    def expire_stale(self, max_age_seconds: float = 2592000) -> int:
        cutoff=time.time()-max_age_seconds
        rows=self.db.execute_read("SELECT id FROM knowledge_expiry WHERE last_verified < ?",(cutoff,))
        for r in rows:
            self.db.execute_write("UPDATE knowledge_expiry SET status='STALE' WHERE id=?",(r[0],))
        return len(rows)
