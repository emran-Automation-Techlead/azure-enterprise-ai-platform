"""Orchestrator Agent: understands the request and decides WHICH agents run. It never answers anything itself.

Input : the (already redacted) user question
Output: OrchestratorPlan (query types, ordered agent list, risk hint, blocked flag)
Tools : router.apply_rules (deterministic safety rules) + one model call that classifies the request
Failure: if the model is unavailable it falls back to the knowledge agent, so retrieval and the grounding gate decide
Bounds: cannot lower a risk or un-block a request the hard rules flagged; cannot invent enterprise knowledge
"""
import json

from app import llm, router
from app.agents.messages import OrchestratorPlan

SYSTEM_PROMPT = """You are the routing coordinator of an enterprise IT assistant. You do NOT answer the question.
Choose every query type the request needs (usually one, sometimes two):
- INCIDENT: something is broken or failing now and the user wants troubleshooting help.
- KNOWLEDGE: a question about a company IT policy, procedure, standard, or whether an action is allowed or safe.
- GENERAL: a general technology concept question not specific to the company.
- OUT_OF_SCOPE: not about IT or technology.
A message that reports a failure AND asks about a policy or whether an action is safe needs both INCIDENT and KNOWLEDGE.
Reply with JSON only: {"query_types": ["INCIDENT", "KNOWLEDGE"]}"""

AGENT_FOR = {"INCIDENT": "incident_agent", "KNOWLEDGE": "knowledge_agent", "GENERAL": "general_agent"}
ORDER = ["INCIDENT", "KNOWLEDGE", "GENERAL"]


def _classify(question: str) -> tuple[list[str], int]:
    try:
        r = llm.chat(
            [{"role": "system", "content": SYSTEM_PROMPT}, {"role": "user", "content": question}],
            temperature=0,
            json_mode=True,
        )
        raw = json.loads(r["text"]).get("query_types", [])
        types = [t for t in (str(x).upper() for x in raw) if t in router.QUERY_TYPES]
        return (types or ["GENERAL"]), r["tokens"]
    except (llm.LLMError, ValueError, AttributeError, TypeError):
        return ["KNOWLEDGE"], 0


def plan(question: str) -> OrchestratorPlan:
    rules = router.apply_rules(question)
    base = dict(risk_hint=rules.risk_level, safety_flags=list(rules.safety_flags), reasons=list(rules.reasons))

    if rules.blocked:  # fast path: no model call, no search, no worker agent
        return OrchestratorPlan(query_types=["OUT_OF_SCOPE"], agents=[], blocked=True, **base)

    types, tokens = _classify(question)
    if "OUT_OF_SCOPE" in types and len(types) > 1:
        types.remove("OUT_OF_SCOPE")
    if types == ["GENERAL"] and router.ENTERPRISE_REF.search(question):
        types = ["KNOWLEDGE"]  # it refers to the company's own material, so it must pass the grounding gate
        base["reasons"].append("Refers to enterprise knowledge, so it cannot be answered from general knowledge.")
    if "SECURITY_CONTROL_CHANGE" in rules.safety_flags and "KNOWLEDGE" not in types and types != ["OUT_OF_SCOPE"]:
        types.append("KNOWLEDGE")  # a proposal to weaken a control needs policy evidence
        base["reasons"].append("Security-control change: policy evidence is required.")

    types = [t for t in ORDER if t in types] or ["OUT_OF_SCOPE"]
    agents = [AGENT_FOR[t] for t in types if t in AGENT_FOR]
    return OrchestratorPlan(query_types=types, agents=agents, tokens=tokens, **base)
