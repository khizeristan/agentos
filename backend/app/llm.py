import os, re, json, httpx
HIGH = r"\b(buy|purchase|ready|start|sign up|enterprise|demo|urgent|asap|today|this week|upgrade)\b"
PRICE = r"\b(price|pricing|cost|quote|how much)\b"
SUPPORT = r"\b(broken|error|refund|not working|can't log|cannot|issue|bug|invoice problem)\b"
LOW = r"\b(browsing|maybe later|just curious|newsletter|no budget|not now)\b"
class DemoLLMProvider:
    name = "demo"
    def classify(self, lead):
        m = lead["message"].lower()
        urgent = "high" if re.search(r"\b(today|urgent|asap|this week)\b", m) else "medium" if re.search(PRICE + "|" + HIGH, m) else "low"
        if re.search(SUPPORT, m): return dict(intent="support_request", priority="medium", urgency=urgent, reason="Customer reports a problem that needs a human", recommended_action="escalate_human")
        if re.search(LOW, m): return dict(intent="low_intent", priority="low", urgency="low", reason="Casual interest, no buying signal", recommended_action="nurture")
        if re.search(HIGH, m): return dict(intent="high_purchase_intent", priority="high", urgency=urgent, reason="Explicit buying signal (" + re.search(HIGH, m).group(0) + ") with timing", recommended_action="send_followup")
        if re.search(PRICE, m): return dict(intent="price_inquiry", priority="medium", urgency=urgent, reason="Asked about pricing, no commitment yet", recommended_action="send_info")
        if len(m.split()) > 8: return dict(intent="product_question", priority="medium", urgency="low", reason="Asked a product question", recommended_action="send_info")
        return dict(intent="unclear", priority="low", urgency="low", reason="Message too vague to classify", recommended_action="escalate_human")
    def followup(self, lead):
        m = lead["message"].lower(); first = lead["name"].split()[0]
        topic = "enterprise plan" if "enterprise" in m else "demo" if "demo" in m else "upgrade" if "upgrade" in m else "pricing" if re.search(PRICE, m) else "your request"
        timing = "today" if re.search(r"today|urgent|asap", m) else "this week" if "this week" in m else "soon"
        return (f"Hi {first}, thanks for reaching out about {topic}" + (f" at {lead['company']}" if lead.get("company") else "") +
                f". I'd be happy to help with the details and setup. Since you're looking to move {timing}, would you like me to arrange a quick call {'today' if timing != 'soon' else 'this week'}?")
class QwenLLMProvider(DemoLLMProvider):
    name = "qwen"
    def _chat(self, prompt):
        r = httpx.post(os.environ["QWEN_API_URL"].rstrip("/") + "/chat/completions", timeout=60,
            headers={"Authorization": "Bearer " + os.environ.get("QWEN_API_KEY", "")},
            json={"model": os.getenv("QWEN_MODEL", "qwen2.5-7b-instruct"), "messages": [{"role": "user", "content": prompt}]})
        return r.json()["choices"][0]["message"]["content"]
    def classify(self, lead):
        from .agents.prompts import CLASSIFY
        try: return json.loads(re.search(r"\{.*\}", self._chat(CLASSIFY.format(**lead)), re.S).group(0))
        except Exception: return super().classify(lead)
    def followup(self, lead):
        from .agents.prompts import FOLLOWUP
        try: return self._chat(FOLLOWUP.format(**lead)).strip()
        except Exception: return super().followup(lead)
def get_llm():
    return DemoLLMProvider() if os.getenv("DEMO_MODE", "true").lower() == "true" or not os.getenv("QWEN_API_URL") else QwenLLMProvider()
