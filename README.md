# AgentOS - AI Employee for Small Businesses
Workflow: "Process today's leads" -> fetch, classify, draft follow-ups, human approval, simulated send, CRM update, report.
## Run
`docker compose up --build` -> http://localhost:8000  (or `cd backend && pip install -r requirements.txt && uvicorn app.main:app`)
Demo login: demo@agentos.ai / AgentOS-Demo-2026
## Use
Dashboard -> Run Agent -> Approvals (approve/edit/reject) -> Reports.
## Qwen
Set `DEMO_MODE=false`, `QWEN_API_URL` (OpenAI-compatible) and `QWEN_API_KEY`. Falls back to demo logic on errors.
## Deploy (Render)
Push to GitHub -> Render > New > Blueprint -> select repo (uses render.yaml). Optionally add a Render Postgres and set `DATABASE_URL`.
## Not in MVP
Next.js UI, LangGraph library, Celery/Redis, Qdrant, Whisper, Playwright (tool interfaces/placeholders only). See docs/architecture.mmd.
