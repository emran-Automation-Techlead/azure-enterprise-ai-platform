"""General Agent: answers genuinely general technology questions, clearly labelled as NOT from enterprise documents.

Input : the (already redacted) question
Output: AgentMessage with answer_kind GENERAL_AI_RESPONSE, no sources, grounded=False always
Tools : one Azure OpenAI call, no search
Failure: outage -> status "error"
Bounds: must not make claims about the company's own systems, policies or incidents
"""
import logging

from app import llm
from app.agents.messages import AgentMessage, Finding

NAME = "general_agent"
log = logging.getLogger(NAME)

PREFIX = "General knowledge (not from the enterprise knowledge base):"
SYSTEM_PROMPT = (
    "You are an IT assistant. Answer the general technology question briefly (under 120 words). "
    f"Begin with: '{PREFIX}'. Do not claim anything about the company's own systems, policies, incidents or documents. "
    "If the question needs company-specific facts, say you cannot answer that from general knowledge."
)


def run(question: str) -> AgentMessage:
    try:
        r = llm.chat([{"role": "system", "content": SYSTEM_PROMPT}, {"role": "user", "content": question}])
    except llm.LLMError as exc:
        log.warning("general agent failed: %s", type(exc).__name__)
        return AgentMessage(
            agent=NAME, status="error", query_type="GENERAL", answer_kind="GENERAL_AI_RESPONSE",
            summary="The general answer was unavailable.",
            findings=[Finding(text="The model could not be reached.", basis="UNKNOWN")],
        )
    text = r["text"].strip()
    if not text.startswith(PREFIX):  # the label is enforced in code, not left to the model
        text = f"{PREFIX} {text}"
    return AgentMessage(
        agent=NAME, status="success", query_type="GENERAL", answer_kind="GENERAL_AI_RESPONSE",
        summary="General knowledge answer. No enterprise sources used.",
        findings=[Finding(text=text, basis="INFERENCE")],  # model knowledge is never "known from sources"
        grounded=False, tokens=r["tokens"],
    )
