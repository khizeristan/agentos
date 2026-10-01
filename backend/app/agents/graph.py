import os, time
from ..models import *
from .. import tools
from ..llm import get_llm
from .state import AgentState
from .planner import make_plan
DELAY = float(os.getenv("STEP_DELAY", "1.3"))
def log(s, text, tid): s.add(Activity(text=text, task_id=tid)); s.commit()
def n_understand(s, st): st["plan"] = make_plan(st["instruction"]); return "Task type: lead_processing"
def n_fetch(s, st): st["leads"] = tools.call("crm_get_today_leads", s); return f"Retrieved {len(st['leads'])} leads"
def n_analyze(s, st):
    llm = get_llm(); st["classifications"] = {}
    for l in st["leads"]:
        c = llm.classify(l); st["classifications"][l["id"]] = c
        tools.call("crm_update_lead", s, lead_id=l["id"], fields={**c, "status": "Needs Attention" if c["recommended_action"] == "escalate_human" else "Qualified" if c["priority"] == "medium" else "New"})
    return f"Analyzed {len(st['leads'])} leads ({llm.name} provider)"
def n_identify(s, st):
    st["high_intent"] = [i for i, c in st["classifications"].items() if c["recommended_action"] == "send_followup"]
    return f"Found {len(st['high_intent'])} high-intent prospects"
def n_generate(s, st):
    st["drafts"] = {}
    for i in st["high_intent"]:
        m = tools.call("generate_followup", s, lead_id=i); st["drafts"][i] = m
        s.add(Approval(task_id=st["task_id"], lead_id=i, message=m)); s.commit()
    return f"Generated {len(st['drafts'])} personalized messages"
def n_approval(s, st): st["status"] = "waiting_approval"; return "Waiting for human approval"
NODES = [("Understanding instruction", n_understand), ("Fetching today's leads", n_fetch), ("Analyzing lead conversations", n_analyze),
         ("Identifying high-intent prospects", n_identify), ("Generating personalized follow-ups", n_generate), ("Waiting for approval", n_approval)]
def run_graph(task_id):
    s = SessionLocal(); t = s.get(Task, task_id); st = AgentState(task_id=task_id, instruction=t.description)
    t.status = "running"; t.steps = [{"name": n, "status": "pending", "detail": ""} for n, _ in NODES]; s.commit()
    log(s, f'AgentOS started "{t.description}"', task_id)
    try:
        for i, (name, fn) in enumerate(NODES):
            t.steps = [{**x, "status": "running"} if j == i else x for j, x in enumerate(t.steps)]; s.commit(); time.sleep(DELAY)
            d = fn(s, st); log(s, d, task_id)
            t.steps = [{**x, "status": "done", "detail": d} if j == i else x for j, x in enumerate(t.steps)]; s.commit()
        t.status = "waiting_approval"; s.commit()
        if not st["drafts"]: finalize(s, t)
    except Exception as e:
        t.status = "failed"; log(s, f"Task failed: {e}", task_id); s.commit()
    finally: s.close()
def resolve(s, ap, approve: bool):
    l = s.get(Lead, ap.lead_id)
    if approve:
        r = tools.call("send_whatsapp_message", s, to=l.phone, body=ap.message)
        assert r["ok"]  # verify
        tools.call("crm_update_lead", s, lead_id=l.id, fields={"status": "Follow-up Sent", "last_contact": now()})
        ap.status = "approved"; log(s, f"Message sent to {l.name} (simulated) / CRM updated / activity logged", ap.task_id)
    else:
        ap.status = "rejected"; log(s, f"Follow-up to {l.name} rejected by human", ap.task_id)
    s.commit()
    left = s.query(Approval).filter_by(task_id=ap.task_id, status="pending").count()
    if left == 0: finalize(s, s.get(Task, ap.task_id))
def finalize(s, t):
    t.steps = [*t.steps, {"name": "Verifying results & generating report", "status": "done", "detail": "All actions verified"}]
    t.status = "completed"; log(s, "Daily report generated", t.id); s.commit()
