from sqlalchemy.orm import Session
from .db import Base, engine, SessionLocal
from .models import User, Team, Membership, WorkItem, ActivityEvent
from .security import hash_password

DEMO_PASSWORD = "NewtoniteDemo!2026"

def seed():
    Base.metadata.create_all(bind=engine)
    db: Session = SessionLocal()
    try:
        if db.query(User).filter_by(email="admin@newtonite.local").first():
            return
        ops = Team(name="Operations")
        eng = Team(name="Engineering")
        compliance = Team(name="Compliance")
        db.add_all([ops, eng, compliance]); db.flush()
        people = [
            ("Avery Admin", "admin@newtonite.local", ["Admin"], [ops, eng, compliance]),
            ("Jordan Lead", "lead@newtonite.local", ["Lead"], [ops]),
            ("Morgan Member", "member@newtonite.local", ["Member"], [ops]),
            ("Taylor Viewer", "viewer@newtonite.local", ["Viewer"], [ops]),
            ("Casey Engineer", "engineer@newtonite.local", ["Member"], [eng]),
            ("Riley Outsider", "outsider@newtonite.local", ["Member"], [compliance]),
        ]
        users = {}
        for name, email, roles, teams in people:
            user = User(name=name, email=email, password_hash=hash_password(DEMO_PASSWORD))
            db.add(user); db.flush(); users[email] = user
            for team in teams:
                role = "Admin" if email.startswith("admin") else ("Lead" if email.startswith("lead") else ("Viewer" if email.startswith("viewer") else "Member"))
                db.add(Membership(user_id=user.id, team_id=team.id, role=role))
        db.flush()
        examples = [
            ("Investigate failed payment retries", "Several payments have entered retry state and need reconciliation.", "Payment", "Urgent", "Open", ops, users["member@newtonite.local"]),
            ("Customer cannot access account", "Review authentication events and confirm account recovery path.", "Customer Issue", "High", "In Progress", ops, users["lead@newtonite.local"]),
            ("Review production alert threshold", "Investigate noisy alert and propose a safe threshold adjustment.", "Incident", "High", "Awaiting Approval", eng, users["engineer@newtonite.local"]),
            ("Quarterly access review", "Confirm access for the compliance workspace.", "Compliance", "Medium", "Open", compliance, None),
            ("Update operational runbook", "Document the recovery procedure and escalation owner.", "Task", "Low", "Resolved", ops, users["member@newtonite.local"]),
        ]
        for title, desc, typ, pri, status, team, assignee in examples:
            item = WorkItem(title=title, description=desc, item_type=typ, priority=pri, status=status, team_id=team.id, assignee_id=assignee.id if assignee else None, created_by=users["admin@newtonite.local"].id)
            db.add(item); db.flush()
            db.add(ActivityEvent(work_item_id=item.id, actor_id=item.created_by, action="created", new_value=title))
        db.commit()
    finally:
        db.close()

if __name__ == "__main__":
    seed()
