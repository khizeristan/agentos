import os, threading, jwt, hashlib, datetime as dt
from fastapi import FastAPI, Depends, HTTPException, Header
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel
from .models import *
from .seed import seed, hp
from .agents.graph import run_graph, resolve
SECRET = os.getenv("JWT_SECRET", "dev-secret-change-me")
app = FastAPI(title="AgentOS")
Base.metadata.create_all(engine)
with SessionLocal() as _s: seed(_s)
def db():
    s = SessionLocal()
    try: yield s
    finally: s.close()
def user(authorization: str = Header(None)):
    try: return jwt.decode((authorization or "").replace("Bearer ", ""), SECRET, algorithms=["HS256"])
    except Exception: raise HTTPException(401, "Not authenticated")
class Login(BaseModel): email: str; password: str
class Run(BaseModel): instruction: str = "Process today's leads"
class Edit(BaseModel): message: str
@app.get("/api/health")
def health(): return {"status": "ok", "demo_mode": os.getenv("DEMO_MODE", "true")}
@app.post("/api/auth/login")
def login(b: Login, s=Depends(db)):
    u = s.query(User).filter_by(email=b.email).first()
    if not u or u.password_hash != hp(b.password): raise HTTPException(401, "Invalid credentials")
    return {"token": jwt.encode({"sub": u.email, "role": u.role, "exp": dt.datetime.utcnow() + dt.timedelta(hours=12)}, SECRET), "role": u.role}
@app.post("/api/agent/run")
def run(b: Run, u=Depends(user), s=Depends(db)):
    for l in s.query(Lead).all(): l.status, l.intent, l.priority, l.urgency = "New", None, None, None
    s.query(Approval).delete(); s.commit()
    t = Task(id=f"TASK-{s.query(Task).count()+1:03d}", type="lead_processing", description=b.instruction, status="queued", steps=[]); s.add(t); s.commit()
    threading.Thread(target=run_graph, args=(t.id,), daemon=True).start(); return row(t)
@app.get("/api/agent/tasks")
def tasks(u=Depends(user), s=Depends(db)): return [row(t) for t in s.query(Task).order_by(Task.created_at.desc())]
@app.get("/api/leads")
def leads(u=Depends(user), s=Depends(db)): return [row(l) for l in s.query(Lead).order_by(Lead.id)]
@app.get("/api/leads/{id}")
def lead(id: str, u=Depends(user), s=Depends(db)):
    l = s.get(Lead, id)
    if not l: raise HTTPException(404)
    return row(l)
def apx(a, s): return {**row(a), "lead": row(s.get(Lead, a.lead_id))}
@app.get("/api/approvals")
def approvals(u=Depends(user), s=Depends(db)): return [apx(a, s) for a in s.query(Approval).order_by(Approval.id)]
def act(id, s, u, ok):
    if u.get("role") != "admin": raise HTTPException(403, "Insufficient role")
    a = s.get(Approval, id)
    if not a or a.status != "pending": raise HTTPException(400, "Not pending")
    resolve(s, a, ok); return apx(a, s)
@app.post("/api/approvals/{id}/approve")
def approve(id: int, u=Depends(user), s=Depends(db)): return act(id, s, u, True)
@app.post("/api/approvals/{id}/reject")
def reject(id: int, u=Depends(user), s=Depends(db)): return act(id, s, u, False)
@app.post("/api/approvals/{id}/edit")
def edit(id: int, b: Edit, u=Depends(user), s=Depends(db)):
    a = s.get(Approval, id)
    if not a or a.status != "pending": raise HTTPException(400, "Not pending")
    a.message = b.message; s.commit(); return apx(a, s)
@app.get("/api/reports/today")
def report(u=Depends(user), s=Depends(db)):
    L = s.query(Lead).all(); A = s.query(Approval).all(); c = lambda p: len([l for l in L if l.priority == p])
    return {"leads_processed": len([l for l in L if l.intent]), "high": c("high"), "medium": c("medium"), "low": c("low"),
      "followups_sent": len([a for a in A if a.status == "approved"]), "needs_attention": len([l for l in L if l.status == "Needs Attention"]),
      "high_priority_leads": [l.name for l in L if l.priority == "high"], "crm_updated": len([l for l in L if l.intent])}
@app.get("/api/activity")
def activity(u=Depends(user), s=Depends(db)): return [row(a) for a in s.query(Activity).order_by(Activity.id.desc()).limit(60)]
STATIC = os.path.join(os.path.dirname(__file__), "static")
@app.get("/")
def index(): return FileResponse(os.path.join(STATIC, "index.html"))
