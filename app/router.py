"""AI router: classifies a question BEFORE any retrieval.

Hard safety rules (regex) decide risk and blocking. The language model only decides the query type.
Rules always win: the model can never lower a risk or un-block a request that the rules flagged.

NOTE: the risk levels are a "Portfolio demonstration risk classification", not a certified framework.
"""
import json
import re
from dataclasses import dataclass, field

from app import llm

QUERY_TYPES = ("INCIDENT", "KNOWLEDGE", "GENERAL", "OUT_OF_SCOPE")
RISK_ORDER = ["LOW", "MEDIUM", "HIGH", "CRITICAL"]

# ---- hard rules ------------------------------------------------------------------------------
INJECTION = re.compile(
    r"(ignore|disregard|forget|override)\b.{0,40}\b(instruction|prompt|rule|polic|guideline)"
    r"|(reveal|show|print|repeat|leak|tell me)\b.{0,40}\b(system prompt|hidden (instruction|prompt)|your (instruction|prompt|rules))"
    r"|\b(developer|debug|god) mode\b|\bjailbreak\b|\bpretend (you are|to be)\b|\byou are now\b",
    re.I,
)
CREDENTIAL_REQUEST = re.compile(
    r"\b(give|share|show|tell|reveal|send|provide|what('s| is))\b.{0,40}"
    r"\b(password|passcode|credential|api key|access key|secret|recovery key|token)s?\b"
    r"(?!.{0,40}\b(polic|reset|procedure|requirement|rule))",
    re.I,
)
BYPASS = re.compile(
    r"\b(bypass|circumvent|evade|get around|work around|defeat)\b.{0,50}\b(security|control|mfa|firewall|authentication|login|antivirus|logging|monitoring|polic)",
    re.I,
)
DISABLE_SECURITY = re.compile(
    r"\b(disable|turn off|switch off|deactivate|remove|stop)\b.{0,50}\b(security|firewall|mfa|multi-factor|antivirus|endpoint protection|logging|monitoring|audit)",
    re.I,
)
PRODUCTION_CHANGE = re.compile(
    r"\b(restart|reboot|shut ?down|delete|drop|wipe|kill|terminate|roll ?back|fail ?over|restore)\b.{0,50}\b(production|prod|live|server|database|cluster)",
    re.I,
)
SENSITIVE_IN_INPUT = re.compile(
    r"(password|passwd|pwd|secret|token|api[ _-]?key)\s*(is|=|:)\s*\S+|AccountKey=|BEGIN [A-Z ]*PRIVATE KEY|\b[A-Za-z0-9]{32,}\b",
    re.I,
)

# Questions that refer to the company's own knowledge, systems or incidents are enterprise-specific, never GENERAL.
ENTERPRISE_REF = re.compile(
    r"\b(your|the|our|this|company'?s?|enterprise|organi[sz]ation'?s?)\s+(knowledge[- ]?base|knowledge|runbook|policy|policies|incident|incidents|documentation|docs)\b"
    r"|\b(our|my company'?s?|the company'?s?)\b",
    re.I,
)

TYPE_PROMPT = """Classify the user's message into exactly one query type for an enterprise IT assistant.
- INCIDENT: something is broken, failing or degraded right now and the user wants help troubleshooting it.
- KNOWLEDGE: a question about an IT policy, procedure, standard or how something is normally done at the company.
- GENERAL: a general IT or technology concept question not specific to the company (e.g. "explain cloud computing").
- OUT_OF_SCOPE: anything that is not about IT or technology (cooking, sport, jokes, etc.).
Reply with JSON only: {"query_type": "INCIDENT|KNOWLEDGE|GENERAL|OUT_OF_SCOPE"}"""


@dataclass
class RouteDecision:
    query_type: str
    risk_level: str = "LOW"
    human_review_required: bool = False
    blocked: bool = False
    safety_flags: list[str] = field(default_factory=list)
    reasons: list[str] = field(default_factory=list)
    tokens: int = 0


def _raise_risk(current: str, new: str) -> str:
    return new if RISK_ORDER.index(new) > RISK_ORDER.index(current) else current


def _llm_query_type(question: str) -> tuple[str, int]:
    try:
        r = llm.chat(
            [{"role": "system", "content": TYPE_PROMPT}, {"role": "user", "content": question}],
            temperature=0,
            json_mode=True,
        )
        qt = str(json.loads(r["text"]).get("query_type", "")).upper()
        return (qt if qt in QUERY_TYPES else "GENERAL"), r["tokens"]
    except (llm.LLMError, ValueError):
        # If the model is unavailable, fall back safely: treat as a company question so retrieval decides.
        return "KNOWLEDGE", 0


def apply_rules(question: str) -> RouteDecision:
    """Deterministic safety rules only (no model call). Sets risk, flags and blocking."""
    d = RouteDecision(query_type="GENERAL")
    q = question.strip()

    if INJECTION.search(q):
        d.safety_flags.append("PROMPT_INJECTION")
        d.risk_level = _raise_risk(d.risk_level, "HIGH")
        d.blocked = True
        d.reasons.append("Attempt to override or reveal system instructions.")
    if CREDENTIAL_REQUEST.search(q):
        d.safety_flags.append("CREDENTIAL_REQUEST")
        d.risk_level = _raise_risk(d.risk_level, "HIGH")
        d.blocked = True
        d.reasons.append("Request for passwords, keys or other credentials.")
    if BYPASS.search(q):
        d.safety_flags.append("SECURITY_BYPASS")
        d.risk_level = _raise_risk(d.risk_level, "CRITICAL")
        d.blocked = True
        d.reasons.append("Request to bypass enterprise security controls.")
    elif DISABLE_SECURITY.search(q):
        d.safety_flags.append("SECURITY_CONTROL_CHANGE")
        d.risk_level = _raise_risk(d.risk_level, "HIGH")
        d.reasons.append("Proposes disabling a security control.")
    if PRODUCTION_CHANGE.search(q):
        d.safety_flags.append("PRODUCTION_CHANGE")
        d.risk_level = _raise_risk(d.risk_level, "MEDIUM")
        d.reasons.append("Asks about a consequential change to a production system.")
    if SENSITIVE_IN_INPUT.search(q):
        d.safety_flags.append("SENSITIVE_DATA_IN_INPUT")
        d.risk_level = _raise_risk(d.risk_level, "MEDIUM")
        d.reasons.append("Message appears to contain a credential or secret.")

    return d


def route(question: str) -> RouteDecision:
    q = question.strip()
    d = apply_rules(q)

    # Query type: skip the model call for requests we will refuse anyway.
    if d.blocked:
        d.query_type = "OUT_OF_SCOPE"
    else:
        d.query_type, d.tokens = _llm_query_type(q)
        if d.query_type == "GENERAL" and ENTERPRISE_REF.search(q):
            d.query_type = "KNOWLEDGE"  # refers to the company's own material -> must pass the grounding gate
            d.reasons.append("Refers to enterprise knowledge, so it cannot be answered from general knowledge.")

    d.human_review_required = RISK_ORDER.index(d.risk_level) >= RISK_ORDER.index("MEDIUM")
    return d
