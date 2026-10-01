import os, datetime as dt
from sqlalchemy import create_engine, Column, Integer, String, JSON, DateTime, Text
from sqlalchemy.orm import declarative_base, sessionmaker
url = os.getenv("DATABASE_URL") or "sqlite:///./agentos.db"
if url.startswith("postgres://"): url = url.replace("postgres://", "postgresql://", 1)
engine = create_engine(url, connect_args={"check_same_thread": False} if url.startswith("sqlite") else {})
SessionLocal = sessionmaker(bind=engine)
Base = declarative_base()
now = lambda: dt.datetime.utcnow()
class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True); email = Column(String, unique=True)
    password_hash = Column(String); role = Column(String, default="admin")
class Lead(Base):
    __tablename__ = "leads"
    id = Column(String, primary_key=True); name = Column(String); email = Column(String); phone = Column(String)
    company = Column(String); source = Column(String); message = Column(Text); conversation_history = Column(JSON)
    created_at = Column(DateTime, default=now); last_contact = Column(DateTime); status = Column(String, default="New")
    intent = Column(String); priority = Column(String); urgency = Column(String); reason = Column(Text); recommended_action = Column(String)
class Task(Base):
    __tablename__ = "tasks"
    id = Column(String, primary_key=True); type = Column(String); description = Column(String)
    status = Column(String, default="queued"); steps = Column(JSON, default=list); created_at = Column(DateTime, default=now)
class Approval(Base):
    __tablename__ = "approvals"
    id = Column(Integer, primary_key=True); task_id = Column(String); lead_id = Column(String)
    channel = Column(String, default="whatsapp"); message = Column(Text); status = Column(String, default="pending")
class Activity(Base):
    __tablename__ = "activity"
    id = Column(Integer, primary_key=True); ts = Column(DateTime, default=now); text = Column(String); task_id = Column(String)
def row(o): return {c.name: (getattr(o, c.name).isoformat() if isinstance(getattr(o, c.name), dt.datetime) else getattr(o, c.name)) for c in o.__table__.columns}
