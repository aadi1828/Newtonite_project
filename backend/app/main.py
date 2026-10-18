from datetime import datetime, timezone
from fastapi import FastAPI, Depends, HTTPException, Query, Header
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from sqlalchemy import or_, update
from sqlalchemy.exc import IntegrityError
from .config import settings
from .db import Base, engine, get_db
from .models import User, Team, Membership, WorkItem, Comment, ActivityEvent
from .schemas import LoginIn, ItemCreate, ItemUpdate, TransitionIn, CommentIn, ItemOut
from .security import verify_password, create_token, get_current_user, require_team, membership_for

app = FastAPI(title="Newtonite Operations API", version="1.0.0", description="Team-based operational work management.")
app.add_middleware(CORSMiddleware, allow_origins=[x.strip() for x in settings.cors_origins.split(",")], allow_credentials=True, allow_methods=["*"], allow_headers=["*"])

@app.on_event("startup")
def startup():
    Base.metadata.create_all(bind=engine)

@app.get("/health")
def health():
    return {"status": "ok"}

@app.post("/auth/login")
def login(payload: LoginIn, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == payload.email.lower()).first()
    if not user or not verify_password(payload.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Email or password is incorrect")
    return {"access_token": create_token(user), "token_type": "bearer", "user": {"id": user.id, "name": user.name, "email": user.email}}

@app.get("/auth/me")
def me(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    memberships = db.query(Membership).filter_by(user_id=user.id).all()
    return {"id": user.id, "name": user.name, "email": user.email, "teams": [{"team_id": m.team_id, "role": m.role} for m in memberships]}

@app.get("/teams")
def teams(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    memberships = db.query(Membership).filter_by(user_id=user.id).all()
    ids = [m.team_id for m in memberships]
    return [{"id": t.id, "name": t.name, "role": membership_for(db, user.id, t.id).role} for t in db.query(Team).filter(Team.id.in_(ids)).all()]

def visible_item(db: Session, user: User, item_id: int):
    item = db.get(WorkItem, item_id)
    if not item:
        raise HTTPException(status_code=404, detail="Work item not found")
    require_team(db, user, item.team_id)
    return item

def log_event(db, item, actor, action, old=None, new=None):
    db.add(ActivityEvent(work_item_id=item.id, actor_id=actor.id, action=action, old_value=None if old is None else str(old), new_value=None if new is None else str(new)))

@app.get("/dashboard/summary")
def dashboard_summary(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    ids = [m.team_id for m in db.query(Membership).filter_by(user_id=user.id).all()]
    items = db.query(WorkItem).filter(WorkItem.team_id.in_(ids))
    return {
        "total": items.filter(WorkItem.status.notin_([ "Closed", "Resolved" ])).count(),
        "urgent": items.filter(WorkItem.priority == "Urgent", WorkItem.status.notin_([ "Closed", "Resolved" ])).count(),
        "unassigned": items.filter(WorkItem.assignee_id.is_(None), WorkItem.status.notin_([ "Closed", "Resolved" ])).count(),
        "awaiting_approval": items.filter(WorkItem.status == "Awaiting Approval").count()
    }

@app.get("/work-items", response_model=list[ItemOut])
def list_items(q: str = "", status: str | None = None, priority: str | None = None, assignee: str | None = None, team_id: int | None = None, page: int = Query(1, ge=1), limit: int = Query(20, ge=1, le=100), db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    team_ids = [m.team_id for m in db.query(Membership).filter_by(user_id=user.id).all()]
    query = db.query(WorkItem).filter(WorkItem.team_id.in_(team_ids))
    if team_id:
        if team_id not in team_ids: raise HTTPException(status_code=403, detail="No access to this team")
        query = query.filter(WorkItem.team_id == team_id)
    if q.strip():
        needle = f"%{q.strip()}%"
        query = query.filter(or_(WorkItem.title.ilike(needle), WorkItem.description.ilike(needle)))
    if status: query = query.filter(WorkItem.status == status)
    if priority: query = query.filter(WorkItem.priority == priority)
    if assignee == "me": query = query.filter(WorkItem.assignee_id == user.id)
    elif assignee == "unassigned": query = query.filter(WorkItem.assignee_id.is_(None))
    return query.order_by(WorkItem.updated_at.desc(), WorkItem.id.desc()).offset((page-1)*limit).limit(limit).all()

@app.post("/work-items", response_model=ItemOut, status_code=201)
def create_item(payload: ItemCreate, idempotency_key: str | None = Header(default=None, alias="Idempotency-Key"), db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    require_team(db, user, payload.team_id, ["Admin", "Lead", "Member"])
    if payload.priority not in ["Low", "Medium", "High", "Urgent"]: raise HTTPException(422, "Invalid priority")
    if payload.item_type not in ["Incident", "Customer Issue", "Payment", "Compliance", "Task"]: raise HTTPException(422, "Invalid item type")
    if payload.assignee_id:
        target = db.get(User, payload.assignee_id)
        if not target or not membership_for(db, target.id, payload.team_id): raise HTTPException(422, "Assignee must belong to the selected team")
    item = WorkItem(**payload.model_dump(), created_by=user.id)
    db.add(item)
    try:
        db.flush()
        log_event(db, item, user, "created", new=item.title)
        db.commit(); db.refresh(item)
    except IntegrityError:
        db.rollback()
        raise HTTPException(409, "Could not create item due to a data conflict")
    # Idempotency-Key is accepted for API compatibility; persistent key storage is a known limitation.
    return item

@app.get("/work-items/{item_id}", response_model=ItemOut)
def get_item(item_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return visible_item(db, user, item_id)

@app.patch("/work-items/{item_id}", response_model=ItemOut)
def update_item(item_id: int, payload: ItemUpdate, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    item = visible_item(db, user, item_id)
    membership = require_team(db, user, item.team_id, ["Admin", "Lead", "Member"])
    if payload.version != item.version:
        raise HTTPException(409, detail={"message": "This item changed since you opened it. Reload and retry.", "current_version": item.version})
    changes = payload.model_dump(exclude_unset=True)
    changes.pop("version", None)
    if "priority" in changes and changes["priority"] not in ["Low", "Medium", "High", "Urgent"]: raise HTTPException(422, "Invalid priority")
    if "assignee_id" in changes and changes["assignee_id"] is not None:
        target = db.get(User, changes["assignee_id"])
        if not target or not membership_for(db, target.id, item.team_id): raise HTTPException(422, "Assignee must belong to the item's team")
    old_values = {k: getattr(item, k) for k in changes}
    result = db.query(WorkItem).filter(WorkItem.id == item.id, WorkItem.version == payload.version).update({**changes, "version": WorkItem.version + 1, "updated_at": datetime.now(timezone.utc)}, synchronize_session=False)
    if result != 1:
        db.rollback()
        raise HTTPException(409, detail="Item changed concurrently. Reload and retry.")
    for key, old in old_values.items():
        log_event(db, item, user, f"{key}_changed", old, changes[key])
    db.commit()
    db.refresh(item)
    return item

@app.post("/work-items/{item_id}/claim", response_model=ItemOut)
def claim_item(item_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    item = visible_item(db, user, item_id)
    require_team(db, user, item.team_id, ["Admin", "Lead", "Member"])
    result = db.query(WorkItem).filter(WorkItem.id == item.id, WorkItem.assignee_id.is_(None), WorkItem.status.notin_(["Resolved", "Closed"])).update({"assignee_id": user.id, "version": WorkItem.version + 1, "updated_at": datetime.now(timezone.utc)}, synchronize_session=False)
    if result != 1:
        db.rollback()
        raise HTTPException(409, detail="This item has already been claimed or is no longer claimable")
    log_event(db, item, user, "claimed", None, user.email)
    db.commit(); db.refresh(item)
    return item

TRANSITIONS = {
    "Open": {"In Progress"},
    "In Progress": {"Open", "Blocked", "Awaiting Approval"},
    "Blocked": {"In Progress"},
    "Awaiting Approval": {"In Progress", "Resolved"},
    "Resolved": {"Closed", "In Progress"},
    "Closed": set()
}

@app.post("/work-items/{item_id}/transition", response_model=ItemOut)
def transition_item(item_id: int, payload: TransitionIn, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    item = visible_item(db, user, item_id)
    membership = require_team(db, user, item.team_id, ["Admin", "Lead", "Member"])
    if payload.version != item.version: raise HTTPException(409, detail="This item changed. Reload before changing status.")
    if payload.status not in TRANSITIONS.get(item.status, set()): raise HTTPException(422, detail=f"Transition {item.status} → {payload.status} is not allowed")
    if item.status == "Awaiting Approval" and payload.status == "Resolved" and membership.role not in ["Admin", "Lead"]:
        raise HTTPException(403, detail="Only a Lead or Admin can approve this item")
    old = item.status
    result = db.query(WorkItem).filter(WorkItem.id == item.id, WorkItem.version == payload.version).update({"status": payload.status, "version": WorkItem.version + 1, "updated_at": datetime.now(timezone.utc)}, synchronize_session=False)
    if result != 1:
        db.rollback(); raise HTTPException(409, detail="Item changed concurrently. Reload and retry.")
    log_event(db, item, user, "status_changed", old, payload.status)
    db.commit(); db.refresh(item)
    return item

@app.post("/work-items/{item_id}/comments", status_code=201)
def add_comment(item_id: int, payload: CommentIn, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    item = visible_item(db, user, item_id)
    db.add(Comment(work_item_id=item.id, author_id=user.id, body=payload.body.strip()))
    log_event(db, item, user, "comment_added", new=payload.body.strip()[:200])
    db.commit()
    return {"ok": True}

@app.get("/work-items/{item_id}/comments")
def list_comments(item_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    visible_item(db, user, item_id)
    rows = db.query(Comment).filter_by(work_item_id=item_id).order_by(Comment.created_at.asc()).all()
    return [{"id": r.id, "author_id": r.author_id, "body": r.body, "created_at": r.created_at} for r in rows]

@app.get("/work-items/{item_id}/activity")
def list_activity(item_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    visible_item(db, user, item_id)
    rows = db.query(ActivityEvent).filter_by(work_item_id=item_id).order_by(ActivityEvent.created_at.desc(), ActivityEvent.id.desc()).limit(100).all()
    return [{"id": r.id, "actor_id": r.actor_id, "action": r.action, "old_value": r.old_value, "new_value": r.new_value, "created_at": r.created_at} for r in rows]
