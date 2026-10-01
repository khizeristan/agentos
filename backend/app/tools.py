"""Tool registry: every tool has a Pydantic schema; the LLM never touches the DB directly."""
import datetime as dt
from pydantic import BaseModel
from .models import Lead, row, now
from .llm import get_llm
class NoArgs(BaseModel): pass
class UpdateLead(BaseModel):
    lead_id: str; fields: dict
class LeadIn(BaseModel): lead_id: str
class Send(BaseModel):
    to: str; body: str
class Query(BaseModel): query: str = ""
ALLOWED = {"status", "intent", "priority", "urgency", "reason", "recommended_action", "last_contact"}
def crm_get_today_leads(s, a): return [row(l) for l in s.query(Lead).all()]
def crm_update_lead(s, a):
    l = s.get(Lead, a.lead_id)
    for k, v in a.fields.items():
        if k in ALLOWED: setattr(l, k, v)
    s.commit(); return {"ok": True}
def generate_followup(s, a): return get_llm().followup(row(s.get(Lead, a.lead_id)))
def send_whatsapp_message(s, a): return {"ok": True, "simulated": True, "channel": "whatsapp", "to": a.to}
def send_email(s, a): return {"ok": True, "simulated": True, "channel": "email", "to": a.to}
def get_calendar_events(s, a): return [{"title": "Sales sync", "time": "15:00"}, {"title": "Demo call slot", "time": "17:30"}]
def search_documents(s, a): return [{"doc": "pricing.md", "snippet": "Enterprise: custom pricing, onboarding in 3 days"}]
def browser_action(s, a): return {"ok": False, "detail": "Playwright placeholder - disabled in MVP"}
REGISTRY = {"crm_get_today_leads": (NoArgs, crm_get_today_leads), "crm_update_lead": (UpdateLead, crm_update_lead),
  "generate_followup": (LeadIn, generate_followup), "send_whatsapp_message": (Send, send_whatsapp_message),
  "send_email": (Send, send_email), "get_calendar_events": (NoArgs, get_calendar_events),
  "search_documents": (Query, search_documents), "browser_action": (Query, browser_action)}
def call(name, s, **kw):
    schema, fn = REGISTRY[name]; return fn(s, schema(**kw))
