from typing import TypedDict, List, Dict, Any
class AgentState(TypedDict, total=False):
    task_id: str; instruction: str; plan: List[str]; leads: List[Dict[str, Any]]
    classifications: Dict[str, Dict[str, Any]]; high_intent: List[str]; drafts: Dict[str, str]; status: str
