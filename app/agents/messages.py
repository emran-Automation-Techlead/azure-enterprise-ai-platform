"""Structured messages exchanged between agents. Agents never pass free text to each other, only these models.

Every agent returns an AgentMessage, so the orchestrator, the reviewer and the UI trace all read the same shape.
"""
from typing import Literal

from pydantic import BaseModel, Field

QueryType = Literal["INCIDENT", "KNOWLEDGE", "GENERAL", "OUT_OF_SCOPE"]
Status = Literal["success", "no_knowledge", "refused", "error"]
RiskLevel = Literal["LOW", "MEDIUM", "HIGH", "CRITICAL"]
AnswerKind = Literal["ENTERPRISE_GROUNDED_RESPONSE", "GENERAL_AI_RESPONSE", "NO_RELEVANT_KNOWLEDGE", "REFUSAL"]


class SourceRef(BaseModel):
    id: str
    title: str
    category: str = ""
    relevance: float = 0.0


class Finding(BaseModel):
    """One statement an agent makes, labelled by how much we know."""
    text: str
    basis: Literal["KNOWN_FROM_SOURCES", "INFERENCE", "UNKNOWN"]
    source_ids: list[str] = []


class AgentMessage(BaseModel):
    agent: str                              # orchestrator | incident_agent | knowledge_agent | general_agent
    status: Status
    query_type: QueryType
    answer_kind: AnswerKind
    summary: str = ""                       # short human-readable result of this agent
    findings: list[Finding] = []
    sources: list[SourceRef] = []
    grounded: bool = False
    grounding_score: float = 0.0
    conflict_detected: bool = False
    tokens: int = 0


class OrchestratorPlan(BaseModel):
    query_types: list[QueryType]            # may hold more than one for a mixed request
    agents: list[str]                       # agents to run, in order
    risk_hint: RiskLevel = "LOW"            # from hard rules; the reviewer can only raise it
    blocked: bool = False
    safety_flags: list[str] = []
    reasons: list[str] = []
    tokens: int = 0


class ReviewVerdict(BaseModel):
    """Output of the Responsible AI Review Agent (concise reasons only, no chain-of-thought)."""
    grounded: bool
    risk_level: RiskLevel
    safety_flags: list[str] = []
    privacy_flags: list[str] = []
    unsupported_claims: list[str] = []
    human_review_required: bool
    human_review_reasons: list[str] = []
    approved: bool
    blocked: bool = False                   # stopped by deterministic rules; no answer should be shown
    reason: str = ""
    tokens: int = 0


class TraceStep(BaseModel):
    """What the UI shows: name, status, purpose, high-level result. Never reasoning."""
    agent: str
    status: str
    purpose: str
    result: str = ""


class AgentRunResult(BaseModel):
    plan: OrchestratorPlan
    messages: list[AgentMessage] = Field(default_factory=list)
    verdict: ReviewVerdict | None = None
    trace: list[TraceStep] = Field(default_factory=list)
