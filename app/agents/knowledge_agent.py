"""Knowledge / RAG Agent: answers enterprise knowledge questions from retrieved documents only.

Input : the (already redacted) question
Output: AgentMessage with source IDs and titles, or NO_RELEVANT_KNOWLEDGE
Tools : the existing RAG pipeline (hybrid Azure AI Search, grounding gate, Azure OpenAI, citation check)
Failure: a search or model outage returns status "error" instead of raising, so the other agents can still report
Bounds: never answers from general knowledge; never invents a document
"""
import logging

from app import rag
from app.agents.messages import AgentMessage, Finding, SourceRef
from app.llm import LLMError
from app.search import SearchError

NAME = "knowledge_agent"
log = logging.getLogger(NAME)


def run(question: str) -> AgentMessage:
    try:
        r = rag.answer(question)
    except (SearchError, LLMError) as exc:
        log.warning("knowledge agent failed: %s (cause: %s)", type(exc).__name__, type(exc.__cause__).__name__)
        return AgentMessage(
            agent=NAME, status="error", query_type="KNOWLEDGE", answer_kind="NO_RELEVANT_KNOWLEDGE",
            summary="The knowledge search was unavailable.",
            findings=[Finding(text="The knowledge base could not be reached, so nothing is known from sources.", basis="UNKNOWN")],
        )

    if not r.grounded:
        return AgentMessage(
            agent=NAME, status="no_knowledge", query_type="KNOWLEDGE", answer_kind="NO_RELEVANT_KNOWLEDGE",
            summary="NO_RELEVANT_KNOWLEDGE", grounding_score=r.grounding_score, tokens=r.tokens,
            findings=[Finding(text=r.answer, basis="UNKNOWN")],
        )

    sources = [SourceRef(**s) for s in r.sources]
    return AgentMessage(
        agent=NAME, status="success", query_type="KNOWLEDGE", answer_kind="ENTERPRISE_GROUNDED_RESPONSE",
        summary=f"{len(sources)} enterprise document(s) support this answer.",
        findings=[Finding(text=r.answer, basis="KNOWN_FROM_SOURCES", source_ids=[s.id for s in sources])],
        sources=sources, grounded=True, grounding_score=r.grounding_score,
        conflict_detected=r.conflict_detected, tokens=r.tokens,
    )
